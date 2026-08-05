"""
token_analytics_router.py — F19 Token消耗分析仪表盘 API (FastAPI)

API:
  GET  /api/token-analytics/summary      — Token 消耗汇总统计
  GET  /api/token-analytics/by-agent     — 按 Agent 聚合
  GET  /api/token-analytics/by-user      — 按用户聚合（Top N）
  GET  /api/token-analytics/trend        — 趋势分析
  GET  /api/token-analytics/agent-trend  — 各 Agent 趋势
  GET  /api/token-analytics/anomalies    — 异常检测
  GET  /api/token-analytics/alerts       — 预算预警列表
  POST /api/token-analytics/alerts/check — 检查并创建预警
  POST /api/token-analytics/alerts/resolve — 解决预警
  POST /api/token-analytics/record       — 写入消费记录
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Optional

from app.database import get_db
from app.services.token_analytics import (
    check_and_create_alerts,
    create_budget_alert,
    detect_anomalies,
    get_alerts,
    get_summary,
    get_by_agent,
    get_by_user,
    get_trend,
    get_agent_trend,
    record_consumption,
    resolve_alert,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/token-analytics", tags=["F19 Token消耗分析"])


# ── 请求/响应模型 ───────────────────────────

class ApiResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: Any = None


class RecordConsumptionRequest(BaseModel):
    agent_name: str = Field(..., description="Agent 名称")
    prompt_tokens: int = Field(default=0, ge=0, description="Prompt Token 数")
    completion_tokens: int = Field(default=0, ge=0, description="Completion Token 数")
    total_tokens: Optional[int] = Field(default=None, ge=0, description="总 Token 数（如不传则自动求和）")
    user_id: Optional[int] = Field(default=None, description="用户 ID")
    session_id: Optional[str] = Field(default=None, description="会话 ID")
    rule_name: Optional[str] = Field(default=None, description="预算规则名称")
    is_truncated: bool = Field(default=False, description="是否被截断")
    is_downgraded: bool = Field(default=False, description="是否被降级")
    degrade_strategy: Optional[str] = Field(default=None, description="降级策略")
    estimated_cost: float = Field(default=0.0, ge=0.0, description="估算成本（元）")
    cost_per_token: float = Field(default=0.0, ge=0.0, description="每 Token 单价（元）")
    model_name: Optional[str] = Field(default=None, description="模型名称")
    operation: Optional[str] = Field(default=None, description="操作类型")
    status: str = Field(default="success", description="状态: success / rejected / error")
    metadata_json: Optional[str] = Field(default=None, description="附加元数据（JSON）")


class ResolveAlertRequest(BaseModel):
    alert_id: str = Field(..., description="预警 ID")


# ── 辅助: 通用时间参数 ─────────────────────

def _time_params(
    period: str | None = Query(default=None, description="时间范围: today / yesterday / 7d / 30d / this_month / last_month"),
    start: str | None = Query(default=None, description="起始时间 (ISO8601)"),
    end: str | None = Query(default=None, description="结束时间 (ISO8601)"),
) -> dict[str, str | None]:
    return {"period": period, "start": start, "end": end}


# ═══════════════════════════════════════════
# GET /api/token-analytics/summary
# ═══════════════════════════════════════════

@router.get("/summary", response_model=ApiResponse)
async def summary(
    db: AsyncSession = Depends(get_db),
    period: str | None = Query(default=None, description="时间范围"),
    start: str | None = Query(default=None, description="起始时间"),
    end: str | None = Query(default=None, description="结束时间"),
):
    """获取 Token 消耗汇总统计 + 预算状态"""
    try:
        data = await get_summary(db, period=period, start=start, end=end)
        return ApiResponse(data=data)
    except Exception as e:
        logger.exception("Token 分析汇总查询失败")
        raise HTTPException(status_code=500, detail=f"查询失败: {e}")


# ═══════════════════════════════════════════
# GET /api/token-analytics/by-agent
# ═══════════════════════════════════════════

@router.get("/by-agent", response_model=ApiResponse)
async def by_agent(
    db: AsyncSession = Depends(get_db),
    period: str | None = Query(default=None, description="时间范围"),
    start: str | None = Query(default=None, description="起始时间"),
    end: str | None = Query(default=None, description="结束时间"),
    agent_name: str | None = Query(default=None, description="筛选特定 Agent"),
):
    """按 Agent 维度聚合 Token 消耗"""
    try:
        data = await get_by_agent(db, period=period, start=start, end=end, agent_name=agent_name)
        return ApiResponse(data={"agents": data, "total": len(data)})
    except Exception as e:
        logger.exception("Token Agent 维度查询失败")
        raise HTTPException(status_code=500, detail=f"查询失败: {e}")


# ═══════════════════════════════════════════
# GET /api/token-analytics/by-user
# ═══════════════════════════════════════════

@router.get("/by-user", response_model=ApiResponse)
async def by_user(
    db: AsyncSession = Depends(get_db),
    period: str | None = Query(default=None, description="时间范围"),
    start: str | None = Query(default=None, description="起始时间"),
    end: str | None = Query(default=None, description="结束时间"),
    limit: int = Query(default=50, ge=1, le=200, description="返回用户数上限"),
):
    """按用户维度聚合 Token 消耗（Top N）"""
    try:
        data = await get_by_user(db, period=period, start=start, end=end, limit=limit)
        return ApiResponse(data={"users": data, "total": len(data)})
    except Exception as e:
        logger.exception("Token 用户维度查询失败")
        raise HTTPException(status_code=500, detail=f"查询失败: {e}")


# ═══════════════════════════════════════════
# GET /api/token-analytics/trend
# ═══════════════════════════════════════════

@router.get("/trend", response_model=ApiResponse)
async def trend(
    db: AsyncSession = Depends(get_db),
    period: str | None = Query(default=None, description="时间范围"),
    start: str | None = Query(default=None, description="起始时间"),
    end: str | None = Query(default=None, description="结束时间"),
    granularity: str = Query(default="day", description="粒度: hour / day / week / month"),
    agent_name: str | None = Query(default=None, description="筛选特定 Agent"),
):
    """获取 Token 消耗趋势数据"""
    if granularity not in ("hour", "day", "week", "month"):
        raise HTTPException(status_code=400, detail="粒度参数无效，可选: hour, day, week, month")
    try:
        data = await get_trend(db, period=period, start=start, end=end, granularity=granularity, agent_name=agent_name)
        return ApiResponse(data={"trend": data, "total_points": len(data)})
    except Exception as e:
        logger.exception("Token 趋势查询失败")
        raise HTTPException(status_code=500, detail=f"查询失败: {e}")


# ═══════════════════════════════════════════
# GET /api/token-analytics/agent-trend
# ═══════════════════════════════════════════

@router.get("/agent-trend", response_model=ApiResponse)
async def agent_trend(
    db: AsyncSession = Depends(get_db),
    period: str | None = Query(default=None, description="时间范围"),
    start: str | None = Query(default=None, description="起始时间"),
    end: str | None = Query(default=None, description="结束时间"),
    granularity: str = Query(default="day", description="粒度: hour / day / week / month"),
):
    """获取各 Agent 的消耗趋势（按 Agent 分组）"""
    if granularity not in ("hour", "day", "week", "month"):
        raise HTTPException(status_code=400, detail="粒度参数无效，可选: hour, day, week, month")
    try:
        data = await get_agent_trend(db, period=period, start=start, end=end, granularity=granularity)
        return ApiResponse(data={"agent_trend": data, "agent_count": len(data)})
    except Exception as e:
        logger.exception("Agent 趋势查询失败")
        raise HTTPException(status_code=500, detail=f"查询失败: {e}")


# ═══════════════════════════════════════════
# GET /api/token-analytics/anomalies
# ═══════════════════════════════════════════

@router.get("/anomalies", response_model=ApiResponse)
async def anomalies(
    db: AsyncSession = Depends(get_db),
    period: str | None = Query(default=None, description="时间范围"),
    z_score_threshold: float = Query(default=2.0, ge=1.0, le=5.0, description="Z-Score 异常阈值"),
):
    """检测 Token 消耗异常（突增/突降/错误率/预算超限）"""
    try:
        data = await detect_anomalies(db, period=period, z_score_threshold=z_score_threshold)
        return ApiResponse(data=data)
    except Exception as e:
        logger.exception("Token 异常检测失败")
        raise HTTPException(status_code=500, detail=f"异常检测失败: {e}")


# ═══════════════════════════════════════════
# GET /api/token-analytics/alerts
# ═══════════════════════════════════════════

@router.get("/alerts", response_model=ApiResponse)
async def alerts(
    db: AsyncSession = Depends(get_db),
    period: str | None = Query(default=None, description="时间范围"),
    start: str | None = Query(default=None, description="起始时间"),
    end: str | None = Query(default=None, description="结束时间"),
    alert_level: str | None = Query(default=None, description="预警级别: info / warning / critical"),
    rule_name: str | None = Query(default=None, description="筛选特定预算规则"),
    unresolved_only: bool = Query(default=False, description="仅未解决的预警"),
    limit: int = Query(default=50, ge=1, le=200, description="每页数量"),
    offset: int = Query(default=0, ge=0, description="偏移量"),
):
    """获取预算预警记录"""
    try:
        data = await get_alerts(
            db,
            period=period,
            start=start,
            end=end,
            alert_level=alert_level,
            rule_name=rule_name,
            unresolved_only=unresolved_only,
            limit=limit,
            offset=offset,
        )
        return ApiResponse(data=data)
    except Exception as e:
        logger.exception("预警查询失败")
        raise HTTPException(status_code=500, detail=f"查询失败: {e}")


# ═══════════════════════════════════════════
# POST /api/token-analytics/alerts/check
# ═══════════════════════════════════════════

@router.post("/alerts/check", response_model=ApiResponse)
async def check_alerts(
    db: AsyncSession = Depends(get_db),
):
    """检查所有预算规则状态，自动创建预警记录"""
    try:
        new_alerts = await check_and_create_alerts(db)
        return ApiResponse(
            message=f"检查完成，新创建 {len(new_alerts)} 条预警",
            data={"new_alerts": new_alerts, "count": len(new_alerts)},
        )
    except Exception as e:
        logger.exception("检查预警失败")
        raise HTTPException(status_code=500, detail=f"检查预警失败: {e}")


# ═══════════════════════════════════════════
# POST /api/token-analytics/alerts/resolve
# ═══════════════════════════════════════════

@router.post("/alerts/resolve", response_model=ApiResponse)
async def resolve_alert_endpoint(
    req: ResolveAlertRequest,
    db: AsyncSession = Depends(get_db),
):
    """将指定预警标记为已解决"""
    try:
        success = await resolve_alert(db, req.alert_id)
        if success:
            return ApiResponse(message=f"预警 {req.alert_id} 已解决")
        else:
            raise HTTPException(status_code=404, detail=f"预警 {req.alert_id} 不存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("解决预警失败")
        raise HTTPException(status_code=500, detail=f"解决预警失败: {e}")


# ═══════════════════════════════════════════
# POST /api/token-analytics/record
# ═══════════════════════════════════════════

@router.post("/record", response_model=ApiResponse)
async def record_consumption_endpoint(
    req: RecordConsumptionRequest,
    db: AsyncSession = Depends(get_db),
):
    """写入一条 Token 消费记录"""
    try:
        record = await record_consumption(
            db=db,
            agent_name=req.agent_name,
            prompt_tokens=req.prompt_tokens,
            completion_tokens=req.completion_tokens,
            total_tokens=req.total_tokens,
            user_id=req.user_id,
            session_id=req.session_id,
            rule_name=req.rule_name,
            is_truncated=req.is_truncated,
            is_downgraded=req.is_downgraded,
            degrade_strategy=req.degrade_strategy,
            estimated_cost=req.estimated_cost,
            cost_per_token=req.cost_per_token,
            model_name=req.model_name,
            operation=req.operation,
            status=req.status,
            metadata_json=req.metadata_json,
        )
        if record:
            return ApiResponse(message="消费记录已写入", data=record.to_dict())
        else:
            raise HTTPException(status_code=500, detail="写入消费记录失败")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("写入消费记录失败")
        raise HTTPException(status_code=500, detail=f"写入失败: {e}")


# ── Health ──────────────────────────────────

@router.get("/health", response_model=ApiResponse)
async def health():
    """Token 分析服务健康检查"""
    return ApiResponse(data={
        "subsystem": "token_analytics",
        "status": "healthy",
        "version": "1.0.0",
    })
