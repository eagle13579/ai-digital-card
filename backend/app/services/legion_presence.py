"""Legion Presence — 军团「谁在场」状态登记与成长统计

记录全员（158 员工）的活动状态与学习成长，支撑:
    1. 总览页「谁在场」看板（status / last_active_at / dept）
    2. 全员唤醒调度器的状态追踪（批次、循环、跳过）
    3. 成长统计（sync_count / share_count / last_learned_title）

存储: SQLite（服务器持久化，无需额外服务）
    /var/www/ai-digital-card/backend/data/legion_presence.db

表结构:
    legion_members(
        emp_id TEXT PRIMARY KEY,      -- emp-烛龙 / emp-贤宇-xxx
        name TEXT,                    -- 姓名
        department TEXT,              -- general / research / ...
        status TEXT,                  -- active(核心常驻) / waking(唤醒中) / idle(待唤醒) / unknown
        capabilities TEXT,            -- JSON 数组
        last_active_at REAL,          -- unix 时间戳
        sync_count INTEGER,           -- 累计同步次数
        share_count INTEGER,          -- 累计分享次数
        learned_count INTEGER,        -- 累计学习条目
        last_learned_title TEXT,      -- 最近一次学习标题
        soul_dir TEXT                 -- 灵魂目录路径
    )

用法:
    from app.services.legion_presence import LegionPresence
    p = LegionPresence()
    p.init_from_roster()          # 启动时同步 roster 全员
    p.mark_active("emp-烛龙")     # 核心常驻标记
    p.mark_waking("emp-贤宇-xxx") # 唤醒调度器标记
    p.record_sync("emp-贤宇-xxx", "最新共享知识标题")
    p.get_all()                   # 全员状态列表
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import time
from pathlib import Path

logger = logging.getLogger(__name__)

LEGION_PATH = Path("/app/gaia-commercial/apps/services/ai_legion/employees")
ROSTER = LEGION_PATH / "roster.json"
DEFAULT_DB = Path("/var/www/ai-digital-card/backend/data/legion_presence.db")

# 核心常驻员工（systemd 9 员工，状态 active）
CORE_EMPLOYEES = {
    "烛龙", "狴犴", "獬豸", "乘黄", "文鳐", "开明兽", "计然", "䑏疏", "白泽",
}


class LegionPresence:
    """全员在场状态登记（线程安全单例）。"""

    _instance: "LegionPresence | None" = None
    _lock = threading.Lock()

    def __init__(self, db_path: str | Path = DEFAULT_DB) -> None:
        self.db_path = str(db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_schema()

    # ── 单例 ─────────────────────────────────────────────────────

    @classmethod
    def get(cls) -> "LegionPresence":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # ── Schema ───────────────────────────────────────────────────

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS legion_members (
                    emp_id TEXT PRIMARY KEY,
                    name TEXT,
                    department TEXT,
                    status TEXT DEFAULT 'unknown',
                    capabilities TEXT DEFAULT '[]',
                    last_active_at REAL,
                    sync_count INTEGER DEFAULT 0,
                    share_count INTEGER DEFAULT 0,
                    learned_count INTEGER DEFAULT 0,
                    last_learned_title TEXT,
                    soul_dir TEXT
                )
            """)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    # ── 初始化 ───────────────────────────────────────────────────

    def init_from_roster(self, force: bool = False) -> int:
        """从 roster.json 同步全员（新增员工入库，不覆盖已有状态）。"""
        if not ROSTER.exists():
            logger.warning("roster 不存在: %s", ROSTER)
            return 0

        with open(ROSTER, encoding="utf-8") as f:
            roster = json.load(f)

        added = 0
        with self._connect() as conn:
            for dept_key, members in roster.items():
                if dept_key == "_meta" or not isinstance(members, list):
                    continue
                for m in members:
                    emp_id = m.get("emp_id", "")
                    name = m.get("name", "")
                    if not emp_id or not name:
                        continue
                    caps = json.dumps(m.get("capabilities", [])[:20], ensure_ascii=False)
                    soul_dir = self._find_soul_dir(emp_id, name)
                    status = "active" if name in CORE_EMPLOYEES else "idle"
                    conn.execute("""
                        INSERT OR IGNORE INTO legion_members
                        (emp_id, name, department, status, capabilities, soul_dir)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (emp_id, name, dept_key, status, caps, soul_dir))
                    added += 1
        logger.info("LegionPresence 初始化完成: roster %d 名员工入库", added)
        return added

    def _find_soul_dir(self, emp_id: str, name: str) -> str:
        """定位员工灵魂目录（emp_id 精确或 emp-{name} 前缀）。"""
        if not LEGION_PATH.is_dir():
            return ""
        # 1. emp_id 精确
        d = LEGION_PATH / emp_id
        if d.is_dir():
            return str(d)
        # 2. emp-{name} 前缀（可能有多个，取第一个）
        prefix = f"emp-{name}"
        for entry in os.listdir(LEGION_PATH):
            if entry.startswith(prefix) and (LEGION_PATH / entry).is_dir():
                return str(LEGION_PATH / entry)
        return ""

    # ── 状态标记 ─────────────────────────────────────────────────

    def mark_active(self, emp_id: str) -> None:
        """核心常驻员工在线标记。"""
        with self._connect() as conn:
            conn.execute(
                "UPDATE legion_members SET status='active', last_active_at=? WHERE emp_id=?",
                (time.time(), emp_id),
            )

    def mark_waking(self, emp_id: str) -> None:
        """唤醒调度器标记（员工正在激活学习）。"""
        with self._connect() as conn:
            conn.execute(
                "UPDATE legion_members SET status='waking', last_active_at=? WHERE emp_id=?",
                (time.time(), emp_id),
            )

    def mark_idle(self, emp_id: str) -> None:
        """激活完成后回到待唤醒。"""
        with self._connect() as conn:
            conn.execute(
                "UPDATE legion_members SET status='idle', last_active_at=? WHERE emp_id=?",
                (time.time(), emp_id),
            )

    def record_sync(self, emp_id: str, learned_title: str = "") -> None:
        """记录一次成功同步（学习）。"""
        with self._connect() as conn:
            conn.execute("""
                UPDATE legion_members
                SET sync_count = sync_count + 1,
                    learned_count = learned_count + 1,
                    last_learned_title = ?,
                    last_active_at = ?
                WHERE emp_id = ?
            """, (learned_title or None, time.time(), emp_id))

    def record_share(self, emp_id: str) -> None:
        """记录一次知识分享。"""
        with self._connect() as conn:
            conn.execute(
                "UPDATE legion_members SET share_count = share_count + 1 WHERE emp_id=?",
                (emp_id,),
            )

    def get_learned_titles(self, emp_id: str) -> list[str]:
        """查询员工最近学过的知识标题（用于差异化学习去重）。"""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT last_learned_title FROM legion_members WHERE emp_id=?",
                (emp_id,),
            ).fetchall()
        titles = [r["last_learned_title"] for r in rows if r["last_learned_title"]]
        # 返回最近 N 个（去重）
        seen: list[str] = []
        for t in titles:
            if t and t not in seen:
                seen.append(t)
        return seen[:50]

    # ── 查询 ─────────────────────────────────────────────────────

    def get_all(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM legion_members ORDER BY department, name"
            ).fetchall()
        return [dict(r) for r in rows]

    def get_by_dept(self, department: str) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM legion_members WHERE department=? ORDER BY name",
                (department,),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_stats(self) -> dict:
        """军团在场概览。"""
        with self._connect() as conn:
            total = conn.execute("SELECT count(*) FROM legion_members").fetchone()[0]
            active = conn.execute(
                "SELECT count(*) FROM legion_members WHERE status='active'"
            ).fetchone()[0]
            waking = conn.execute(
                "SELECT count(*) FROM legion_members WHERE status='waking'"
            ).fetchone()[0]
            idle = conn.execute(
                "SELECT count(*) FROM legion_members WHERE status='idle'"
            ).fetchone()[0]
            total_syncs = conn.execute(
                "SELECT COALESCE(sum(sync_count),0) FROM legion_members"
            ).fetchone()[0]
            total_shares = conn.execute(
                "SELECT COALESCE(sum(share_count),0) FROM legion_members"
            ).fetchone()[0]
            learned = conn.execute(
                "SELECT COALESCE(sum(learned_count),0) FROM legion_members"
            ).fetchone()[0]
        return {
            "total": total,
            "active": active,
            "waking": waking,
            "idle": idle,
            "unknown": max(0, total - active - waking - idle),
            "total_syncs": total_syncs,
            "total_shares": total_shares,
            "total_learned": learned,
            "updated_at": time.time(),
        }

    def top_learners(self, limit: int = 10) -> list[dict]:
        """学习成长 TOP 榜（谁在成长一目了然）。"""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM legion_members WHERE learned_count > 0 "
                "ORDER BY learned_count DESC, sync_count DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]
