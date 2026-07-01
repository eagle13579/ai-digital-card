"""
种子数据生成 — 在线学习冷启动
================================

生成100条模拟用户反馈记录 (60% like, 30% dislike, 10% skip)，
通过 FeedbackService 注入到 FeedbackLoop，然后触发在线学习。

用法:
    cd D:/AI数智名片/backend && python -m scripts.seed_feedback
"""

import logging
import random
import sys
import os

# ── 确保 backend 可导入 ──────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.feedback_service import get_feedback_service
from app.ai.online_learning import get_online_learning_engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# 种子数据参数
# ═══════════════════════════════════════════════════════════════

TOTAL_RECORDS = 100
LIKE_RATIO = 0.60     # 60% like
DISLIKE_RATIO = 0.30  # 30% dislike
SKIP_RATIO = 0.10     # 10% skip

# 模拟用户 / 内容 ID 范围
USER_IDS = [1, 2, 3, 5, 8, 13, 21, 34]
CONTENT_IDS = list(range(1, 51))


def seed_feedback():
    """注入种子反馈数据到 FeedbackLoop"""
    svc = get_feedback_service()

    # 构建反馈动作列表并打乱顺序
    n_like = int(TOTAL_RECORDS * LIKE_RATIO)
    n_dislike = int(TOTAL_RECORDS * DISLIKE_RATIO)
    n_skip = TOTAL_RECORDS - n_like - n_dislike

    actions = ["like"] * n_like + ["dislike"] * n_dislike + ["skip"] * n_skip
    random.shuffle(actions)

    logger.info("种子数据: 共 %d 条 (like=%d dislike=%d skip=%d)",
                len(actions), n_like, n_dislike, n_skip)
    logger.info("注入中...")

    for i, action in enumerate(actions, 1):
        user_id = random.choice(USER_IDS)
        content_id = random.choice(CONTENT_IDS)
        svc.record_feedback(
            user_id=user_id,
            content_id=content_id,
            action=action,
            source="seed",
        )
        if i % 20 == 0:
            logger.info("  进度: %d/%d", i, len(actions))

    # 打印最终统计
    stats = svc.get_global_stats()
    logger.info("注入完成!")
    logger.info("  总反馈:      %d", stats.get("total_feedback", 0))
    logger.info("  点赞(like):  %d", stats.get("positive_feedback", 0))
    logger.info("  踩(dislike): %d", stats.get("negative_feedback", 0))
    logger.info("  唯一用户数:  %d", stats.get("unique_users", 0))
    return stats


def trigger_learning():
    """触发在线学习引擎"""
    logger.info("触发在线学习...")
    engine = get_online_learning_engine()
    result = engine.run_learning_cycle()

    changes = result.get("weight_changes", {})
    logger.info("学习完成!")
    logger.info("  周期:         %s", result.get("cycle"))
    logger.info("  耗时:         %.3fs", result.get("duration_seconds", 0))
    logger.info("  调整前系数:   %.4f", changes.get("old_global_adjustment"))
    logger.info("  调整后系数:   %.4f", changes.get("new_global_adjustment"))
    logger.info("  新权重:       %s", changes.get("new_weights"))

    # 查看引擎状态
    status = engine.get_learning_status()
    logger.info("引擎状态:      %s", status.get("status"))
    logger.info("学习周期数:    %d", status.get("learning", {}).get("total_cycles", 0))
    return result


def main():
    logger.info("=" * 50)
    logger.info("  在线学习冷启动 — 种子数据生成")
    logger.info("=" * 50)
    print()

    seed_feedback()
    print()
    trigger_learning()

    print()
    logger.info("✅ 冷启动完成！在线学习引擎已就绪。")
    logger.info("可通过 GET /api/ai/learning/status 查看状态")


if __name__ == "__main__":
    main()
