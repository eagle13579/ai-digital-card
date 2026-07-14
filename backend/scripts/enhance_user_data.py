"""用户数据增强脚本 — 自动计算全量用户间V2匹配度并写入match_records表

功能:
  1. 从 digital_brochure.db 读取所有用户
  2. 自动计算每对用户之间的 V2 匹配度（使用 matching_engine_v2 的五层算法）
  3. 将 V2 评分 ≥ 0.5 的对作为"正样本"写入 match_records 表
  4. 评分 0.3-0.5 的作为"弱正样本"
  5. 评分 < 0.2 的作为"负样本"
  6. 输出统计：新生成匹配对数、平均评分、各等级分布

使用方式:
    cd backend
    python scripts/enhance_user_data.py

输出:
    - 直接写入 match_records 表（不会重复写入已存在的对）
    - 终端打印统计摘要
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# 确保 backend 目录在 sys.path 中
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("enhance_user_data")

# ── 评分阈值 ──────────────────────────────────────────────────────────────
POSITIVE_THRESHOLD = 0.50   # 正样本
WEAK_THRESHOLD = 0.30       # 弱正样本下界
NEGATIVE_THRESHOLD = 0.20   # 负样本上界


async def enhance_user_data():
    """主流程：读取用户 → 计算V2匹配 → 写入数据库"""
    # ── 1. 导入应用模块（延迟导入，避免 import 时触发 app.__init__ 全量加载） ──
    from sqlalchemy import select, and_, or_
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.database import AsyncSessionLocal
    from app.models.tag import MatchRecord, UserTag
    from app.models.user import User
    from app.services.matching_engine import MatchEngine

    async with AsyncSessionLocal() as db:
        # ── 2. 读取所有用户 ────────────────────────────────────────────────────
        result = await db.execute(select(User).order_by(User.id))
        users = result.scalars().all()
        logger.info("读取到 %d 个用户", len(users))

        if len(users) < 2:
            logger.warning("用户数不足2个，无需计算匹配对")
            return

        # ── 3. 读取已有的匹配记录（避免重复写入） ─────────────────────────────
        result = await db.execute(select(MatchRecord))
        existing_records = result.scalars().all()
        existing_pairs: set[tuple[int, int]] = set()
        for rec in existing_records:
            a, b = rec.user_a_id, rec.user_b_id
            existing_pairs.add((a, b))
            existing_pairs.add((b, a))  # 双向去重

        logger.info(
            "已有 %d 对匹配记录（%d 对唯一用户对）",
            len(existing_records),
            len(existing_pairs),
        )

        # ── 4. 预加载所有用户的标签 ───────────────────────────────────────────
        result = await db.execute(
            select(UserTag).order_by(UserTag.user_id, UserTag.tag_type)
        )
        all_tags = result.scalars().all()

        # 按用户 ID 分组：{user_id: {"provide": {tag: weight}, "need": {tag: weight}}}
        user_tags_map: dict[int, dict[str, dict[str, float]]] = {}
        for tag in all_tags:
            if tag.user_id not in user_tags_map:
                user_tags_map[tag.user_id] = {"provide": {}, "need": {}}
            user_tags_map[tag.user_id].setdefault(tag.tag_type, {})[tag.tag] = tag.weight

        # ── 5. 计算全量用户对的 V2 匹配度 ────────────────────────────────────
        new_match_records: list[MatchRecord] = []
        stats = {
            "positive": 0,      # ≥ 0.5
            "weak_positive": 0,  # 0.3-0.5
            "negative": 0,      # < 0.2
            "neutral": 0,       # 0.2-0.3
            "skipped_existing": 0,
            "total_pairs": 0,
            "score_sum": 0.0,
        }

        total_pairs = len(users) * (len(users) - 1) // 2
        processed = 0

        for i in range(len(users)):
            user_a = users[i]
            for j in range(i + 1, len(users)):
                user_b = users[j]
                processed += 1

                # 跳过已有匹配记录的对
                if (user_a.id, user_b.id) in existing_pairs:
                    stats["skipped_existing"] += 1
                    continue

                # 跳过缺少标签的用户（任一方无标签则无法计算有效匹配）
                tags_a = user_tags_map.get(user_a.id, {"provide": {}, "need": {}})
                tags_b = user_tags_map.get(user_b.id, {"provide": {}, "need": {}})
                if not tags_a["provide"] and not tags_a["need"]:
                    continue
                if not tags_b["provide"] and not tags_b["need"]:
                    continue

                # 计算 V2 五层匹配度
                try:
                    v2_result = await MatchEngine.compute_similarity(
                        db, user_a.id, user_b.id
                    )
                except Exception as exc:
                    logger.warning(
                        "计算匹配度失败: user_a=%d, user_b=%d, error=%s",
                        user_a.id, user_b.id, exc,
                    )
                    continue

                score = v2_result["score"]
                stats["total_pairs"] += 1
                stats["score_sum"] += score

                # 确定样本类型
                if score >= POSITIVE_THRESHOLD:
                    status_label = "positive"
                    stats["positive"] += 1
                elif score >= WEAK_THRESHOLD:
                    status_label = "weak_positive"
                    stats["weak_positive"] += 1
                elif score < NEGATIVE_THRESHOLD:
                    status_label = "negative"
                    stats["negative"] += 1
                else:
                    status_label = "neutral"
                    stats["neutral"] += 1

                # 构建匹配记录
                common_tags_json = json.dumps(v2_result.get("common_tags", []), ensure_ascii=False)
                record = MatchRecord(
                    user_a_id=user_a.id,
                    user_b_id=user_b.id,
                    match_score=score,
                    status=status_label,
                    common_tags=common_tags_json,
                    source="v2_auto_enhance",
                )
                new_match_records.append(record)

                # 进度日志（每 50 对打印一次）
                if processed % 50 == 0 or processed == total_pairs:
                    logger.info(
                        "进度: %d/%d (%.1f%%)  新匹配对: %d",
                        processed, total_pairs,
                        processed / total_pairs * 100,
                        len(new_match_records),
                    )

        # ── 6. 批量写入数据库 ────────────────────────────────────────────────
        if new_match_records:
            db.add_all(new_match_records)
            await db.commit()
            logger.info("已写入 %d 条新匹配记录到 match_records 表", len(new_match_records))
        else:
            logger.info("没有新匹配记录需要写入")

        # ── 7. 输出统计 ──────────────────────────────────────────────────────
        avg_score = stats["score_sum"] / max(1, stats["total_pairs"])

        print("\n" + "=" * 60)
        print(f"{'📊 用户数据增强完成':^60}")
        print("=" * 60)
        print(f"  用户总数:              {len(users)}")
        print(f"  全量用户对（全部组合）:  {total_pairs}")
        print(f"  已存在匹配对（跳过）:    {stats['skipped_existing']}")
        print(f"  新生成匹配对:           {len(new_match_records)}")
        print(f"  平均评分:               {avg_score:.4f}")
        print("-" * 60)
        print(f"  样本分布:")
        print(f"    🟢 正样本  (≥{POSITIVE_THRESHOLD}):     {stats['positive']}")
        print(f"    🟡 弱正样本 (≥{WEAK_THRESHOLD}):     {stats['weak_positive']}")
        print(f"    ⚪ 中性     (≥{NEGATIVE_THRESHOLD}):     {stats['neutral']}")
        print(f"    🔴 负样本   (<{NEGATIVE_THRESHOLD}):     {stats['negative']}")
        print("=" * 60)


def main():
    asyncio.run(enhance_user_data())


if __name__ == "__main__":
    main()
