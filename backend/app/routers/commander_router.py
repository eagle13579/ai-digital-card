"""
commander_router.py — Commander-Worker 管理 API (FastAPI)

路由前缀: /api/commander

API 列表:
  POST   /api/commander/tasks          — 提交新任务（支持 content / slices / dag）
  GET    /api/commander/tasks          — 查询任务列表（支持按状态筛选）
  GET    /api/commander/tasks/{task_id} — 查询任务详情（含 DAG 状态）
  GET    /api/commander/tasks/{task_id}/dag  — 获取 DAG 完整定义
  POST   /api/commander/tasks/{task_id}/stop — 停止任务
  POST   /api/commander/tasks/{task_id}/retry — 重试任务
  POST   /api/commander/tasks/{task_id}/pause — 暂停任务
  POST   /api/commander/tasks/{task_id}/resume — 恢复任务
  GET    /api/commander/workers         — 查询 Worker Agent 列表
  GET    /api/commander/workers/{worker_id} — 查询单个 Worker
  GET    /api/commander/stats           — Commander 全局统计
"""

from __future__ import annotations
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field

from app.middleware.rbac import require_role
from app.models.commander import (
    CommanderTaskStatus,
    DAGDefinition,
    TaskNode,
    TaskNodeStatus,
)
from app.services.commander import get_commander

router = APIRouter(prefix="/api/commander", tags=["Commander调度层"])


# ── Request Schemas ────────────────────────────────────


class SubmitTaskRequest(BaseModel):
    title: str = Field(default="", description="任务标题")
    description: str = Field(default="", description="任务描述")
    task_id: Optional[str] = Field(default=None, description="可选自定义任务 ID")
    content: Optional[str] = Field(default=None, description="原始大任务文本（自动切片构建 DAG）")
    slices: Optional[list[dict[str, Any]]] = Field(
        default=None,
        description="预切片列表，每片需有 content 字段，可选 label/node_id/metadata",
    )
    dag: Optional[dict[str, Any]] = Field(
        default=None,
        description="显式 DAG 定义（override content/slices）",
    )
    user_id: Optional[str] = Field(default=None, description="提交用户标识")


class WorkerActionRequest(BaseModel):
    worker_id: str = Field(..., description="Worker ID")


# ── POST /api/commander/tasks — 提交任务 ─────────────


@router.post("/tasks", summary="提交新任务")
async def submit_task(req: SubmitTaskRequest, _: bool = Depends(require_role(["admin"]))):
    """提交任务到 Commander 调度层（修复 BUG-013：仅管理员）"""
    commander = get_commander()

    # 参数校验
    if not req.content and not req.slices and not req.dag:
        raise HTTPException(
            status_code=400,
            detail="必须至少提供 content、slices 或 dag 之一",
        )

    try:
        dag_obj = None
        if req.dag:
            dag_obj = DAGDefinition.from_dict(req.dag)
            try:
                dag_obj.validate()
            except ValueError as ve:
                raise HTTPException(status_code=400, detail=f"DAG 验证失败: {ve}")

        task = await commander.submit_task(
            title=req.title,
            description=req.description,
            task_id=req.task_id,
            content=req.content,
            slices=req.slices,
            dag=dag_obj,
            user_id=req.user_id,
        )

        return {
            "code": 0,
            "message": "任务已提交",
            "data": {
                "task_id": task.task_id,
                "title": task.title,
                "status": task.status.value,
                "dag_id": task.dag.dag_id if task.dag else None,
                "total_nodes": task.dag.total_nodes if task.dag else 0,
                "entry_nodes": task.dag.entry_nodes if task.dag else [],
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提交任务失败: {str(e)}")


# ── GET /api/commander/tasks — 任务列表 ──────────────


@router.get("/tasks", summary="查询任务列表")
async def list_tasks(
    _: bool = Depends(require_role(["admin"])),
    status: Optional[str] = None,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
):
    """查询所有任务（支持按状态筛选和分页）"""
    commander = get_commander()

    status_enum = None
    if status:
        try:
            status_enum = CommanderTaskStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的状态值: '{status}'。可选: {[s.value for s in CommanderTaskStatus]}",
            )

    tasks = commander.list_tasks(status=status_enum)
    total = len(tasks)
    start = (page - 1) * page_size
    end = start + page_size
    page_data = tasks[start:end]

    return {
        "code": 0,
        "message": "success",
        "data": {
            "tasks": page_data,
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


# ── GET /api/commander/tasks/{task_id} — 任务详情 ───


@router.get("/tasks/{task_id}", summary="查询任务详情")
async def get_task_detail(
    task_id: str = Path(..., description="任务 ID"),
    _: bool = Depends(require_role(["admin"])),
):
    """查询单个任务的完整详情（修复 BUG-013：仅管理员）"""
    commander = get_commander()
    task = commander.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")

    status_summary = commander.get_task_status(task_id)
    return {
        "code": 0,
        "message": "success",
        "data": status_summary,
    }


# ── GET /api/commander/tasks/{task_id}/dag — DAG 详情


@router.get("/tasks/{task_id}/dag", summary="获取任务 DAG 定义")
async def get_task_dag(
    task_id: str = Path(..., description="任务 ID"),
    _: bool = Depends(require_role(["admin"])),
):
    """获取任务的完整 DAG 定义（含所有节点及依赖关系）（修复 BUG-013：仅管理员）"""
    commander = get_commander()
    dag = commander.get_dag(task_id)
    if dag is None:
        raise HTTPException(status_code=404, detail=f"任务不存在或 DAG 未就绪: {task_id}")

    return {
        "code": 0,
        "message": "success",
        "data": dag.to_dict(),
    }


# ── POST /api/commander/tasks/{task_id}/stop — 停止任务


@router.post("/tasks/{task_id}/stop", summary="停止任务")
async def stop_task(
    task_id: str = Path(..., description="任务 ID"),
    _: bool = Depends(require_role(["admin"])),
):
    """停止/取消正在运行的任务（修复 BUG-013：仅管理员）"""
    commander = get_commander()
    success = await commander.stop_task(task_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"任务不存在或无法停止: {task_id}",
        )

    return {
        "code": 0,
        "message": f"任务已停止: {task_id}",
        "data": {"task_id": task_id, "status": CommanderTaskStatus.CANCELLED.value},
    }


# ── POST /api/commander/tasks/{task_id}/retry — 重试任务


@router.post("/tasks/{task_id}/retry", summary="重试失败任务")
async def retry_task(
    task_id: str = Path(..., description="任务 ID"),
    _: bool = Depends(require_role(["admin"])),
):
    """重试失败的任务（重置所有 FAILED 节点为 PENDING）（修复 BUG-013：仅管理员）"""
    commander = get_commander()
    success = await commander.retry_task(task_id)
    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"任务不存在或状态不允许重试: {task_id}",
        )

    return {
        "code": 0,
        "message": f"任务已重试: {task_id}",
        "data": {"task_id": task_id, "status": CommanderTaskStatus.RUNNING.value},
    }


# ── POST /api/commander/tasks/{task_id}/pause — 暂停任务


@router.post("/tasks/{task_id}/pause", summary="暂停任务")
async def pause_task(
    task_id: str = Path(..., description="任务 ID"),
    _: bool = Depends(require_role(["admin"])),
):
    """暂停运行中的任务（修复 BUG-013：仅管理员）"""
    commander = get_commander()
    success = await commander.pause_task(task_id)
    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"任务不存在或状态不允许暂停: {task_id}",
        )

    return {
        "code": 0,
        "message": f"任务已暂停: {task_id}",
        "data": {"task_id": task_id, "status": CommanderTaskStatus.SCHEDULING.value},
    }


# ── POST /api/commander/tasks/{task_id}/resume — 恢复任务


@router.post("/tasks/{task_id}/resume", summary="恢复任务")
async def resume_task(
    task_id: str = Path(..., description="任务 ID"),
    _: bool = Depends(require_role(["admin"])),
):
    """恢复暂停的任务（修复 BUG-013：仅管理员）"""
    commander = get_commander()
    success = await commander.resume_task(task_id)
    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"任务不存在或状态不允许恢复: {task_id}",
        )

    return {
        "code": 0,
        "message": f"任务已恢复: {task_id}",
        "data": {"task_id": task_id, "status": CommanderTaskStatus.RUNNING.value},
    }


# ── GET /api/commander/workers — Worker 列表 ─────────


@router.get("/workers", summary="查询 Worker Agent 列表")
async def list_workers(_: bool = Depends(require_role(["admin"]))):
    """列出所有 Worker Agent 及其当前状态（修复 BUG-013：仅管理员）"""
    commander = get_commander()
    workers = commander.list_workers()

    return {
        "code": 0,
        "message": "success",
        "data": {
            "workers": workers,
            "total": len(workers),
        },
    }


# ── GET /api/commander/workers/{worker_id} — 单个 Worker


@router.get("/workers/{worker_id}", summary="查询 Worker 详情")
async def get_worker_detail(
    worker_id: str = Path(..., description="Worker ID"),
    _: bool = Depends(require_role(["admin"])),
):
    """查询单个 Worker Agent 的详细信息（修复 BUG-013：仅管理员）"""
    commander = get_commander()
    worker = commander.get_worker(worker_id)
    if worker is None:
        raise HTTPException(status_code=404, detail=f"Worker 不存在: {worker_id}")

    return {
        "code": 0,
        "message": "success",
        "data": worker.to_dict(),
    }


# ── GET /api/commander/stats — 全局统计 ─────────────


@router.get("/stats", summary="Commander 全局统计")
async def commander_stats(_: bool = Depends(require_role(["admin"]))):
    """Commander 调度层全局统计信息（修复 BUG-013：仅管理员）"""
    commander = get_commander()
    stats = commander.get_stats()

    return {
        "code": 0,
        "message": "success",
        "data": stats,
    }
