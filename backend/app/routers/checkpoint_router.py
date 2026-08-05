"""checkpoint_router.py — F16 Checkpoint 恢复 API

API 端点:
  POST   /api/checkpoint/save        — 持久化/更新 Checkpoint
  GET    /api/checkpoint/restore/{task_id}  — 恢复 Checkpoint（含状态重置）
  GET    /api/checkpoint/status/{task_id}   — 查询 Checkpoint 状态
  DELETE /api/checkpoint/{task_id}   — 删除 Checkpoint
  POST   /api/checkpoint/step/update — 更新单步状态
  POST   /api/checkpoint/create      — 从步骤列表创建新 Checkpoint
  GET    /api/checkpoint/list        — 列出所有 Checkpoint
  POST   /api/checkpoint/cleanup     — 手动触发过期清理

依赖:
  - app.services.checkpoint_service: CheckpointEngine
  - app.models.checkpoint: TaskCheckpoint, StepRecord, StepStatus
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Any

from app.models.checkpoint import (
    CheckpointStatus,
    StepStatus,
    TaskCheckpoint,
    StepRecord,
)
from app.services.checkpoint_service import (
    CheckpointService,
    get_checkpoint_service,
    save_checkpoint,
    restore_checkpoint,
    get_status,
)

router = APIRouter(prefix="/api/checkpoint", tags=["F16 Checkpoint恢复"])

# 全局 Checkpoint 服务实例
_service: CheckpointService = get_checkpoint_service()


# ──────────────────────────────────────────────
# Pydantic 请求 / 响应模型
# ──────────────────────────────────────────────

class StepData(BaseModel):
    """单步数据"""
    step_name: str = Field(..., description="步骤名称")
    index: int = Field(default=0, description="步骤序号")
    status: str = Field(default="pending", description="步骤状态")
    data: dict[str, Any] = Field(default_factory=dict, description="步骤产出数据")
    error: str | None = Field(default=None, description="错误信息")


class SaveCheckpointRequest(BaseModel):
    """保存 Checkpoint 请求"""
    task_id: str = Field(..., description="任务 ID")
    steps: list[StepData] = Field(default_factory=list, description="步骤列表")
    status: str = Field(default="running", description="任务状态")
    metadata: dict[str, Any] = Field(default_factory=dict, description="任务元数据")
    ttl_seconds: int = Field(default=86400, description="TTL（秒）")


class CreateCheckpointRequest(BaseModel):
    """创建 Checkpoint 请求"""
    task_id: str = Field(..., description="任务 ID")
    step_names: list[str] = Field(..., description="步骤名称列表")
    metadata: dict[str, Any] = Field(default_factory=dict, description="任务元数据")


class UpdateStepRequest(BaseModel):
    """更新单步状态请求"""
    task_id: str = Field(..., description="任务 ID")
    step_index: int = Field(..., description="步骤序号")
    status: str = Field(..., description="新状态: pending | running | completed | failed | skipped | timeout")
    data: dict[str, Any] = Field(default_factory=dict, description="步骤数据")
    error: str | None = Field(default=None, description="错误信息")


class APIResponse(BaseModel):
    """统一响应格式"""
    code: int = Field(default=0, description="状态码（0=成功）")
    message: str = Field(default="success", description="消息")
    data: Any = Field(default=None, description="数据")


# ──────────────────────────────────────────────
# API 端点
# ──────────────────────────────────────────────

@router.post("/save", response_model=APIResponse)
async def api_save_checkpoint(req: SaveCheckpointRequest):
    """
    持久化 Checkpoint 状态。

    每步骤执行完毕后调用此接口，确保断点可恢复。
    如果 task_id 已存在，会覆盖现有数据。
    """
    try:
        ckpt = TaskCheckpoint(
            task_id=req.task_id,
            status=CheckpointStatus(req.status),
            metadata=req.metadata,
            ttl_seconds=req.ttl_seconds,
        )
        for s in req.steps:
            step = StepRecord(
                step_name=s.step_name,
                index=s.index,
                status=StepStatus(s.status),
                data=s.data,
                error=s.error,
            )
            ckpt.add_step(step)

        saved = _service.save_checkpoint(ckpt)
        return APIResponse(data=saved.to_dict())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"保存失败: {str(exc)}")


@router.get("/restore/{task_id}", response_model=APIResponse)
async def api_restore_checkpoint(task_id: str):
    """
    恢复指定任务的 Checkpoint。

    恢复逻辑:
      1. 加载持久化的 Checkpoint
      2. 确定恢复点（第一个失败的步骤或第一个未完成的步骤）
      3. 重置恢复点之后的步骤为 PENDING
      4. 返回恢复后的完整 Checkpoint

    如果任务已完成或不存在，返回对应信息。
    """
    try:
        ckpt = _service.restore_checkpoint(task_id)
        if ckpt is None:
            raise HTTPException(
                status_code=404,
                detail=f"Checkpoint 不存在或已过期: {task_id}",
            )
        return APIResponse(data=ckpt.to_dict())
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"恢复失败: {str(exc)}")


@router.get("/status/{task_id}", response_model=APIResponse)
async def api_checkpoint_status(task_id: str):
    """
    查询任务 Checkpoint 状态。

    返回精简快照（不含步骤详细数据），包括:
      - 进度百分比
      - 已完成/失败步骤数
      - 当前步骤索引
      - 恢复点
      - 过期时间
    """
    try:
        snapshot = _service.get_status(task_id)
        if snapshot is None:
            raise HTTPException(
                status_code=404,
                detail=f"Checkpoint 不存在或已过期: {task_id}",
            )
        return APIResponse(data=snapshot)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(exc)}")


@router.delete("/{task_id}", response_model=APIResponse)
async def api_delete_checkpoint(task_id: str):
    """删除指定任务的 Checkpoint"""
    try:
        deleted = _service.delete_checkpoint(task_id)
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"Checkpoint 不存在: {task_id}",
            )
        return APIResponse(message="已删除", data={"task_id": task_id})
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(exc)}")


@router.post("/create", response_model=APIResponse)
async def api_create_checkpoint(req: CreateCheckpointRequest):
    """
    从步骤名称列表创建新 Checkpoint。

    适用于任务启动前，先注册所有步骤名称，
    然后每步骤执行时通过 /step/update 更新状态。
    """
    try:
        ckpt = _service.create_from_task(
            task_id=req.task_id,
            step_names=req.step_names,
            metadata=req.metadata,
        )
        return APIResponse(data=ckpt.to_dict())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"创建失败: {str(exc)}")


@router.post("/step/update", response_model=APIResponse)
async def api_update_step(req: UpdateStepRequest):
    """
    更新单步执行状态。

    典型用法（任务处理循环中每步后调用）:
      POST /api/checkpoint/step/update
      {
        "task_id": "task_abc123",
        "step_index": 2,
        "status": "completed",
        "data": {"result": "...", "tokens_used": 150}
      }

    如果某步失败，传 status="failed" 和 error 信息。
    """
    try:
        status = StepStatus(req.status)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"无效的状态值: '{req.status}'。可选: {[s.value for s in StepStatus]}",
        )

    try:
        ckpt = _service.update_step_status(
            task_id=req.task_id,
            step_index=req.step_index,
            status=status,
            data=req.data if req.data else None,
            error=req.error,
        )
        if ckpt is None:
            raise HTTPException(
                status_code=404,
                detail=f"Checkpoint 不存在: {req.task_id}",
            )
        return APIResponse(data=ckpt.to_dict())
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"更新失败: {str(exc)}")


@router.get("/list", response_model=APIResponse)
async def api_list_checkpoints(
    include_expired: bool = Query(default=False, description="是否包含已过期的 Checkpoint"),
):
    """列出所有 Checkpoint 摘要"""
    try:
        items = _service.list_checkpoints(include_expired=include_expired)
        return APIResponse(data={
            "total": len(items),
            "checkpoints": items,
        })
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(exc)}")


@router.post("/cleanup", response_model=APIResponse)
async def api_cleanup_expired(
    max_age: int = Query(default=86400, description="过期阈值（秒，默认24小时）"),
):
    """
    手动触发过期 Checkpoint 清理。

    系统不会自动清理，需定时调用此接口或外部 cronjob。
    """
    try:
        removed = _service.cleanup_expired(max_age_seconds=max_age)
        return APIResponse(data={"removed": removed})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"清理失败: {str(exc)}")
