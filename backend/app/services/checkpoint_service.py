"""checkpoint_service.py — F16 Checkpoint 恢复引擎

每步骤持久化状态，失败时从最近 Checkpoint 恢复。
支持：
  - save / restore / status / update_step
  - 超时清理（cleanup_expired）
  - JSON 文件持久化（可替换为 Redis / DB）

依赖:
  - app.models.checkpoint: TaskCheckpoint, StepRecord, StepStatus, CheckpointStatus
  - F08 task_slicer: 可选，用于将切片计划转化为步骤名称列表
"""

from __future__ import annotations
import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any

from app.models.checkpoint import (
    CheckpointStatus,
    StepRecord,
    StepStatus,
    TaskCheckpoint,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# 默认持久化目录
# ──────────────────────────────────────────────

def _default_checkpoint_dir() -> str:
    """获取默认 Checkpoint 持久化目录"""
    base = os.environ.get("CHECKPOINT_DIR", "")
    if base:
        return base
    # 回退到项目 data/checkpoints/
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(os.path.dirname(app_dir), "data", "checkpoints")


CHECKPOINT_DIR = _default_checkpoint_dir()
# 默认 TTL：24 小时
DEFAULT_TTL_SECONDS = 86400
# 清理间隔（秒）
CLEANUP_INTERVAL = 300  # 5 分钟
# 锁（线程安全）
_checkpoint_lock = threading.Lock()


# ──────────────────────────────────────────────
# Checkpoint 恢复引擎
# ──────────────────────────────────────────────

class CheckpointService:
    """
    Checkpoint 恢复引擎 — 异步任务断点恢复核心。

    职责：
      - save_checkpoint:    持久化当前 Checkpoint 状态到磁盘
      - restore_checkpoint: 从磁盘恢复指定任务的 Checkpoint
      - get_status:         获取任务当前执行状态
      - update_step_status: 更新单步执行状态（自动持久化）
      - mark_failed:        标记任务完成/失败
      - cleanup_expired:    清理过期 Checkpoint 文件
      - create_from_task:   从任务元信息创建新 Checkpoint

    线程安全：内部使用 threading.Lock 保护文件读写。
    """

    def __init__(
        self,
        checkpoint_dir: str = "",
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ):
        self.checkpoint_dir: str = checkpoint_dir or CHECKPOINT_DIR
        self.ttl_seconds: int = ttl_seconds
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        self._lock = _checkpoint_lock
        logger.info(
            "CheckpointService 初始化: dir=%s ttl=%ds",
            self.checkpoint_dir, self.ttl_seconds,
        )

    # ── 文件路径 ──────────────────────────────

    def _file_path(self, task_id: str) -> str:
        return os.path.join(self.checkpoint_dir, f"{task_id}.json")

    # ── 持久化 / 恢复 ─────────────────────────

    def save_checkpoint(self, ckpt: TaskCheckpoint) -> TaskCheckpoint:
        """
        持久化 Checkpoint 状态到磁盘。
        每步骤执行完毕后调用，确保断点可恢复。
        """
        ckpt.updated_at = time.time()
        filepath = self._file_path(ckpt.task_id)
        with self._lock:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(ckpt.to_dict(), f, ensure_ascii=False, indent=2)
                logger.debug(
                    "Checkpoint 已持久化: task=%s steps=%d/%d",
                    ckpt.task_id, ckpt.completed_step_count, ckpt.step_count,
                )
            except OSError as exc:
                logger.error("Checkpoint 持久化失败 task=%s: %s", ckpt.task_id, exc)
                raise
        return ckpt

    def restore_checkpoint(self, task_id: str) -> TaskCheckpoint | None:
        """
        从磁盘恢复指定任务的 Checkpoint。
        返回 None 表示不存在或已过期。

        恢复逻辑：
          1. 读取文件
          2. 检查是否过期（expires_at）
          3. 确定恢复点（recovery_point）
          4. 将被恢复的步骤标记为 pending
        """
        filepath = self._file_path(task_id)
        if not os.path.exists(filepath):
            logger.warning("Checkpoint 文件不存在: task=%s path=%s", task_id, filepath)
            return None

        with self._lock:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (OSError, json.JSONDecodeError) as exc:
                logger.error("Checkpoint 读取失败 task=%s: %s", task_id, exc)
                return None

        ckpt = TaskCheckpoint.from_dict(data, ttl_seconds=self.ttl_seconds)

        # 过期检查
        now = time.time()
        if ckpt.is_expired(now):
            logger.warning("Checkpoint 已过期: task=%s expires_at=%s", task_id, ckpt.expires_at)
            self.delete_checkpoint(task_id)
            return None

        # 已完成的任务不再恢复
        if ckpt.status in (CheckpointStatus.COMPLETED, CheckpointStatus.FAILED):
            logger.info(
                "Checkpoint 终态无需恢复: task=%s status=%s", task_id, ckpt.status.value,
            )
            return ckpt

        # 确定恢复点
        recovery_point = ckpt.get_recovery_point()
        if recovery_point >= ckpt.step_count:
            logger.info("所有步骤已完成: task=%s", task_id)
            ckpt.status = CheckpointStatus.COMPLETED
            return ckpt

        # 重置恢复点之后的步骤为 PENDING
        for i in range(recovery_point, ckpt.step_count):
            step = ckpt.steps[i]
            if step.status != StepStatus.COMPLETED:
                step.status = StepStatus.PENDING
                step.error = None
                step.started_at = None
                step.completed_at = None

        # 重置任务状态为 RUNNING
        ckpt.status = CheckpointStatus.RUNNING
        ckpt.current_step_index = recovery_point
        ckpt.updated_at = now

        logger.info(
            "Checkpoint 恢复: task=%s recovery_point=%d total_steps=%d",
            task_id, recovery_point, ckpt.step_count,
        )

        # 重新持久化（保存重置后的状态）
        self.save_checkpoint(ckpt)
        return ckpt

    def get_status(self, task_id: str) -> dict[str, Any] | None:
        """获取任务 Checkpoint 状态快照"""
        ckpt = self.restore_checkpoint(task_id)
        if ckpt is None:
            return None
        return ckpt.to_snapshot()

    # ── 步骤管理 ──────────────────────────────

    def update_step_status(
        self,
        task_id: str,
        step_index: int,
        status: StepStatus,
        data: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> TaskCheckpoint | None:
        """
        更新单步状态并自动持久化。

        典型流程：
          1. 恢复 Checkpoint
          2. 更新某一步骤状态
          3. 自动保存

        返回更新后的 TaskCheckpoint，失败返回 None。
        """
        ckpt = self.restore_checkpoint(task_id)
        if ckpt is None:
            logger.error("更新步骤状态失败: 任务不存在 task=%s", task_id)
            return None

        try:
            ckpt.update_step_status(step_index, status, data=data, error=error)
        except IndexError as exc:
            logger.error("更新步骤状态失败: %s", exc)
            return None

        # 检查是否所有步骤完成
        if ckpt.completed_step_count == ckpt.step_count:
            ckpt.status = CheckpointStatus.COMPLETED
        elif status == StepStatus.FAILED:
            ckpt.status = CheckpointStatus.FAILED

        self.save_checkpoint(ckpt)
        return ckpt

    def mark_step_completed(
        self,
        task_id: str,
        step_index: int,
        step_data: dict[str, Any] | None = None,
    ) -> TaskCheckpoint | None:
        """标记步骤完成"""
        return self.update_step_status(task_id, step_index, StepStatus.COMPLETED, data=step_data)

    def mark_step_failed(
        self,
        task_id: str,
        step_index: int,
        error: str,
        step_data: dict[str, Any] | None = None,
    ) -> TaskCheckpoint | None:
        """标记步骤失败"""
        return self.update_step_status(task_id, step_index, StepStatus.FAILED, data=step_data, error=error)

    def mark_task_failed(
        self,
        task_id: str,
        error: str,
    ) -> TaskCheckpoint | None:
        """直接标记整个任务失败"""
        ckpt = self.restore_checkpoint(task_id)
        if ckpt is None:
            return None
        ckpt.status = CheckpointStatus.FAILED
        ckpt.error = error
        ckpt.updated_at = time.time()
        self.save_checkpoint(ckpt)
        return ckpt

    def mark_task_completed(self, task_id: str) -> TaskCheckpoint | None:
        """标记任务完成（所有剩余步骤跳过）"""
        ckpt = self.restore_checkpoint(task_id)
        if ckpt is None:
            return None
        ckpt.status = CheckpointStatus.COMPLETED
        for i in range(ckpt.current_step_index, ckpt.step_count):
            step = ckpt.steps[i]
            if step.status not in (StepStatus.COMPLETED, StepStatus.SKIPPED):
                step.status = StepStatus.SKIPPED
                step.completed_at = time.time()
        ckpt.updated_at = time.time()
        self.save_checkpoint(ckpt)
        return ckpt

    # ── 创建新 Checkpoint ─────────────────────

    def create_from_task(
        self,
        task_id: str,
        step_names: list[str],
        metadata: dict[str, Any] | None = None,
    ) -> TaskCheckpoint:
        """
        从步骤名称列表创建新 Checkpoint 并持久化。

        Args:
            task_id: 任务唯一 ID
            step_names: 步骤名称列表，如 ["load", "parse", "transform", "save"]
            metadata: 任务级元数据

        Returns:
            已持久化的 TaskCheckpoint
        """
        ckpt = TaskCheckpoint(
            task_id=task_id,
            metadata=metadata or {},
            ttl_seconds=self.ttl_seconds,
            status=CheckpointStatus.RUNNING,
        )
        for name in step_names:
            ckpt.add_step(StepRecord(step_name=name))
        self.save_checkpoint(ckpt)
        logger.info(
            "新 Checkpoint 已创建: task=%s steps=%d",
            task_id, len(step_names),
        )
        return ckpt

    def create_from_slicer_plan(
        self,
        task_id: str,
        slice_plan_id: str,
        slice_count: int,
        metadata: dict[str, Any] | None = None,
    ) -> TaskCheckpoint:
        """
        从 F08 TaskSlicer 切片计划创建 Checkpoint。
        每个切片对应一个步骤。

        Args:
            task_id: 任务 ID
            slice_plan_id: TaskSlicer 的 plan.task_id
            slice_count: 切片数量
            metadata: 附加元数据
        """
        step_names = [f"slice_{i}" for i in range(slice_count)]
        meta = {
            "slice_plan_id": slice_plan_id,
            "slice_count": slice_count,
            **(metadata or {}),
        }
        return self.create_from_task(task_id, step_names, metadata=meta)

    # ── 删除 / 清理 ───────────────────────────

    def delete_checkpoint(self, task_id: str) -> bool:
        """删除指定任务的 Checkpoint 文件"""
        filepath = self._file_path(task_id)
        with self._lock:
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    logger.info("Checkpoint 已删除: task=%s", task_id)
                    return True
                except OSError as exc:
                    logger.error("Checkpoint 删除失败 task=%s: %s", task_id, exc)
                    return False
        return False

    def cleanup_expired(self, max_age_seconds: int | None = None) -> int:
        """
        清理过期 Checkpoint 文件。

        Args:
            max_age_seconds: 覆盖实例默认 ttl_seconds，用于强制清理

        Returns:
            已删除的文件数量
        """
        max_age = max_age_seconds or self.ttl_seconds
        now = time.time()
        removed = 0

        with self._lock:
            if not os.path.isdir(self.checkpoint_dir):
                return 0
            for fname in os.listdir(self.checkpoint_dir):
                if not fname.endswith(".json"):
                    continue
                filepath = os.path.join(self.checkpoint_dir, fname)
                try:
                    # 根据文件修改时间判断
                    mtime = os.path.getmtime(filepath)
                    if now - mtime > max_age:
                        os.remove(filepath)
                        removed += 1
                        task_id = fname[:-5]
                        logger.debug("清理过期 Checkpoint: task=%s age=%.1fs", task_id, now - mtime)
                except OSError:
                    continue

        if removed:
            logger.info("过期 Checkpoint 清理完成: 删除 %d 个", removed)
        return removed

    def list_checkpoints(self, include_expired: bool = False) -> list[dict[str, Any]]:
        """
        列出所有 Checkpoint 摘要列表。
        """
        results: list[dict[str, Any]] = []
        if not os.path.isdir(self.checkpoint_dir):
            return results
        now = time.time()
        for fname in sorted(os.listdir(self.checkpoint_dir)):
            if not fname.endswith(".json"):
                continue
            filepath = os.path.join(self.checkpoint_dir, fname)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                ckpt = TaskCheckpoint.from_dict(data, ttl_seconds=self.ttl_seconds)
                expired = ckpt.is_expired(now)
                if not include_expired and expired:
                    continue
                snapshot = ckpt.to_snapshot()
                snapshot["expired"] = expired
                results.append(snapshot)
            except (OSError, json.JSONDecodeError):
                continue
        return results


# ──────────────────────────────────────────────
# 全局单例
# ──────────────────────────────────────────────

_checkpoint_service: CheckpointService | None = None


def get_checkpoint_service(
    checkpoint_dir: str = "",
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> CheckpointService:
    """获取全局 CheckpointService 单例"""
    global _checkpoint_service
    if _checkpoint_service is None:
        _checkpoint_service = CheckpointService(
            checkpoint_dir=checkpoint_dir,
            ttl_seconds=ttl_seconds,
        )
    return _checkpoint_service


# ── 便捷函数 ─────────────────────────────────

def save_checkpoint(ckpt: TaskCheckpoint) -> TaskCheckpoint:
    """便捷：持久化 Checkpoint"""
    return get_checkpoint_service().save_checkpoint(ckpt)


def restore_checkpoint(task_id: str) -> TaskCheckpoint | None:
    """便捷：恢复 Checkpoint"""
    return get_checkpoint_service().restore_checkpoint(task_id)


def get_status(task_id: str) -> dict[str, Any] | None:
    """便捷：查询状态"""
    return get_checkpoint_service().get_status(task_id)
