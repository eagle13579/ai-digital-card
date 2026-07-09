"""Collaboration Service — 实时协作：名片+CRM多人编辑/评论系统

提供协作文档会话管理与评论系统，基于 SQLite 独立持久化。
"""
import json
import logging
import os
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


# ======================================================================
# Data Models
# ======================================================================


@dataclass
class Comment:
    """单个评论数据类。"""
    id: int
    session_id: str
    user_id: str
    user_name: str
    content: str
    created_at: str
    resolved: bool = False


@dataclass
class CollaborationSession:
    """协作会话数据类。"""
    session_id: str
    document_type: str  # 'brochure' | 'crm'
    document_id: str
    participants: list = field(default_factory=list)
    created_at: str = ""


# ======================================================================
# Service
# ======================================================================


class CollaborationService:
    """协作服务 — 管理会话生命周期与评论。

    存储：独立的 SQLite 文件 (data/collaboration.db)
    并发：WAL 模式 + 行级锁
    """

    def __init__(self, db_path: str | None = None):
        if db_path is None:
            # Default: data/collaboration.db 与主数据库同级
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "collaboration.db")
        self.db_path = db_path
        self._init_db()
        logger.info("CollaborationService 初始化完成: db=%s", self.db_path)

    # ------------------------------------------------------------------
    # 内部工具
    # ------------------------------------------------------------------

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self) -> None:
        conn = self._get_conn()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS collaboration_sessions (
                    session_id   TEXT PRIMARY KEY,
                    document_type TEXT NOT NULL,
                    document_id  TEXT NOT NULL,
                    participants TEXT NOT NULL DEFAULT '[]',
                    created_at   TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS comments (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    user_id    TEXT NOT NULL,
                    user_name  TEXT NOT NULL DEFAULT '',
                    content    TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    resolved   INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY (session_id) REFERENCES collaboration_sessions(session_id)
                );
                CREATE INDEX IF NOT EXISTS idx_comments_session
                    ON comments(session_id);
                CREATE INDEX IF NOT EXISTS idx_sessions_doc
                    ON collaboration_sessions(document_type, document_id);
            """)
            conn.commit()
        finally:
            conn.close()

    def _build_session(self, row: sqlite3.Row) -> CollaborationSession:
        return CollaborationSession(
            session_id=row["session_id"],
            document_type=row["document_type"],
            document_id=row["document_id"],
            participants=json.loads(row["participants"]),
            created_at=row["created_at"],
        )

    def _build_comment(self, row: sqlite3.Row) -> Comment:
        return Comment(
            id=row["id"],
            session_id=row["session_id"],
            user_id=row["user_id"],
            user_name=row["user_name"],
            content=row["content"],
            created_at=row["created_at"],
            resolved=bool(row["resolved"]),
        )

    # ------------------------------------------------------------------
    # 会话管理
    # ------------------------------------------------------------------

    def create_session(
        self,
        session_id: str,
        document_type: str,
        document_id: str,
    ) -> CollaborationSession:
        """创建一个新的协作会话。如果 session_id 已存在则返回已有会话。"""
        now = datetime.now(timezone.utc).isoformat()
        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT INTO collaboration_sessions (session_id, document_type, document_id, participants, created_at) "
                "VALUES (?, ?, ?, '[]', ?)",
                (session_id, document_type, document_id, now),
            )
            conn.commit()
            return CollaborationSession(
                session_id=session_id,
                document_type=document_type,
                document_id=document_id,
                participants=[],
                created_at=now,
            )
        except sqlite3.IntegrityError:
            return self.get_session(session_id)
        finally:
            conn.close()

    def get_session(self, session_id: str) -> Optional[CollaborationSession]:
        """按 session_id 查询会话。"""
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM collaboration_sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            return self._build_session(row) if row else None
        finally:
            conn.close()

    def join_session(
        self,
        session_id: str,
        user_id: str,
        user_name: str,
    ) -> Optional[CollaborationSession]:
        """加入协作会话。返回更新后的会话，或 None（会话不存在）。"""
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM collaboration_sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            if not row:
                return None
            participants: list = json.loads(row["participants"])
            if not any(p.get("user_id") == user_id for p in participants):
                participants.append({"user_id": user_id, "user_name": user_name})
                conn.execute(
                    "UPDATE collaboration_sessions SET participants = ? WHERE session_id = ?",
                    (json.dumps(participants, ensure_ascii=False), session_id),
                )
                conn.commit()
            return CollaborationSession(
                session_id=row["session_id"],
                document_type=row["document_type"],
                document_id=row["document_id"],
                participants=participants,
                created_at=row["created_at"],
            )
        finally:
            conn.close()

    def leave_session(
        self,
        session_id: str,
        user_id: str,
    ) -> Optional[CollaborationSession]:
        """离开协作会话。返回更新后的会话，或 None（会话不存在）。"""
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM collaboration_sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            if not row:
                return None
            participants: list = json.loads(row["participants"])
            participants = [p for p in participants if p.get("user_id") != user_id]
            conn.execute(
                "UPDATE collaboration_sessions SET participants = ? WHERE session_id = ?",
                (json.dumps(participants, ensure_ascii=False), session_id),
            )
            conn.commit()
            return CollaborationSession(
                session_id=row["session_id"],
                document_type=row["document_type"],
                document_id=row["document_id"],
                participants=participants,
                created_at=row["created_at"],
            )
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # 评论管理
    # ------------------------------------------------------------------

    def add_comment(
        self,
        session_id: str,
        user_id: str,
        user_name: str,
        content: str,
    ) -> Comment:
        """在会话中添加一条评论。"""
        now = datetime.now(timezone.utc).isoformat()
        conn = self._get_conn()
        try:
            cur = conn.execute(
                "INSERT INTO comments (session_id, user_id, user_name, content, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (session_id, user_id, user_name, content, now),
            )
            conn.commit()
            return Comment(
                id=cur.lastrowid,
                session_id=session_id,
                user_id=user_id,
                user_name=user_name,
                content=content,
                created_at=now,
                resolved=False,
            )
        finally:
            conn.close()

    def get_comments(self, session_id: str) -> list[Comment]:
        """获取某会话的所有评论（按创建时间升序）。"""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM comments WHERE session_id = ? ORDER BY created_at ASC",
                (session_id,),
            ).fetchall()
            return [self._build_comment(r) for r in rows]
        finally:
            conn.close()

    def resolve_comment(self, comment_id: int) -> Optional[Comment]:
        """将评论标记为已解决。返回更新后的 Comment，或 None（不存在）。"""
        conn = self._get_conn()
        try:
            conn.execute("UPDATE comments SET resolved = 1 WHERE id = ?", (comment_id,))
            conn.commit()
            row = conn.execute(
                "SELECT * FROM comments WHERE id = ?", (comment_id,)
            ).fetchone()
            return self._build_comment(row) if row else None
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # 全局查询
    # ------------------------------------------------------------------

    def get_active_sessions(self) -> list[CollaborationSession]:
        """返回所有活跃会话（按创建时间降序）。"""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM collaboration_sessions ORDER BY created_at DESC"
            ).fetchall()
            return [self._build_session(r) for r in rows]
        finally:
            conn.close()


# ======================================================================
# 单例
# ======================================================================

_collaboration_service: Optional[CollaborationService] = None


def get_collaboration_service() -> CollaborationService:
    """获取全局单例的 CollaborationService。"""
    global _collaboration_service
    if _collaboration_service is None:
        _collaboration_service = CollaborationService()
    return _collaboration_service
