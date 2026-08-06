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
    """激活单个员工：加载灵魂 → sync 学习 → 更新在场状态。"""
    from app.agents.legion_employee import LegionEmployee
    from app.services.legion_presence import LegionPresence

    emp_id = member["emp_id"]
    name = member["name"]
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

        # 从共享知识库直查最新共享知识（同步学习）
        new_count = 0
        learned_title = ""
        try:
            from app.database import AsyncSessionLocal
            from sqlalchemy import text as _text

            async with AsyncSessionLocal() as db:
                rows = await db.execute(
                    _text("""
                        SELECT title, content FROM gaia_knowledge
                        WHERE (source LIKE 'agent_share%' OR tags::text LIKE '%shared%')
                          AND is_active = true
                        ORDER BY created_at DESC, id DESC
                        LIMIT 5
                    """)
                )
                items = [{"title": r.title or "", "content": (r.content or "")[:300]} for r in rows]

            for it in items:
                title = it.get("title", "")
                existing = await employee.remember(title, limit=2) if title else []
                if existing:
                    continue
                await employee.memorize(
                    content=f"[共享学习] {title}\n{it.get('content', '')}",
                    category="shared_learning",
                )
                new_count += 1
                learned_title = title
                if new_count >= 3:
                    break
        except Exception as exc:  # noqa: BLE001
            logger.debug("wake sync failed for %s: %s", emp_id, repr(exc))

        # 更新在场状态 + 成长统计
        if new_count:
            presence.record_sync(emp_id, learned_title)
            presence.mark_idle(emp_id)
            logger.info("  📖 %s(%s) 学习 %d 条 → %s", name, emp_id, new_count, learned_title[:40])
        else:
            # 没有新知识也记一次「在场」（sync_count 仍+1 表示活跃）
            presence.record_sync(emp_id, "")
            presence.mark_idle(emp_id)
            logger.info("  💤 %s(%s) 在场（无新知识）", name, emp_id)

        return {"emp_id": emp_id, "ok": True, "learned": new_count, "title": learned_title}

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
