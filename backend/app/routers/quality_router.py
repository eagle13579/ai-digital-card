"""
quality_router.py — F18 Agent质量评估看板 API

API:
  POST   /api/quality/evaluate     — 执行质量评估（单条或批量）
  GET    /api/quality/dashboard    — 质量评估看板统计数据
  GET    /api/quality/samples      — 评测样本管理（列表/创建/删除）
  GET    /api/quality/baseline     — 基线查询与对比
"""
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Any, Optional

from app.services.quality_evaluator import (
    quality_evaluator,
    QualityEvaluator,
    QualityEvalError,
    SampleNotFoundError,
    BaselineNotFoundError,
    DEFAULT_PASSING_THRESHOLD,
)
from app.models.quality import QualityDimension, EvalStatus

router = APIRouter(prefix="/api/quality", tags=["F18 Agent质量评估看板"])


# ──────────────────────────────────────────────
# 请求/响应模型
# ──────────────────────────────────────────────

class ApiResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: Any = None


class SampleCreateRequest(BaseModel):
    input_text: str = Field(..., min_length=1, max_length=10000, description="用户输入/问题")
    agent_output: str = Field(..., min_length=1, max_length=50000, description="Agent输出/回答")
    expected_output: Optional[str] = Field(None, description="预期输出（可选）")
    category: Optional[str] = Field(None, description="样本分类")
    tags: list[str] = Field(default=[], description="样本标签")
    metadata: Optional[dict] = Field(default=None, description="附加元数据")
    canary_deployment_id: Optional[str] = Field(None, description="关联灰度部署ID")
    agent_version: Optional[str] = Field(None, description="Agent版本号")
    model_name: Optional[str] = Field(None, description="模型名称")


class EvaluateRequest(BaseModel):
    """评估请求 — 支持单样本或批量"""
    sample_ids: list[str] = Field(default=[], description="指定样本ID列表（批量）")
    input_text: Optional[str] = Field(None, description="直接传入输入文本（单样本快捷评估）")
    agent_output: Optional[str] = Field(None, description="直接传入Agent输出（单样本快捷评估）")
    category: Optional[str] = Field(None, description="按分类评估所有待评样本")
    concurrency: int = Field(default=5, ge=1, le=20, description="并发评估数")


class BaselineCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128, description="基线名称")
    description: Optional[str] = Field(None, description="基线描述")
    agent_version: Optional[str] = Field(None, description="Agent版本号")
    model_name: Optional[str] = Field(None, description="模型名称")
    canary_deployment_id: Optional[str] = Field(None, description="关联灰度部署ID")
    sample_ids: Optional[list[str]] = Field(None, description="指定样本ID（不传则用全部已评估样本）")
    passing_threshold: float = Field(default=DEFAULT_PASSING_THRESHOLD, ge=0, le=5, description="达标阈值")
    tags: list[str] = Field(default=[], description="标签")


class BaselineCompareRequest(BaseModel):
    baseline_ids: list[str] = Field(..., min_length=2, max_length=20, description="要对比的基线ID列表")


# ──────────────────────────────────────────────
# POST /api/quality/evaluate — 执行质量评估
# ──────────────────────────────────────────────

@router.post("/evaluate", response_model=ApiResponse)
async def evaluate(req: EvaluateRequest, background_tasks: BackgroundTasks):
    """执行LM-as-Judge质量评估

    支持三种模式：
      1. 直接传入 input_text + agent_output 评估单条
      2. 传入 sample_ids 批量评估已存在的样本
      3. 传入 category 按分类评估所有待评样本
    """
    try:
        # 模式1：直接传入内容评估
        if req.input_text and req.agent_output:
            # 先创建样本
            sample = await quality_evaluator.create_sample(
                input_text=req.input_text,
                agent_output=req.agent_output,
            )
            # 执行评估
            result = await quality_evaluator.evaluate_single(sample.sample_id)
            return ApiResponse(
                message="单样本评估完成",
                data={
                    "sample_id": result.sample_id,
                    "scores": result.scores,
                    "total_score": result.total_score,
                    "detail": result.detail,
                    "passed": result.passed,
                },
            )

        # 模式2：批量按样本ID
        if req.sample_ids:
            results, job_id = await quality_evaluator.evaluate_batch(
                sample_ids=req.sample_ids,
                concurrency=req.concurrency,
            )
            return ApiResponse(
                message=f"批量评估已完成: {len(results)} 个样本",
                data={
                    "job_id": job_id,
                    "total": len(results),
                    "results": [r.to_dict() for r in results],
                },
            )

        # 模式3：按分类评估
        if req.category:
            results, job_id = await quality_evaluator.evaluate_batch(
                category=req.category,
                concurrency=req.concurrency,
            )
            return ApiResponse(
                message=f"批量评估已完成: {len(results)} 个样本 (category={req.category})",
                data={
                    "job_id": job_id,
                    "category": req.category,
                    "total": len(results),
                    "results": [r.to_dict() for r in results],
                },
            )

        # 默认：评估所有待评样本
        results, job_id = await quality_evaluator.evaluate_batch(
            concurrency=req.concurrency,
        )
        return ApiResponse(
            message=f"全量评估已完成: {len(results)} 个样本",
            data={
                "job_id": job_id,
                "total": len(results),
                "results": [r.to_dict() for r in results],
            },
        )

    except QualityEvalError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"评估执行失败: {str(e)}")


# ──────────────────────────────────────────────
# GET /api/quality/dashboard — 看板统计
# ──────────────────────────────────────────────

@router.get("/dashboard", response_model=ApiResponse)
async def get_dashboard():
    """获取质量评估看板统计数据"""
    try:
        stats = await quality_evaluator.get_dashboard_stats()
        return ApiResponse(data=stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取看板数据失败: {str(e)}")


# ──────────────────────────────────────────────
# GET /api/quality/samples — 样本管理
# ──────────────────────────────────────────────

@router.get("/samples", response_model=ApiResponse)
async def list_samples(
    category: Optional[str] = Query(None, description="按分类过滤"),
    status: Optional[str] = Query(None, description="按状态过滤: pending/running/completed/failed"),
    agent_version: Optional[str] = Query(None, description="按Agent版本过滤"),
    model_name: Optional[str] = Query(None, description="按模型名称过滤"),
    tags: Optional[str] = Query(None, description="按标签过滤（逗号分隔）"),
    offset: int = Query(0, ge=0, description="分页偏移"),
    limit: int = Query(50, ge=1, le=200, description="每页数量"),
):
    """查询评测样本列表"""
    try:
        tag_list = tags.split(",") if tags else None
        samples, total = await quality_evaluator.list_samples(
            category=category,
            status=status,
            agent_version=agent_version,
            model_name=model_name,
            tags=tag_list,
            offset=offset,
            limit=limit,
        )
        return ApiResponse(data={
            "total": total,
            "offset": offset,
            "limit": limit,
            "samples": [s.to_dict() for s in samples],
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询样本失败: {str(e)}")


@router.post("/samples", response_model=ApiResponse)
async def create_sample(req: SampleCreateRequest):
    """创建评测样本"""
    try:
        sample = await quality_evaluator.create_sample(
            input_text=req.input_text,
            agent_output=req.agent_output,
            expected_output=req.expected_output,
            category=req.category,
            tags=req.tags,
            metadata=req.metadata,
            canary_deployment_id=req.canary_deployment_id,
            agent_version=req.agent_version,
            model_name=req.model_name,
        )
        return ApiResponse(
            message=f"样本 '{sample.sample_id}' 创建成功",
            data=sample.to_dict(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建样本失败: {str(e)}")


@router.delete("/samples/{sample_id}", response_model=ApiResponse)
async def delete_sample(sample_id: str):
    """删除评测样本"""
    deleted = await quality_evaluator.delete_sample(sample_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"样本不存在: {sample_id}")
    return ApiResponse(message=f"样本 '{sample_id}' 已删除")


@router.post("/samples/import-default", response_model=ApiResponse)
async def import_default_samples():
    """导入内置的20+评测样本"""
    try:
        count = await quality_evaluator.import_default_samples()
        return ApiResponse(
            message=f"已导入 {count} 个默认评测样本",
            data={"imported_count": count},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入默认样本失败: {str(e)}")


# ──────────────────────────────────────────────
# GET /api/quality/baseline — 基线管理
# ──────────────────────────────────────────────

@router.get("/baseline", response_model=ApiResponse)
async def list_baselines(
    agent_version: Optional[str] = Query(None, description="按Agent版本过滤"),
    is_active: Optional[bool] = Query(None, description="仅查询活跃基线"),
    offset: int = Query(0, ge=0, description="分页偏移"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """查询质量基线列表"""
    try:
        baselines, total = await quality_evaluator.list_baselines(
            agent_version=agent_version,
            is_active=is_active,
            offset=offset,
            limit=limit,
        )
        return ApiResponse(data={
            "total": total,
            "offset": offset,
            "limit": limit,
            "baselines": [bl.to_dict() for bl in baselines],
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询基线失败: {str(e)}")


@router.get("/baseline/{baseline_id}", response_model=ApiResponse)
async def get_baseline(baseline_id: str):
    """获取单个基线详情"""
    baseline = await quality_evaluator.get_baseline(baseline_id)
    if not baseline:
        raise HTTPException(status_code=404, detail=f"基线不存在: {baseline_id}")
    return ApiResponse(data=baseline.to_dict())


@router.post("/baseline", response_model=ApiResponse)
async def create_baseline(req: BaselineCreateRequest):
    """创建质量基线"""
    try:
        baseline = await quality_evaluator.create_baseline(
            name=req.name,
            description=req.description,
            agent_version=req.agent_version,
            model_name=req.model_name,
            canary_deployment_id=req.canary_deployment_id,
            sample_ids=req.sample_ids,
            passing_threshold=req.passing_threshold,
            tags=req.tags,
        )
        return ApiResponse(
            message=f"基线 '{baseline.baseline_id}' 创建成功",
            data=baseline.to_dict(),
        )
    except QualityEvalError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建基线失败: {str(e)}")


@router.post("/baseline/compare", response_model=ApiResponse)
async def compare_baselines(req: BaselineCompareRequest):
    """对比多个基线"""
    try:
        comparison = await quality_evaluator.compare_baselines(req.baseline_ids)
        return ApiResponse(
            message=f"对比了 {len(comparison)} 个基线",
            data={"comparison": comparison},
        )
    except BaselineNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对比基线失败: {str(e)}")


# ──────────────────────────────────────────────
# GET /api/quality/jobs — 评估任务管理
# ──────────────────────────────────────────────

@router.get("/jobs", response_model=ApiResponse)
async def list_eval_jobs(
    status: Optional[str] = Query(None, description="按状态过滤"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """查询评估任务列表"""
    try:
        from app.database import AsyncSessionLocal
        from sqlalchemy import select, desc, func
        from app.models.quality import QualityEvalJob

        async with AsyncSessionLocal() as session:
            query = select(QualityEvalJob)
            count_query = select(func.count(QualityEvalJob.id))

            if status:
                query = query.where(QualityEvalJob.status == status)
                count_query = count_query.where(QualityEvalJob.status == status)

            query = query.order_by(desc(QualityEvalJob.created_at)).offset(offset).limit(limit)

            total_result = await session.execute(count_query)
            total = total_result.scalar() or 0

            result = await session.execute(query)
            jobs = [j.to_dict() for j in result.scalars().all()]

        return ApiResponse(data={
            "total": total,
            "offset": offset,
            "limit": limit,
            "jobs": jobs,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询评估任务失败: {str(e)}")


# ──────────────────────────────────────────────
# 维度枚举信息
# ──────────────────────────────────────────────

@router.get("/dimensions", response_model=ApiResponse)
async def get_dimensions():
    """获取5个评估维度信息"""
    return ApiResponse(data={
        "dimensions": [
            {
                "key": d.value,
                "name": name,
                "description": desc,
            }
            for d, (name, desc) in zip(
                QualityDimension,
                [
                    ("有用性", "回答是否满足用户需求，提供有价值的信息"),
                    ("准确性", "事实是否正确，逻辑是否严谨"),
                    ("完整性", "是否全面覆盖问题，没有遗漏关键点"),
                    ("连贯性", "表达是否流畅，结构是否清晰，逻辑是否连贯"),
                    ("无害性", "内容是否安全，避免有害/歧视/误导性信息"),
                ],
            )
        ],
        "score_range": {
            "min": 0.0,
            "max": 5.0,
            "passing_threshold": DEFAULT_PASSING_THRESHOLD,
        },
    })
