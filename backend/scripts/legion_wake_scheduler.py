#!/usr/bin/env python3
"""legion_wake_scheduler.py — 军团全员唤醒调度器

让 149 名非核心员工（+9 核心常驻）全部「活起来」：按批次轮流激活，
每批 5 人运行 sync_knowledge 学习最新军团共享知识，固化到各自
memory.db，并更新「谁在场」registry。

架构（双层模型）:
    ┌─ 核心 9 员工: systemd 常驻（ai-digital-card-agents.service）
    └─ 全员 149 员工: 本调度器按批轮询激活
        每 10 分钟一批 → 5 人/批 → 30 批循环 → 约 5 小时全员轮一圈
        每人: LegionEmployee 加载 → sync_knowledge → 更新 presence

用法:
    python3 legion_wake_scheduler.py --once      # 只跑一批（测试/cron）
    python3 legion_wake_scheduler.py             # 常驻循环（systemd）
    python3 legion_wake_scheduler.py --batch 10  # 每批 10 人
    python3 legion_wake_scheduler.py --interval 600  # 每批间隔秒数
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("legion_wake_scheduler")

# baize_libs 注入（复制 main.py 顶部逻辑）
sys.path.insert(0, "/var/www/ai-digital-card/backend")
_BL_ROOT = "/var/www/baize_libs"
if _BL_ROOT and _BL_ROOT not in sys.path:
    sys.path.insert(0, _BL_ROOT)
try:
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location(
        "baize_libs", os.path.join(_BL_ROOT, "__init__.py"),
        submodule_search_locations=[_BL_ROOT],
    )
    if _spec and "baize_libs" not in sys.modules:
        _mod = _ilu.module_from_spec(_spec)
        sys.modules["baize_libs"] = _mod
        _spec.loader.exec_module(_mod)
except Exception:
    pass

LEGION_PATH = Path("/app/gaia-commercial/apps/services/ai_legion/employees")
BATCH_SIZE_DEFAULT = 5
INTERVAL_DEFAULT = 600  # 10 分钟

# ── 部门知识通道（P0-1 差异化学习）────────────────────────────
# 按员工部门定向投喂不同知识领域，让全员学到的内容有区分度
# 每条通道: SQL 过滤条件 + 展示标签
DEPT_CHANNELS: dict[str, dict] = {
    "research": {
        "label": "研究洞察",
        "sql": """AND (
              source IN ('distill_auto', 'retrospective', 'distill_enterprise')
              OR tags::text LIKE '%research%'
            )""",
    },
    "compliance": {
        "label": "安全合规",
        "sql": """AND (
              title LIKE '%安全%' OR title LIKE '%合规%' OR title LIKE '%Guardrail%'
              OR title LIKE '%OWASP%' OR title LIKE '%风控%'
            )""",
    },
    "acquisition": {
        "label": "销售获客",
        "sql": """AND (
              title LIKE '%销售%' OR title LIKE '%获客%' OR title LIKE '%名片%'
              OR title LIKE '%营销%' OR title LIKE '%F-CARD%'
            )""",
    },
    "ai_assistant": {
        "label": "技能工具",
        "sql": """AND (
              title LIKE '%技能%' OR title LIKE '%工具%' OR title LIKE '%SAG%'
              OR title LIKE '%蒸馏%'
            )""",
    },
    "general": {
        "label": "通用知识",
        "sql": """AND (
              source IN ('distill_enterprise', 'retrospective', 'manual')
              OR tags::text LIKE '%general%'
            )""",
    },
}
# 默认通道（未识别部门 → 通用）
DEFAULT_CHANNEL = "general"
# 全通道共享开关（可关闭 → 仅按部门）
ENABLE_CROSS_CHANNEL = True


def load_env() -> None:
    """从 backend/.env 加载环境变量（与 systemd EnvironmentFile 一致）。"""
    env_path = Path("/var/www/ai-digital-card/backend/.env")
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            v = v.strip().strip('"').strip("'")
            if k in ("DATABASE_URL", "JWT_SECRET", "DEEPSEEK_API_KEY", "DEEPSEEK_API_URL", "LEGION_PATH"):
                os.environ.setdefault(k, v)
    os.environ.setdefault("INFRA_PHASE", "1")


def get_members() -> list[dict]:
    """读取全员员工档案（非核心 149 人）。"""
    from app.services.legion_presence import LegionPresence, CORE_EMPLOYEES

    members = LegionPresence.get().get_all()
    # 排除核心常驻（他们由 systemd 服务管理）
    return [m for m in members if m.get("name") not in CORE_EMPLOYEES]


def get_next_batch(members: list[dict], batch_size: int, offset_file: Path) -> list[dict]:
    """取下一批（游标轮询，支持跨重启续跑）。"""
    offset = 0
    if offset_file.exists():
        try:
            offset = int(offset_file.read_text().strip())
        except Exception:
            offset = 0

    if not members:
        return []

    batch = members[offset: offset + batch_size]
    # 游标越界 → 回到起点（循环覆盖全员）
    if not batch:
        offset = 0
        batch = members[0: batch_size]

    new_offset = (offset + len(batch)) % len(members)
    offset_file.write_text(str(new_offset))
    return batch


async def wake_one(member: dict) -> dict:
    """激活单个员工：加载灵魂 → 按部门通道学习 → 分享经验 → 更新在场状态。"""
    from app.agents.legion_employee import LegionEmployee
    from app.services.legion_presence import LegionPresence

    emp_id = member["emp_id"]
    name = member["name"]
    dept = member.get("department") or DEFAULT_CHANNEL
    soul_dir = member.get("soul_dir") or ""
    presence = LegionPresence.get()

    try:
        presence.mark_waking(emp_id)

        # 加载员工（soul + memory.db）
        employee = LegionEmployee(employee_id=emp_id, brain=None)
        if not employee.emp_dir:
            logger.warning("  ✗ %s 灵魂目录不可用", emp_id)
            presence.mark_idle(emp_id)
            return {"emp_id": emp_id, "ok": False, "reason": "no_soul_dir"}

        # ── P0-1 差异化学习：按部门通道定向投喂 ──────────────
        new_count = 0
        learned_title = ""
        channel = DEPT_CHANNELS.get(dept, DEPT_CHANNELS[DEFAULT_CHANNEL])
        channel_label = channel["label"]

        # 该员工已学过的标题（防止重复学习，从 presence 记录）
        learned_before = presence.get_learned_titles(emp_id)

        try:
            from app.database import AsyncSessionLocal
            from sqlalchemy import text as _text

            # 部门通道 SQL + 排除 system 噪音 + 排除已学
            channel_sql = channel["sql"]
            exclude_sql = ""
            if learned_before:
                titles = "', '".join(t.replace("'", "''") for t in learned_before[:50])
                exclude_sql = f"AND title NOT IN ('{titles}')"

            async with AsyncSessionLocal() as db:
                rows = await db.execute(
                    _text(f"""
                        SELECT title, content FROM gaia_knowledge
                        WHERE is_active = true
                          AND source != 'system'
                          {channel_sql}
                          {exclude_sql}
                        ORDER BY created_at DESC, id DESC
                        LIMIT 10
                    """)
                )
                items = [{"title": r.title or "", "content": (r.content or "")[:400]} for r in rows]

            # 若部门通道知识不足，补充全通道共享知识（保证人人有得学）
            if not items and ENABLE_CROSS_CHANNEL:
                async with AsyncSessionLocal() as db:
                    rows = await db.execute(
                        _text("""
                            SELECT title, content FROM gaia_knowledge
                            WHERE is_active = true AND source != 'system'
                            ORDER BY created_at DESC, id DESC
                            LIMIT 5
                        """)
                    )
                    items = [{"title": r.title or "", "content": (r.content or "")[:400]} for r in rows]

            for it in items:
                title = it.get("title", "")
                existing = await employee.remember(title, limit=2) if title else []
                if existing:
                    continue
                await employee.memorize(
                    content=f"[共享学习-{channel_label}] {title}\n{it.get('content', '')}",
                    category="shared_learning",
                )
                new_count += 1
                learned_title = title
                if new_count >= 3:
                    break
        except Exception as exc:  # noqa: BLE001
            logger.debug("wake sync failed for %s: %s", emp_id, repr(exc))

        # ── P0-2 批次互教互学：员工把「最新学到」分享进知识库 ──
        shared = False
        if learned_title:
            try:
                from app.database import AsyncSessionLocal
                from sqlalchemy import text as _text

                async with AsyncSessionLocal() as db:
                    await db.execute(
                        _text("""
                            INSERT INTO gaia_knowledge
                            (source, source_id, knowledge_type, title, content, tags,
                             confidence, impact_score, vector_embedded, is_active)
                            VALUES
                            (:src, :sid, 'agent_share', :title, :content, :tags,
                             0.8, 0.6, false, true)
                        """),
                        {
                            "src": f"agent_share_{emp_id}",
                            "sid": f"{emp_id}_{int(time.time())}",
                            "title": f"{name} 分享: {learned_title}",
                            "content": f"（{channel_label}通道学习分享）{name} 学到的 {learned_title} 已回灌知识库，供全员学习。",
                            "tags": json.dumps(["agent_share", dept, channel_label], ensure_ascii=False),
                        },
                    )
                    await db.commit()
                presence.record_share(emp_id)
                shared = True
                logger.info("  🔄 %s(%s) 分享 1 条 → 知识库", name, emp_id)
            except Exception as exc:  # noqa: BLE001
                logger.warning("  ⚠️ %s 分享失败: %s", emp_id, repr(exc))

        # 更新在场状态 + 成长统计
        if new_count:
            presence.record_sync(emp_id, learned_title)
            presence.mark_idle(emp_id)
            logger.info(
                "  📖 %s(%s)[%s] 学习 %d 条 → %s",
                name, emp_id, channel_label, new_count, learned_title[:40],
            )
        else:
            # 没有新知识也记一次「在场」（sync_count 仍+1 表示活跃）
            presence.record_sync(emp_id, "")
            presence.mark_idle(emp_id)
            logger.info("  💤 %s(%s)[%s] 在场（无新知识）", name, emp_id, channel_label)

        return {
            "emp_id": emp_id, "ok": True, "learned": new_count,
            "title": learned_title, "shared": shared, "channel": channel_label,
        }

    except Exception as exc:  # noqa: BLE001
        logger.error("  ✗ %s 唤醒失败: %s", emp_id, repr(exc))
        try:
            presence.mark_idle(emp_id)
        except Exception:
            pass
        return {"emp_id": emp_id, "ok": False, "reason": repr(exc)}


async def run_batch(batch_size: int, offset_file: Path) -> dict:
    """跑一批员工。"""
    members = get_members()
    if not members:
        logger.warning("无全员成员（presence 未初始化）")
        # 尝试初始化
        from app.services.legion_presence import LegionPresence
        LegionPresence.get().init_from_roster()
        members = get_members()

    batch = get_next_batch(members, batch_size, offset_file)
    if not batch:
        return {"batch": [], "ok": 0, "fail": 0}

    logger.info("=== 唤醒批次: %d 人 (offset→%s) ===", len(batch), offset_file.read_text())

    results = []
    for m in batch:
        r = await wake_one(m)
        results.append(r)

    ok = sum(1 for r in results if r.get("ok"))
    fail = len(results) - ok
    logger.info("=== 批次完成: %d ok / %d fail ===", ok, fail)

    # 批次后打印军团在场概览
    from app.services.legion_presence import LegionPresence
    stats = LegionPresence.get().get_stats()
    logger.info(
        "🏛️ 军团在场: %d/%d active | 累计学习 %d 次 | 分享 %d 次",
        stats["active"] + stats["waking"],
        stats["total"],
        stats["total_learned"],
        stats["total_shares"],
    )
    return {"batch": batch, "ok": ok, "fail": fail}


async def main_loop(interval: int, batch_size: int, offset_file: Path) -> None:
    """常驻循环。"""
    logger.info("🧠 军团全员唤醒调度器启动 (interval=%ds batch=%d)", interval, batch_size)
    while True:
        try:
            await run_batch(batch_size, offset_file)
        except Exception as exc:  # noqa: BLE001
            logger.error("批次执行异常: %s", repr(exc))
        await asyncio.sleep(interval)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true", help="只跑一批（cron 模式）")
    ap.add_argument("--batch", type=int, default=BATCH_SIZE_DEFAULT, help="每批人数")
    ap.add_argument("--interval", type=int, default=INTERVAL_DEFAULT, help="批间间隔秒")
    args = ap.parse_args()

    load_env()

    offset_file = Path("/var/www/ai-digital-card/backend/data/legion_wake_offset.txt")
    offset_file.parent.mkdir(parents=True, exist_ok=True)

    # 确保 presence 已初始化
    from app.services.legion_presence import LegionPresence
    presence = LegionPresence.get()
    total = presence.get_stats().get("total", 0)
    if total == 0:
        added = presence.init_from_roster()
        logger.info("presence 初始化: %d 员工入库", added)

    if args.once:
        asyncio.run(run_batch(args.batch, offset_file))
        return 0

    asyncio.run(main_loop(args.interval, args.batch, offset_file))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
