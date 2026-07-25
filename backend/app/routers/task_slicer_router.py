"""
task_slicer_router.py — 任务切片管理 API (FastAPI)

POST /api/v1/tasks/slice  — 接收大任务，返回子任务列表
GET  /api/v1/tasks/slice  — 获取所有切片计划
GET  /api/v1/tasks/slice/stats — 引擎统计
DELETE /api/v1/tasks/slice — 清空切片计划
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from app.services.task_slicer import TaskSlicer
from app.models.task_slice import SliceMode

router = APIRouter(prefix="/api/tasks", tags=["任务切片"])

# 全局引擎（单例）
_slicer = TaskSlicer()

# 切片存储（内存，可按需替换为 DB）
_slice_plans: dict[str, dict] = {}


class SliceRequest(BaseModel):
    content: str = Field(..., description="大任务文本")
    mode: str = Field(default="token_budget", description="切片模式: token_budget | step | semantic")
    task_id: Optional[str] = Field(default=None, description="可选任务 ID")
    budget: Optional[int] = Field(default=None, description="Token 预算 (token_budget模式)")
    overlap: Optional[int] = Field(default=50, description="重叠 Tokens (token_budget模式)")
    step_markers: Optional[list[str]] = Field(default=None, description="自定义步骤标识 (step模式)")
    min_chunk_size: Optional[int] = Field(default=None, description="最小语义块大小 (semantic模式)")


# ── POST /api/v1/tasks/slice — 切片执行 ──

@router.post("/slice")
async def slice_task(req: SliceRequest):
    """接收大任务文本，按指定模式切分为子任务列表"""
    content = req.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="content 不能为空")

    mode = req.mode
    kwargs: dict = {}

    if mode == "token_budget":
        if req.budget is not None:
            kwargs["budget"] = req.budget
        kwargs["overlap"] = req.overlap
    elif mode == "step":
        if req.step_markers:
            kwargs["step_markers"] = req.step_markers
    elif mode == "semantic":
        if req.min_chunk_size is not None:
            kwargs["min_chunk_size"] = req.min_chunk_size
    else:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的切片模式: '{mode}'。可选: token_budget, step, semantic"
        )

    try:
        plan = _slicer.auto_slice(
            content=content,
            mode=mode,
            task_id=req.task_id,
            metadata={"source": "api"},
            **kwargs,
        )
        data = plan.to_dict()
        data["original_content"] = content[:200]
        _slice_plans[plan.task_id] = data
        return {"code": 0, "message": "success", "data": data}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"切片引擎内部错误: {str(e)}")


# ── GET /api/v1/tasks/slice — 查询切片计划 ──

@router.get("/slice")
async def list_slice_plans(task_id: Optional[str] = None):
    """获取切片计划列表（概要），或通过 task_id 查询详情"""
    if task_id:
        plan = _slice_plans.get(task_id)
        if plan is None:
            raise HTTPException(status_code=404, detail=f"切片计划不存在: {task_id}")
        return {"code": 0, "message": "success", "data": plan}

    summaries = []
    for tid, plan in _slice_plans.items():
        summaries.append({
            "task_id": tid,
            "mode": plan.get("mode"),
            "slice_count": plan.get("slice_count"),
            "total_token_estimate": plan.get("total_token_estimate"),
            "created_at": plan.get("created_at"),
        })
    return {"code": 0, "message": "success", "data": {"plans": summaries, "total": len(summaries)}}


# ── GET /api/v1/tasks/slice/stats — 引擎统计 ──

@router.get("/slice/stats")
async def slicer_stats():
    """返回切片引擎统计信息"""
    total_plans = len(_slice_plans)
    total_slices = sum(p.get("slice_count", 0) for p in _slice_plans.values())
    total_tokens = sum(p.get("total_token_estimate", 0) for p in _slice_plans.values())
    return {
        "code": 0, "message": "success",
        "data": {
            "engine": "TaskSlicer",
            "total_plans": total_plans,
            "total_slices": total_slices,
            "total_tokens_estimated": total_tokens,
            "modes_available": [m.value for m in SliceMode],
        }
    }


# ── DELETE /api/v1/tasks/slice — 清空切片计划 ──

@router.delete("/slice")
async def clear_slice_plans():
    """清空所有内存中的切片计划"""
    count = len(_slice_plans)
    _slice_plans.clear()
    return {"code": 0, "message": "success", "data": {"cleared": count}}
