"""
checkpoint.py — 导入进度检查点管理器

支持中断恢复（resume）和进度追踪。
使用 JSONL 格式持久化，每条记录代表一个客户的状态变更。
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

logger = logging.getLogger(__name__)

# ── 状态常量 ──────────────────────────────────────────────────────────────


class ImportStatus:
    """导入状态枚举（字符串常量，方便序列化）"""
    PENDING = "pending"       # 等待导入
    IN_PROGRESS = "in_progress"  # 正在导入
    SUCCESS = "success"       # 导入成功
    SKIPPED = "skipped"       # 跳过（重复等）
    FAILED = "failed"         # 导入失败
    CANCELLED = "cancelled"   # 手动取消


# ── 数据模型 ──────────────────────────────────────────────────────────────


@dataclass
class ImportRecord:
    """单条客户导入记录"""
    index: int                       # 在源文件中的序号（0-based）
    raw_data: dict[str, str]         # 原始客户数据
    status: str = ImportStatus.PENDING
    message: str = ""                # 成功/失败信息
    timestamp: float = field(default_factory=time.time)
    retry_count: int = 0
    max_retries: int = 3

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ImportRecord":
        return cls(**data)


@dataclass
class Checkpoint:
    """检查点快照 — 保存整个导入会话的状态"""
    session_id: str                    # 唯一会话 ID（基于时间戳或文件路径）
    source_file: str                   # 源文件路径
    total_records: int                 # 总记录数
    records: list[ImportRecord] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def completed_count(self) -> int:
        return sum(1 for r in self.records if r.status in (ImportStatus.SUCCESS, ImportStatus.SKIPPED))

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.records if r.status == ImportStatus.FAILED)

    @property
    def progress(self) -> float:
        if self.total_records == 0:
            return 0.0
        return self.completed_count / self.total_records

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "source_file": self.source_file,
            "total_records": self.total_records,
            "records": [r.to_dict() for r in self.records],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_count": self.completed_count,
            "failed_count": self.failed_count,
            "progress": self.progress,
            "metadata": self.metadata,
        }


# ── 检查点管理器 ──────────────────────────────────────────────────────────


class CheckpointManager:
    """JSONL 持久化的检查点管理器

    用法:
        mgr = CheckpointManager("./checkpoints")
        cp = mgr.create_session("import_20260729", "customers.xlsx", 100)
        mgr.update_record(cp, 0, ImportStatus.SUCCESS, "导入成功")
        cp = mgr.load_session("import_20260729")  # 恢复
    """

    def __init__(self, checkpoint_dir: str | Path = "./checkpoints"):
        self._dir = Path(checkpoint_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    # ── 会话管理 ──────────────────────────────────────────────────────────

    def create_session(
        self,
        session_id: str,
        source_file: str,
        total_records: int,
        metadata: dict[str, Any] | None = None,
        initial_data: list[dict[str, str]] | None = None,
    ) -> Checkpoint:
        """创建新的导入会话

        Args:
            session_id: 唯一会话标识
            source_file: 源文件路径
            total_records: 总记录数
            metadata: 可选元数据（如目标系统名称、用户等）
            initial_data: 可选的初始客户数据列表

        Returns:
            初始化的 Checkpoint 对象
        """
        records = [
            ImportRecord(
                index=i,
                raw_data=initial_data[i] if initial_data and i < len(initial_data) else {},
            )
            for i in range(total_records)
        ]
        cp = Checkpoint(
            session_id=session_id,
            source_file=source_file,
            total_records=total_records,
            records=records,
            metadata=metadata or {},
        )
        self._write_jsonl(cp)  # 写初始快照
        return cp

    def load_session(self, session_id: str) -> Checkpoint | None:
        """加载已有会话（用于中断恢复）

        Args:
            session_id: 会话 ID

        Returns:
            Checkpoint 对象（如果存在），否则 None
        """
        jsonl_path = self._dir / f"{session_id}.jsonl"
        if not jsonl_path.exists():
            return None

        cp: Checkpoint | None = None
        for line in self._read_jsonl(jsonl_path):
            if cp is None:
                # 第一行是完整快照
                data = json.loads(line)
                records = [ImportRecord.from_dict(r) for r in data.pop("records", [])]
                # 移除计算字段
                data.pop("completed_count", None)
                data.pop("failed_count", None)
                data.pop("progress", None)
                cp = Checkpoint(**data, records=records)
            else:
                # 后续行是增量更新
                update = json.loads(line)
                self._apply_update(cp, update)

        return cp

    def list_sessions(self) -> list[dict[str, Any]]:
        """列出所有导入会话摘要"""
        sessions: list[dict[str, Any]] = []
        for f in sorted(self._dir.glob("*.jsonl"), reverse=True):
            try:
                with open(f, encoding="utf-8") as fh:
                    first_line = fh.readline()
                    if first_line:
                        data = json.loads(first_line)
                        sessions.append({
                            "session_id": data.get("session_id", f.stem),
                            "source_file": data.get("source_file", ""),
                            "total_records": data.get("total_records", 0),
                            "completed_count": data.get("completed_count", 0),
                            "failed_count": data.get("failed_count", 0),
                            "progress": data.get("progress", 0),
                            "updated_at": data.get("updated_at", 0),
                            "file": str(f),
                        })
            except (json.JSONDecodeError, OSError):
                continue
        return sessions

    # ── 记录更新 ──────────────────────────────────────────────────────────

    def update_record(
        self,
        cp: Checkpoint,
        index: int,
        status: str,
        message: str = "",
        raw_data: dict[str, str] | None = None,
    ) -> None:
        """更新单条记录的导入状态（追加到 JSONL）"""
        if index < 0 or index >= len(cp.records):
            raise IndexError(f"记录索引 {index} 超出范围 (0..{len(cp.records) - 1})")

        record = cp.records[index]
        record.status = status
        record.message = message
        record.timestamp = time.time()
        if status in (ImportStatus.FAILED,):
            record.retry_count += 1
        if raw_data:
            record.raw_data = raw_data

        cp.updated_at = time.time()

        # 追加增量更新到 JSONL
        update: dict[str, Any] = {
            "type": "record_update",
            "index": index,
            "status": status,
            "message": message,
            "timestamp": record.timestamp,
            "retry_count": record.retry_count,
        }
        if raw_data:
            update["raw_data"] = raw_data
        self._append_jsonl(cp, update)

    def update_metadata(self, cp: Checkpoint, **kwargs: Any) -> None:
        """更新会话元数据"""
        cp.metadata.update(kwargs)
        cp.updated_at = time.time()
        self._append_jsonl(cp, {"type": "metadata_update", "metadata": cp.metadata})

    def write_snapshot(self, cp: Checkpoint) -> None:
        """写入完整快照（用于阶段性持久化）"""
        self._write_jsonl(cp)

    def get_resume_index(self, cp: Checkpoint) -> int:
        """获取恢复导入的起始索引

        返回第一个状态为 PENDING 或 FAILED 且重试次数未超限的记录索引。
        如果全部完成，返回 total_records。
        """
        for i, record in enumerate(cp.records):
            if record.status == ImportStatus.PENDING:
                return i
            if record.status == ImportStatus.FAILED and record.retry_count < record.max_retries:
                return i
        return cp.total_records

    def summary(self, cp: Checkpoint) -> dict[str, Any]:
        """生成导入进度摘要"""
        return {
            "session_id": cp.session_id,
            "source_file": cp.source_file,
            "total": cp.total_records,
            "completed": cp.completed_count,
            "failed": cp.failed_count,
            "in_progress": sum(1 for r in cp.records if r.status == ImportStatus.IN_PROGRESS),
            "pending": sum(1 for r in cp.records if r.status == ImportStatus.PENDING),
            "progress_pct": round(cp.progress * 100, 1),
            "resume_index": self.get_resume_index(cp),
            "elapsed_seconds": round(time.time() - cp.created_at, 1),
        }

    # ── 内部 JSONL IO ────────────────────────────────────────────────────

    def _jsonl_path(self, session_id: str) -> Path:
        return self._dir / f"{session_id}.jsonl"

    def _write_jsonl(self, cp: Checkpoint) -> None:
        """写入完整快照（覆盖模式）"""
        path = self._jsonl_path(cp.session_id)
        with open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps(cp.to_dict(), ensure_ascii=False) + "\n")

    def _append_jsonl(self, cp: Checkpoint, update: dict[str, Any]) -> None:
        """追加增量更新到 JSONL"""
        path = self._jsonl_path(cp.session_id)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(update, ensure_ascii=False) + "\n")

    def _read_jsonl(self, path: Path) -> Iterator[str]:
        """逐行读取 JSONL 文件"""
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield line

    def _apply_update(self, cp: Checkpoint, update: dict[str, Any]) -> None:
        """将增量更新应用到 Checkpoint 对象"""
        update_type = update.get("type")
        if update_type == "record_update":
            idx = update["index"]
            if 0 <= idx < len(cp.records):
                cp.records[idx].status = update.get("status", cp.records[idx].status)
                cp.records[idx].message = update.get("message", cp.records[idx].message)
                cp.records[idx].timestamp = update.get("timestamp", cp.records[idx].timestamp)
                cp.records[idx].retry_count = update.get("retry_count", cp.records[idx].retry_count)
                if "raw_data" in update:
                    cp.records[idx].raw_data = update["raw_data"]
                cp.updated_at = update.get("timestamp", time.time())
        elif update_type == "metadata_update":
            cp.metadata.update(update.get("metadata", {}))
            cp.updated_at = update.get("timestamp", time.time())


# ── 便捷格式化 ────────────────────────────────────────────────────────────


def format_progress_bar(
    completed: int,
    total: int,
    width: int = 40,
    fill: str = "█",
    empty: str = "░",
) -> str:
    """生成进度条字符串"""
    if total == 0:
        ratio = 0.0
    else:
        ratio = completed / total
    filled = int(width * ratio)
    bar = fill * filled + empty * (width - filled)
    pct = round(ratio * 100, 1)
    return f"[{bar}] {pct}% ({completed}/{total})"
