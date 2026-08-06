"""
A/B 测试 API 路由
──────────────────
提供实验 CRUD、启动/停止、结果查询。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, delete, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.ab_test import ABTest, ABTestVariant, ABTestEvent, ABTestDecisionLog
from app.models.user import User
from app.routers.auth import get_current_user
from app.ai.ab_testing import (
    ABTestingEngine,
    get_ab_testing_engine,
    SignificanceTester,
)

router = APIRouter(prefix="/api/v1/ab-test", tags=["A/B测试"])


# ─── Pydantic Schemas ────────────────────────────────────

class VariantCreate(BaseModel):
    name: str
    description: str = ""
    is_control: bool = False
    config: dict[str, Any] | None = None
    weight: float = 1.0


class ExperimentCreate(BaseModel):
    name: str
    description: str = ""
    traffic_fraction: float = 1.0
    min_sample_size: int = 100
    significance_level: float = 0.05
    metric: str = "click_rate"
    target_brochure_id: int | None = None
    variants: list[VariantCreate] = []


class ExperimentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    traffic_fraction: float | None = None
    min_sample_size: int | None = None
    significance_level: float | None = None
    metric: str | None = None
    target_brochure_id: int | None = None


class EventRecord(BaseModel):
    experiment_id: int
    variant_id: int
    visitor_id: str | None = None
    event_type: str = "impression"
    metadata: dict[str, Any] | None = None


class ResultsQuery(BaseModel):
    method: str = "chi_square"  # chi_square | bayesian


# ─── CRUD 实验 ────────────────────────────────────────────

@router.post("/experiments")
async def create_experiment(
    data: ExperimentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建 A/B 测试实验。"""
    # 创建实验
    experiment = ABTest(
        user_id=current_user.id,
        name=data.name,
        description=data.description,
        status="draft",
        traffic_fraction=data.traffic_fraction,
        min_sample_size=data.min_sample_size,
        significance_level=data.significance_level,
        metric=data.metric,
        target_brochure_id=data.target_brochure_id,
    )
    db.add(experiment)
    await db.flush()

    # 创建变体
    for idx, v in enumerate(data.variants):
        variant = ABTestVariant(
            experiment_id=experiment.id,
            name=v.name,
            description=v.description,
            sort_order=idx,
            is_control=v.is_control or (idx == 0),
            config=v.config,
            weight=v.weight,
        )
        db.add(variant)

    await db.commit()
    await db.refresh(experiment)

    # 同步 AI 引擎
    engine = get_ab_testing_engine()
    engine.create_experiment(
        experiment_id=experiment.id,
        name=data.name,
        description=data.description,
        traffic_fraction=data.traffic_fraction,
        variants=[v.model_dump() for v in data.variants],
        min_sample_size=data.min_sample_size,
        significance_level=data.significance_level,
        metric=data.metric,
    )

    return {"code": 200, "message": "实验创建成功", "data": await _experiment_to_dict(experiment, db)}


@router.get("/experiments")
async def list_experiments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """列出当前用户的 A/B 测试实验。"""
    stmt = (
        select(ABTest)
        .where(ABTest.user_id == current_user.id)
        .order_by(ABTest.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    experiments = result.scalars().all()

    # 总数
    count_stmt = select(sa_func.count()).select_from(ABTest).where(ABTest.user_id == current_user.id)
    total = (await db.execute(count_stmt)).scalar() or 0

    items = []
    for exp in experiments:
        items.append(await _experiment_to_dict(exp, db))

    return {
        "code": 200,
        "message": "ok",
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.get("/experiments/{experiment_id}")
async def get_experiment(
    experiment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取实验详情。"""
    experiment = await _get_owned_experiment(experiment_id, current_user.id, db)
    if not experiment:
        raise HTTPException(status_code=404, detail="实验不存在")
    return {"code": 200, "message": "ok", "data": await _experiment_to_dict(experiment, db)}


@router.put("/experiments/{experiment_id}")
async def update_experiment(
    experiment_id: int,
    data: ExperimentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新实验配置（仅 draft 状态可修改）。"""
    experiment = await _get_owned_experiment(experiment_id, current_user.id, db)
    if not experiment:
        raise HTTPException(status_code=404, detail="实验不存在")
    if experiment.status != "draft":
        raise HTTPException(status_code=400, detail="仅草稿状态可修改")

    update_data = data.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(experiment, key, value)

    await db.commit()
    await db.refresh(experiment)
    return {"code": 200, "message": "更新成功", "data": await _experiment_to_dict(experiment, db)}


@router.delete("/experiments/{experiment_id}")
async def delete_experiment(
    experiment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除实验。"""
    experiment = await _get_owned_experiment(experiment_id, current_user.id, db)
    if not experiment:
        raise HTTPException(status_code=404, detail="实验不存在")

    await db.delete(experiment)
    await db.commit()

    # 同步 AI 引擎
    engine = get_ab_testing_engine()
    engine.delete_experiment(experiment_id)

    return {"code": 200, "message": "删除成功"}


# ─── 启动 / 停止 / 暂停 ──────────────────────────────────

@router.post("/experiments/{experiment_id}/start")
async def start_experiment(
    experiment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """启动实验（将状态从 draft 改为 running）。"""
    experiment = await _get_owned_experiment(experiment_id, current_user.id, db)
    if not experiment:
        raise HTTPException(status_code=404, detail="实验不存在")
    if experiment.status != "draft":
        raise HTTPException(status_code=400, detail=f"当前状态不允许启动: {experiment.status}")

    # 检查是否有变体
    variants_result = await db.execute(
        select(ABTestVariant).where(ABTestVariant.experiment_id == experiment_id)
    )
    variants = variants_result.scalars().all()
    if len(variants) < 2:
        raise HTTPException(status_code=400, detail="需要至少 2 个变体（包含对照组）")

    experiment.status = "running"
    experiment.started_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(experiment)

    # 同步 AI 引擎
    engine = get_ab_testing_engine()
    engine.start_experiment(experiment_id)

    return {"code": 200, "message": "实验已启动", "data": await _experiment_to_dict(experiment, db)}


@router.post("/experiments/{experiment_id}/pause")
async def pause_experiment(
    experiment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """暂停正在运行的实验。"""
    experiment = await _get_owned_experiment(experiment_id, current_user.id, db)
    if not experiment:
        raise HTTPException(status_code=404, detail="实验不存在")
    if experiment.status != "running":
        raise HTTPException(status_code=400, detail="仅运行中的实验可暂停")

    experiment.status = "paused"
    await db.commit()
    await db.refresh(experiment)

    engine = get_ab_testing_engine()
    engine.pause_experiment(experiment_id)

    return {"code": 200, "message": "实验已暂停", "data": await _experiment_to_dict(experiment, db)}


@router.post("/experiments/{experiment_id}/resume")
async def resume_experiment(
    experiment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """恢复暂停的实验。"""
    experiment = await _get_owned_experiment(experiment_id, current_user.id, db)
    if not experiment:
        raise HTTPException(status_code=404, detail="实验不存在")
    if experiment.status != "paused":
        raise HTTPException(status_code=400, detail="仅暂停中的实验可恢复")

    experiment.status = "running"
    await db.commit()
    await db.refresh(experiment)

    engine = get_ab_testing_engine()
    engine.resume_experiment(experiment_id)

    return {"code": 200, "message": "实验已恢复", "data": await _experiment_to_dict(experiment, db)}


@router.post("/experiments/{experiment_id}/stop")
async def stop_experiment(
    experiment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """停止实验并计算结果。"""
    experiment = await _get_owned_experiment(experiment_id, current_user.id, db)
    if not experiment:
        raise HTTPException(status_code=404, detail="实验不存在")
    if experiment.status not in ("running", "paused"):
        raise HTTPException(status_code=400, detail="仅运行中或暂停中的实验可停止")

    experiment.status = "completed"
    experiment.completed_at = datetime.now(timezone.utc)

    # 计算结果并缓存
    results = await _compute_results(experiment.id, db)
    experiment.cached_results = results

    await db.commit()
    await db.refresh(experiment)

    # 同步 AI 引擎
    engine = get_ab_testing_engine()
    engine.stop_experiment(experiment_id)

    return {"code": 200, "message": "实验已结束", "data": await _experiment_to_dict(experiment, db)}


# ─── 事件记录 ────────────────────────────────────────────

@router.post("/events")
async def record_event(
    data: EventRecord,
    current_user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """记录实验事件（支持免登录埋点）。"""
    # 验证实验存在
    exp_result = await db.execute(select(ABTest).where(ABTest.id == data.experiment_id))
    experiment = exp_result.scalars().first()
    if not experiment:
        raise HTTPException(status_code=404, detail="实验不存在")

    # 更新变体统计计数
    variant_result = await db.execute(
        select(ABTestVariant).where(ABTestVariant.id == data.variant_id)
    )
    variant = variant_result.scalars().first()
    if not variant:
        raise HTTPException(status_code=404, detail="变体不存在")

    if data.event_type == "impression":
        variant.impressions += 1
    elif data.event_type == "click":
        variant.clicks += 1
    elif data.event_type == "conversion":
        variant.conversions += 1
    elif data.event_type == "view":
        variant.views += 1

    event = ABTestEvent(
        experiment_id=data.experiment_id,
        variant_id=data.variant_id,
        user_id=current_user.id if current_user else None,
        visitor_id=data.visitor_id,
        event_type=data.event_type,
        metadata=data.metadata,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    return {
        "code": 200,
        "message": "事件已记录",
        "data": {"event_id": event.id, "event_type": event.event_type},
    }


# ─── 实验结果 ────────────────────────────────────────────

@router.get("/experiments/{experiment_id}/results")
async def get_results(
    experiment_id: int,
    method: str = Query("chi_square", regex="^(chi_square|bayesian)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取实验统计结果。"""
    experiment = await _get_owned_experiment(experiment_id, current_user.id, db)
    if not experiment:
        raise HTTPException(status_code=404, detail="实验不存在")

    # 如果有缓存结果且方法相同，直接返回
    if experiment.cached_results and experiment.cached_results.get("test_method") == method:
        return {"code": 200, "message": "ok", "data": experiment.cached_results}

    results = await _compute_results(experiment.id, db, method)

    # 仅 completed 状态才缓存
    if experiment.status == "completed":
        experiment.cached_results = results
        await db.commit()

    return {"code": 200, "message": "ok", "data": results}


@router.get("/experiments/{experiment_id}/events")
async def list_events(
    experiment_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    event_type: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取实验事件列表。"""
    experiment = await _get_owned_experiment(experiment_id, current_user.id, db)
    if not experiment:
        raise HTTPException(status_code=404, detail="实验不存在")

    stmt = (
        select(ABTestEvent)
        .where(ABTestEvent.experiment_id == experiment_id)
        .order_by(ABTestEvent.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    if event_type:
        stmt = stmt.where(ABTestEvent.event_type == event_type)

    result = await db.execute(stmt)
    events = result.scalars().all()

    count_stmt = select(sa_func.count()).select_from(ABTestEvent).where(
        ABTestEvent.experiment_id == experiment_id
    )
    if event_type:
        count_stmt = count_stmt.where(ABTestEvent.event_type == event_type)
    total = (await db.execute(count_stmt)).scalar() or 0

    return {
        "code": 200,
        "message": "ok",
        "data": {
            "items": [
                {
                    "id": e.id,
                    "variant_id": e.variant_id,
                    "user_id": e.user_id,
                    "visitor_id": e.visitor_id,
                    "event_type": e.event_type,
                    "metadata": e.event_meta,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                }
                for e in events
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


# ─── 自动决策 ────────────────────────────────────────────

@router.post("/{experiment_id}/auto-decision")
async def trigger_auto_decision(
    experiment_id: int,
    method: str = Query("chi_square", regex="^(chi_square|bayesian)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """触发实验的自动决策闭环。

    1. 获取实验事件 → 计算统计结果
    2. 根据 p_value 自动决策（rollout / continue / stop）
    3. 若决策为 rollout，自动发布胜出变体并写入 DB
    4. 记录决策日志
    """
    experiment = await _get_owned_experiment(experiment_id, current_user.id, db)
    if not experiment:
        raise HTTPException(status_code=404, detail="实验不存在")
    if experiment.status not in ("running", "paused"):
        raise HTTPException(status_code=400, detail=f"当前状态不允许自动决策: {experiment.status}")

    # 1. 从 DB 获取事件并计算结果
    results = await _compute_results(experiment.id, db, method)

    # 2. 调用引擎自动决策
    engine = get_ab_testing_engine()
    decision = engine.auto_decision(experiment_id, results)

    if decision.get("error"):
        raise HTTPException(status_code=400, detail=decision["error"])

    # 3. 若决策为 rollout，更新 DB
    if decision["decision"] == "rollout":
        variant_name = decision.get("variant_name")
        if variant_name:
            # 查找胜出变体并标记 is_default
            variants_result = await db.execute(
                select(ABTestVariant).where(
                    ABTestVariant.experiment_id == experiment_id,
                    ABTestVariant.name == variant_name,
                )
            )
            winner = variants_result.scalars().first()
            if winner:
                # 清除其它变体的 default 标记
                await db.execute(
                    delete(ABTestVariant).where(
                        ABTestVariant.experiment_id == experiment_id,
                        ABTestVariant.is_default == True,
                    )
                )
                winner.is_default = True

        # 更新实验状态为 completed
        experiment.status = "completed"
        experiment.completed_at = datetime.now(timezone.utc)
        experiment.cached_results = results

    elif decision["decision"] == "stop":
        # 停止实验
        experiment.status = "completed"
        experiment.completed_at = datetime.now(timezone.utc)
        experiment.cached_results = results

    # 4. 写入决策日志到 DB
    log_entry = ABTestDecisionLog(
        experiment_id=experiment_id,
        decision=decision["decision"],
        variant_name=decision.get("variant_name"),
        p_value=decision.get("p_value"),
        reason=decision.get("reason", ""),
        details=decision.get("details"),
    )
    db.add(log_entry)

    await db.commit()
    await db.refresh(experiment)
    await db.refresh(log_entry)

    return {
        "code": 200,
        "message": "自动决策完成",
        "data": {
            "decision": decision["decision"],
            "variant_name": decision.get("variant_name"),
            "p_value": decision.get("p_value"),
            "reason": decision.get("reason"),
            "log_id": log_entry.id,
            "experiment": await _experiment_to_dict(experiment, db),
        },
    }


@router.get("/{experiment_id}/decision-log")
async def get_decision_log(
    experiment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查看实验的自动决策历史。"""
    experiment = await _get_owned_experiment(experiment_id, current_user.id, db)
    if not experiment:
        raise HTTPException(status_code=404, detail="实验不存在")

    result = await db.execute(
        select(ABTestDecisionLog)
        .where(ABTestDecisionLog.experiment_id == experiment_id)
        .order_by(ABTestDecisionLog.created_at.desc())
    )
    logs = result.scalars().all()

    return {
        "code": 200,
        "message": "ok",
        "data": {
            "experiment_id": experiment_id,
            "logs": [
                {
                    "id": log.id,
                    "decision": log.decision,
                    "variant_name": log.variant_name,
                    "p_value": log.p_value,
                    "reason": log.reason,
                    "details": log.details,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                }
                for log in logs
            ],
        },
    }


# ─── 辅助函数 ────────────────────────────────────────────

async def _get_owned_experiment(
    experiment_id: int,
    user_id: int,
    db: AsyncSession,
) -> ABTest | None:
    """获取当前用户拥有的实验。"""
    result = await db.execute(
        select(ABTest).where(ABTest.id == experiment_id, ABTest.user_id == user_id)
    )
    return result.scalars().first()


async def _experiment_to_dict(experiment: ABTest, db: AsyncSession) -> dict[str, Any]:
    """将实验 ORM 对象转为字典。"""
    variants_result = await db.execute(
        select(ABTestVariant)
        .where(ABTestVariant.experiment_id == experiment.id)
        .order_by(ABTestVariant.sort_order)
    )
    variants = variants_result.scalars().all()

    return {
        "id": experiment.id,
        "user_id": experiment.user_id,
        "name": experiment.name,
        "description": experiment.description,
        "status": experiment.status,
        "traffic_fraction": experiment.traffic_fraction,
        "min_sample_size": experiment.min_sample_size,
        "significance_level": experiment.significance_level,
        "metric": experiment.metric,
        "target_brochure_id": experiment.target_brochure_id,
        "variants": [
            {
                "id": v.id,
                "name": v.name,
                "description": v.description,
                "sort_order": v.sort_order,
                "is_control": v.is_control,
                "config": v.config,
                "weight": v.weight,
                "impressions": v.impressions,
                "clicks": v.clicks,
                "conversions": v.conversions,
                "views": v.views,
            }
            for v in variants
        ],
        "cached_results": experiment.cached_results,
        "created_at": experiment.created_at.isoformat() if experiment.created_at else None,
        "updated_at": experiment.updated_at.isoformat() if experiment.updated_at else None,
        "started_at": experiment.started_at.isoformat() if experiment.started_at else None,
        "completed_at": experiment.completed_at.isoformat() if experiment.completed_at else None,
    }


async def _compute_results(
    experiment_id: int,
    db: AsyncSession,
    method: str = "chi_square",
) -> dict[str, Any]:
    """从事件数据计算实验结果。"""
    # 获取实验
    result = await db.execute(select(ABTest).where(ABTest.id == experiment_id))
    experiment = result.scalars().first()
    if not experiment:
        return {"error": "实验不存在"}

    # 获取变体
    variants_result = await db.execute(
        select(ABTestVariant)
        .where(ABTestVariant.experiment_id == experiment_id)
        .order_by(ABTestVariant.sort_order)
    )
    variants = variants_result.scalars().all()

    # 获取事件
    events_result = await db.execute(
        select(ABTestEvent).where(ABTestEvent.experiment_id == experiment_id)
    )
    events = events_result.scalars().all()

    if not variants:
        return {"error": "没有变体"}

    # 构建 AI 引擎所需格式
    engine_events = [
        {
            "variant_id": e.variant_id,
            "event_type": e.event_type,
            "user_id": e.user_id,
            "timestamp": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]

    # 使用 AI 引擎计算结果
    engine = get_ab_testing_engine()

    # 确保引擎中有此实验
    if not engine.get_experiment(experiment_id):
        engine.create_experiment(
            experiment_id=experiment.id,
            name=experiment.name,
            description=experiment.description or "",
            traffic_fraction=experiment.traffic_fraction,
            variants=[{"name": v.name, "is_control": v.is_control} for v in variants],
            min_sample_size=experiment.min_sample_size,
            significance_level=experiment.significance_level,
            metric=experiment.metric,
        )

    results = engine.compute_results(experiment_id, engine_events, method=method)

    # 补充变体名称
    variant_map = {v.id: v.name for v in variants}
    for v in results.get("variants", []):
        vid = v.get("variant_id")
        if vid is not None and vid in variant_map:
            v["variant_name"] = variant_map[vid]

    control = results.get("control", {})
    control_vid = control.get("variant_id")
    if control_vid is not None and control_vid in variant_map:
        control["variant_name"] = variant_map[control_vid]

    return results
