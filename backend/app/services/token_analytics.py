"""
token_analytics.py — F19 Token消耗分析服务

功能:
  - 多维度聚合（按 Agent / 用户 / 时段）
  - 趋势分析（日/周/月）
  - 异常检测（突增/突降/均值漂移）
  - 预算预警（接近阈值/超限/成本异常）
"""
from __future__ import annotations

import json
import logging
import math
import statistics
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import Select, and_, case, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.token_analytics import (
    AgentTokenSummary,
    TokenBudgetAlert,
    TokenConsumptionRecord,
    TokenSummaryStats,
)
from app.services.token_budget import token_budget_registry

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════
# 辅助: 时间范围解析
# ═══════════════════════════════════════════════════

def _parse_time_range(
    period: str | None,
    start: str | None,
    end: str | None,
) -> tuple[datetime | None, datetime | None]:
    """解析时间范围参数，返回 (start_dt, end_dt)"""
    now = datetime.utcnow()

    if start:
        try:
            start_dt = datetime.fromisoformat(start)
        except ValueError:
            start_dt = now - timedelta(days=7)
    elif period == "today":
        start_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "yesterday":
        start_dt = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return start_dt, end_dt
    elif period == "7d":
        start_dt = now - timedelta(days=7)
    elif period == "30d":
        start_dt = now - timedelta(days=30)
    elif period == "this_month":
        start_dt = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == "last_month":
        first_this = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_dt = (first_this - timedelta(days=1)).replace(day=1)
        end_dt = first_this
        return start_dt, end_dt
    else:
        start_dt = now - timedelta(days=7)  # 默认近7天

    if end:
        try:
            end_dt = datetime.fromisoformat(end)
        except ValueError:
            end_dt = now
    else:
        end_dt = now

    return start_dt, end_dt


def _build_time_filter(
    query: Select,
    start_dt: datetime | None,
    end_dt: datetime | None,
    column_name: str = "created_at",
) -> Select:
    """为查询添加时间范围过滤"""
    if start_dt:
        query = query.where(text(f"token_consumption_record.{column_name} >= :start_dt"))
    if end_dt:
        query = query.where(text(f"token_consumption_record.{column_name} <= :end_dt"))
    return query


# ═══════════════════════════════════════════════════
# 1. 多维度聚合
# ═══════════════════════════════════════════════════

async def get_summary(
    db: AsyncSession,
    period: str | None = None,
    start: str | None = None,
    end: str | None = None,
) -> dict[str, Any]:
    """获取 Token 消耗汇总统计"""
    start_dt, end_dt = _parse_time_range(period, start, end)

    params: dict[str, Any] = {}
    where_clauses = ["1=1"]

    if start_dt:
        where_clauses.append("created_at >= :start_dt")
        params["start_dt"] = start_dt
    if end_dt:
        where_clauses.append("created_at <= :end_dt")
        params["end_dt"] = end_dt

    where_sql = " AND ".join(where_clauses)

    # 基础汇总
    sql = f"""
        SELECT
            COALESCE(SUM(total_tokens), 0) AS total_tokens,
            COALESCE(SUM(prompt_tokens), 0) AS total_prompt_tokens,
            COALESCE(SUM(completion_tokens), 0) AS total_completion_tokens,
            COALESCE(SUM(estimated_cost), 0) AS total_cost,
            COUNT(*) AS total_requests,
            SUM(CASE WHEN is_truncated = 1 THEN 1 ELSE 0 END) AS truncated_count,
            SUM(CASE WHEN is_downgraded = 1 THEN 1 ELSE 0 END) AS downgraded_count,
            SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) AS rejected_count,
            COUNT(DISTINCT agent_name) AS unique_agents,
            COUNT(DISTINCT user_id) AS unique_users
        FROM token_consumption_record
        WHERE {where_sql}
    """
    result = await db.execute(text(sql), params)
    row = result.fetchone()

    # 预算状态信息（来自 F13 TokenBudgetRegistry）
    budget_statuses = token_budget_registry.all_status()
    budget_info = {
        "total_budget_rules": len(budget_statuses),
        "total_exceeded": sum(1 for s in budget_statuses if s.is_exceeded),
        "total_warning": sum(1 for s in budget_statuses if s.is_warning),
        "rules": [
            {
                "name": s.name,
                "token_limit": s.rule.token_limit,
                "current_usage": s.current_usage,
                "usage_ratio": round(s.usage_ratio, 4),
                "remaining_tokens": s.remaining_tokens,
                "is_warning": s.is_warning,
                "is_exceeded": s.is_exceeded,
            }
            for s in budget_statuses
        ],
    }

    stats = TokenSummaryStats(
        total_tokens=row[0] or 0,
        total_prompt_tokens=row[1] or 0,
        total_completion_tokens=row[2] or 0,
        total_cost=float(row[3] or 0),
        total_requests=row[4] or 0,
        truncated_count=row[5] or 0,
        downgraded_count=row[6] or 0,
        rejected_count=row[7] or 0,
        unique_agents=row[8] or 0,
        unique_users=row[9] or 0,
        avg_tokens_per_request=(row[0] or 0) / max(row[4] or 1, 1),
        period_start=start_dt.isoformat() if start_dt else None,
        period_end=end_dt.isoformat() if end_dt else None,
    )

    return {
        "summary": stats.to_dict(),
        "budget_status": budget_info,
    }


async def get_by_agent(
    db: AsyncSession,
    period: str | None = None,
    start: str | None = None,
    end: str | None = None,
    agent_name: str | None = None,
) -> list[dict[str, Any]]:
    """按 Agent 维度聚合 Token 消耗"""
    start_dt, end_dt = _parse_time_range(period, start, end)

    params: dict[str, Any] = {}
    where_clauses = ["1=1"]

    if start_dt:
        where_clauses.append("created_at >= :start_dt")
        params["start_dt"] = start_dt
    if end_dt:
        where_clauses.append("created_at <= :end_dt")
        params["end_dt"] = end_dt
    if agent_name:
        where_clauses.append("agent_name = :agent_name")
        params["agent_name"] = agent_name

    where_sql = " AND ".join(where_clauses)

    sql = f"""
        SELECT
            agent_name,
            COALESCE(SUM(total_tokens), 0) AS total_tokens,
            COALESCE(SUM(estimated_cost), 0) AS total_cost,
            COUNT(*) AS total_requests,
            SUM(CASE WHEN is_truncated = 1 THEN 1 ELSE 0 END) AS truncated_count,
            SUM(CASE WHEN is_downgraded = 1 THEN 1 ELSE 0 END) AS downgraded_count,
            COUNT(DISTINCT user_id) AS unique_users
        FROM token_consumption_record
        WHERE {where_sql}
        GROUP BY agent_name
        ORDER BY total_tokens DESC
    """
    result = await db.execute(text(sql), params)
    rows = result.fetchall()

    # 注入预算信息
    budget_map = {}
    for bs in token_budget_registry.all_status():
        budget_map[bs.name] = {
            "token_limit": bs.rule.token_limit,
            "usage_ratio": bs.usage_ratio,
        }

    agents = []
    for row in rows:
        name = row[0]
        budget_info = budget_map.get(name, {})
        agents.append(
            AgentTokenSummary(
                agent_name=name,
                total_tokens=row[1] or 0,
                total_cost=float(row[2] or 0),
                total_requests=row[3] or 0,
                truncated_count=row[4] or 0,
                downgraded_count=row[5] or 0,
                unique_users=row[6] or 0,
                token_limit=budget_info.get("token_limit", 0),
                usage_ratio=budget_info.get("usage_ratio", 0.0),
            ).to_dict()
        )

    return agents


async def get_by_user(
    db: AsyncSession,
    period: str | None = None,
    start: str | None = None,
    end: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """按用户维度聚合 Token 消耗（Top N）"""
    start_dt, end_dt = _parse_time_range(period, start, end)

    params: dict[str, Any] = {}
    where_clauses = ["user_id IS NOT NULL"]

    if start_dt:
        where_clauses.append("created_at >= :start_dt")
        params["start_dt"] = start_dt
    if end_dt:
        where_clauses.append("created_at <= :end_dt")
        params["end_dt"] = end_dt

    where_sql = " AND ".join(where_clauses)

    sql = f"""
        SELECT
            user_id,
            COALESCE(SUM(total_tokens), 0) AS total_tokens,
            COALESCE(SUM(estimated_cost), 0) AS total_cost,
            COUNT(*) AS total_requests,
            COUNT(DISTINCT agent_name) AS agent_count,
            SUM(CASE WHEN is_truncated = 1 THEN 1 ELSE 0 END) AS truncated_count,
            SUM(CASE WHEN is_downgraded = 1 THEN 1 ELSE 0 END) AS downgraded_count,
            MAX(created_at) AS last_active
        FROM token_consumption_record
        WHERE {where_sql}
        GROUP BY user_id
        ORDER BY total_tokens DESC
        LIMIT :limit_val
    """
    params["limit_val"] = limit
    result = await db.execute(text(sql), params)
    rows = result.fetchall()

    users = []
    for row in rows:
        users.append({
            "user_id": row[0],
            "total_tokens": row[1] or 0,
            "total_cost": round(float(row[2] or 0), 4),
            "total_requests": row[3] or 0,
            "agent_count": row[4] or 0,
            "truncated_count": row[5] or 0,
            "downgraded_count": row[6] or 0,
            "avg_tokens_per_request": round((row[1] or 0) / max(row[3] or 1, 1), 2),
            "last_active": row[7].isoformat() if row[7] else None,
        })
    return users


# ═══════════════════════════════════════════════════
# 2. 趋势分析
# ═══════════════════════════════════════════════════

async def get_trend(
    db: AsyncSession,
    period: str | None = None,
    start: str | None = None,
    end: str | None = None,
    granularity: str = "day",
    agent_name: str | None = None,
) -> list[dict[str, Any]]:
    """获取 Token 消耗趋势数据"""
    start_dt, end_dt = _parse_time_range(period, start, end)

    params: dict[str, Any] = {}
    where_clauses = ["1=1"]

    if start_dt:
        where_clauses.append("created_at >= :start_dt")
        params["start_dt"] = start_dt
    if end_dt:
        where_clauses.append("created_at <= :end_dt")
        params["end_dt"] = end_dt
    if agent_name:
        where_clauses.append("agent_name = :agent_name")
        params["agent_name"] = agent_name

    where_sql = " AND ".join(where_clauses)

    # 根据粒度选择时间分组格式
    if granularity == "hour":
        date_format = "%Y-%m-%d %H:00"
        date_trunc = "strftime('%Y-%m-%d %H:00', created_at)"
    elif granularity == "week":
        date_format = "%Y-%W"
        date_trunc = "strftime('%Y-%W', created_at)"
    elif granularity == "month":
        date_format = "%Y-%m"
        date_trunc = "strftime('%Y-%m', created_at)"
    else:  # day (default)
        date_format = "%Y-%m-%d"
        date_trunc = "strftime('%Y-%m-%d', created_at)"

    sql = f"""
        SELECT
            {date_trunc} AS period,
            COALESCE(SUM(total_tokens), 0) AS total_tokens,
            COALESCE(SUM(prompt_tokens), 0) AS prompt_tokens,
            COALESCE(SUM(completion_tokens), 0) AS completion_tokens,
            COALESCE(SUM(estimated_cost), 0) AS total_cost,
            COUNT(*) AS total_requests,
            SUM(CASE WHEN is_truncated = 1 THEN 1 ELSE 0 END) AS truncated_count,
            SUM(CASE WHEN is_downgraded = 1 THEN 1 ELSE 0 END) AS downgraded_count,
            SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) AS rejected_count,
            COUNT(DISTINCT user_id) AS active_users
        FROM token_consumption_record
        WHERE {where_sql}
        GROUP BY period
        ORDER BY period ASC
    """
    result = await db.execute(text(sql), params)
    rows = result.fetchall()

    trend_data = []
    for row in rows:
        trend_data.append({
            "period": row[0],
            "total_tokens": row[1] or 0,
            "prompt_tokens": row[2] or 0,
            "completion_tokens": row[3] or 0,
            "total_cost": round(float(row[4] or 0), 4),
            "total_requests": row[5] or 0,
            "truncated_count": row[6] or 0,
            "downgraded_count": row[7] or 0,
            "rejected_count": row[8] or 0,
            "active_users": row[9] or 0,
            "avg_tokens_per_request": round((row[1] or 0) / max(row[5] or 1, 1), 2),
        })

    return trend_data


async def get_agent_trend(
    db: AsyncSession,
    period: str | None = None,
    start: str | None = None,
    end: str | None = None,
    granularity: str = "day",
) -> dict[str, list[dict[str, Any]]]:
    """获取各 Agent 的趋势数据（按 Agent 分组）"""
    start_dt, end_dt = _parse_time_range(period, start, end)

    params: dict[str, Any] = {}
    where_clauses = ["1=1"]

    if start_dt:
        where_clauses.append("created_at >= :start_dt")
        params["start_dt"] = start_dt
    if end_dt:
        where_clauses.append("created_at <= :end_dt")
        params["end_dt"] = end_dt

    where_sql = " AND ".join(where_clauses)

    if granularity == "hour":
        date_trunc = "strftime('%Y-%m-%d %H:00', created_at)"
    elif granularity == "week":
        date_trunc = "strftime('%Y-%W', created_at)"
    elif granularity == "month":
        date_trunc = "strftime('%Y-%m', created_at)"
    else:
        date_trunc = "strftime('%Y-%m-%d', created_at)"

    sql = f"""
        SELECT
            agent_name,
            {date_trunc} AS period,
            COALESCE(SUM(total_tokens), 0) AS total_tokens,
            COALESCE(SUM(estimated_cost), 0) AS total_cost,
            COUNT(*) AS total_requests
        FROM token_consumption_record
        WHERE {where_sql}
        GROUP BY agent_name, period
        ORDER BY agent_name, period ASC
    """
    result = await db.execute(text(sql), params)
    rows = result.fetchall()

    agent_trend: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        name = row[0]
        entry = {
            "period": row[1],
            "total_tokens": row[2] or 0,
            "total_cost": round(float(row[3] or 0), 4),
            "total_requests": row[4] or 0,
        }
        if name not in agent_trend:
            agent_trend[name] = []
        agent_trend[name].append(entry)

    return agent_trend


# ═══════════════════════════════════════════════════
# 3. 异常检测
# ═══════════════════════════════════════════════════

async def detect_anomalies(
    db: AsyncSession,
    period: str | None = None,
    z_score_threshold: float = 2.0,
) -> dict[str, Any]:
    """
    检测 Token 消耗异常。

    检测维度:
      1. 单日 Token 消耗突增/突降（基于 Z-Score）
      2. 请求量异常
      3. 错误率突增
      4. Token/请求比异常

    Returns:
        {
            "has_anomaly": bool,
            "anomalies": [...],
            "metrics": {...}
        }
    """
    start_dt, end_dt = _parse_time_range(period, None, None)
    # 取 2 倍时间范围用于计算基线
    baseline_start = start_dt - (end_dt - start_dt) if start_dt and end_dt else None

    params: dict[str, Any] = {}
    where_current = ["1=1"]
    where_baseline = ["1=1"]

    if start_dt:
        where_current.append("created_at >= :start_dt")
        params["start_dt"] = start_dt
    if end_dt:
        where_current.append("created_at <= :end_dt")
        params["end_dt"] = end_dt
    if baseline_start:
        where_baseline.append("created_at >= :baseline_start")
        params["baseline_start"] = baseline_start
    if start_dt:
        where_baseline.append("created_at < :start_dt")
        params["baseline_start_cut"] = start_dt

    # 获取每日 Token 消耗历史（用于 Z-Score 计算）
    sql_daily = """
        SELECT
            strftime('%Y-%m-%d', created_at) AS day,
            COALESCE(SUM(total_tokens), 0) AS total_tokens,
            COUNT(*) AS total_requests,
            COALESCE(SUM(CASE WHEN status = 'error' OR status = 'rejected' THEN 1 ELSE 0 END), 0) AS error_count
        FROM token_consumption_record
        WHERE created_at >= :baseline_dt
        GROUP BY day
        ORDER BY day ASC
    """
    baseline_dt = baseline_start if baseline_start else (datetime.utcnow() - timedelta(days=30))
    daily_result = await db.execute(text(sql_daily), {"baseline_dt": baseline_dt})
    daily_rows = daily_result.fetchall()

    anomalies = []

    if len(daily_rows) < 3:
        return {
            "has_anomaly": False,
            "anomalies": [],
            "metrics": {"total_days": len(daily_rows), "note": "数据点不足，无法进行异常检测"},
        }

    # 1. Token 消耗 Z-Score 异常检测
    token_values = [row[1] for row in daily_rows]
    req_values = [row[2] for row in daily_rows]
    err_values = [row[3] for row in daily_rows]

    token_mean = statistics.mean(token_values)
    token_stdev = statistics.stdev(token_values) if len(token_values) > 1 else 0

    req_mean = statistics.mean(req_values)
    req_stdev = statistics.stdev(req_values) if len(req_values) > 1 else 0

    err_total = sum(err_values)
    err_rate_total = err_total / max(sum(req_values), 1)

    for i, row in enumerate(daily_rows):
        day = row[0]
        day_tokens = row[1]
        day_requests = row[2]
        day_errors = row[3]

        if token_stdev > 0:
            z_token = (day_tokens - token_mean) / token_stdev
            if abs(z_token) > z_score_threshold:
                anomalies.append({
                    "type": "token_spike" if z_token > 0 else "token_drop",
                    "severity": "critical" if abs(z_token) > 3.0 else "warning",
                    "day": day,
                    "value": day_tokens,
                    "expected": round(token_mean, 2),
                    "z_score": round(z_token, 4),
                    "deviation_percent": round(((day_tokens - token_mean) / max(token_mean, 1)) * 100, 2),
                    "message": f"{day} Token 消耗 {'突增' if z_token > 0 else '骤降'}: "
                               f"{day_tokens} (预期 {round(token_mean, 2)}, "
                               f"Z={round(z_token, 2)}, "
                               f"偏差 {round(((day_tokens - token_mean) / max(token_mean, 1)) * 100, 2)}%)",
                })

        if req_stdev > 0:
            z_req = (day_requests - req_mean) / req_stdev
            if abs(z_req) > z_score_threshold:
                anomalies.append({
                    "type": "request_spike" if z_req > 0 else "request_drop",
                    "severity": "critical" if abs(z_req) > 3.0 else "warning",
                    "day": day,
                    "value": day_requests,
                    "expected": round(req_mean, 2),
                    "z_score": round(z_req, 4),
                    "deviation_percent": round(((day_requests - req_mean) / max(req_mean, 1)) * 100, 2),
                    "message": f"{day} 请求量 {'突增' if z_req > 0 else '骤降'}: "
                               f"{day_requests} (预期 {round(req_mean, 2)}, Z={round(z_req, 2)})",
                })

        # 单日错误率异常
        if day_requests > 0:
            day_err_rate = day_errors / day_requests
            if day_err_rate > 0.1 and day_err_rate > err_rate_total * 3:
                anomalies.append({
                    "type": "error_rate_spike",
                    "severity": "critical",
                    "day": day,
                    "value": round(day_err_rate, 4),
                    "expected": round(err_rate_total, 4),
                    "z_score": None,
                    "deviation_percent": round((day_err_rate - err_rate_total) / max(err_rate_total, 0.001) * 100, 2),
                    "message": f"{day} 错误率异常: {day_err_rate:.2%} (基线 {err_rate_total:.2%}, "
                               f"错误数 {day_errors}/{day_requests})",
                })

    # 2. 预算超限检查（来自 F13 状态）
    budget_anomalies = []
    for bs in token_budget_registry.all_status():
        if bs.is_exceeded:
            budget_anomalies.append({
                "type": "budget_exceeded",
                "severity": "critical",
                "rule_name": bs.name,
                "current_usage": bs.current_usage,
                "token_limit": bs.rule.token_limit,
                "usage_ratio": round(bs.usage_ratio, 4),
                "message": f"预算 '{bs.name}' 已超限: {bs.current_usage}/{bs.rule.token_limit} "
                           f"({bs.usage_ratio:.1%})",
            })
        elif bs.is_warning:
            budget_anomalies.append({
                "type": "budget_warning",
                "severity": "warning",
                "rule_name": bs.name,
                "current_usage": bs.current_usage,
                "token_limit": bs.rule.token_limit,
                "usage_ratio": round(bs.usage_ratio, 4),
                "message": f"预算 '{bs.name}' 接近上限: {bs.current_usage}/{bs.rule.token_limit} "
                           f"({bs.usage_ratio:.1%})",
            })

    all_anomalies = anomalies + budget_anomalies
    # 按严重性排序
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    all_anomalies.sort(key=lambda a: severity_order.get(a.get("severity", "info"), 99))

    return {
        "has_anomaly": len(all_anomalies) > 0,
        "anomaly_count": len(all_anomalies),
        "critical_count": sum(1 for a in all_anomalies if a.get("severity") == "critical"),
        "warning_count": sum(1 for a in all_anomalies if a.get("severity") == "warning"),
        "anomalies": all_anomalies,
        "metrics": {
            "total_days": len(daily_rows),
            "token_mean": round(token_mean, 2),
            "token_stdev": round(token_stdev, 2) if token_stdev else 0,
            "request_mean": round(req_mean, 2),
            "request_stdev": round(req_stdev, 2) if req_stdev else 0,
            "overall_error_rate": round(err_rate_total, 4),
            "z_score_threshold": z_score_threshold,
        },
    }


# ═══════════════════════════════════════════════════
# 4. 预算预警
# ═══════════════════════════════════════════════════

async def create_budget_alert(
    db: AsyncSession,
    rule_name: str,
    alert_level: str = "warning",
    current_usage: int = 0,
    token_limit: int = 0,
    usage_ratio: float = 0.0,
    threshold: float = 0.8,
    agent_name: str | None = None,
    user_id: int | None = None,
    message: str = "",
    detail: dict[str, Any] | None = None,
) -> TokenBudgetAlert | None:
    """创建预算预警记录"""
    try:
        alert = TokenBudgetAlert(
            alert_id=f"alert_{uuid.uuid4().hex[:12]}",
            rule_name=rule_name,
            alert_level=alert_level,
            current_usage=current_usage,
            token_limit=token_limit,
            usage_ratio=usage_ratio,
            threshold=threshold,
            agent_name=agent_name,
            user_id=user_id,
            message=message,
            detail=json.dumps(detail, ensure_ascii=False) if detail else None,
            is_resolved=False,
            created_at=datetime.utcnow(),
        )
        db.add(alert)
        await db.commit()
        await db.refresh(alert)
        logger.info("预算预警已创建: [%s] %s - %s", alert_level, rule_name, message[:80])
        return alert
    except Exception as e:
        logger.error("创建预算预警失败: %s", e)
        await db.rollback()
        return None


async def check_and_create_alerts(
    db: AsyncSession,
) -> list[dict[str, Any]]:
    """
    检查所有预算规则状态，自动创建预警记录。
    返回本次新创建的预警列表。
    """
    new_alerts: list[dict[str, Any]] = []
    now = datetime.utcnow()

    # 获取最近 N 分钟内的同类预警（避免重复告警）
    recent_sql = """
        SELECT rule_name, alert_level FROM token_budget_alert
        WHERE created_at >= :since_dt
        GROUP BY rule_name, alert_level
    """
    since_dt = now - timedelta(minutes=30)
    recent_result = await db.execute(text(recent_sql), {"since_dt": since_dt})
    recent_alerts = {(row[0], row[1]) for row in recent_result.fetchall()}

    for bs in token_budget_registry.all_status():
        # 检查超限
        if bs.is_exceeded and (bs.name, "critical") not in recent_alerts:
            alert = await create_budget_alert(
                db=db,
                rule_name=bs.name,
                alert_level="critical",
                current_usage=bs.current_usage,
                token_limit=bs.rule.token_limit,
                usage_ratio=bs.usage_ratio,
                threshold=bs.rule.warn_threshold,
                message=f"预算 '{bs.name}' 已超限: {bs.current_usage}/{bs.rule.token_limit} ({bs.usage_ratio:.1%})",
                detail={"remaining_tokens": bs.remaining_tokens, "degrade_strategy": bs.rule.degrade_strategy.value},
            )
            if alert:
                new_alerts.append(alert.to_dict())

        # 检查预警阈值
        elif bs.is_warning and (bs.name, "warning") not in recent_alerts:
            alert = await create_budget_alert(
                db=db,
                rule_name=bs.name,
                alert_level="warning",
                current_usage=bs.current_usage,
                token_limit=bs.rule.token_limit,
                usage_ratio=bs.usage_ratio,
                threshold=bs.rule.warn_threshold,
                message=f"预算 '{bs.name}' 使用率 {bs.usage_ratio:.1%} 已达预警阈值",
                detail={"remaining_tokens": bs.remaining_tokens, "degrade_strategy": bs.rule.degrade_strategy.value},
            )
            if alert:
                new_alerts.append(alert.to_dict())

    return new_alerts


async def get_alerts(
    db: AsyncSession,
    period: str | None = None,
    start: str | None = None,
    end: str | None = None,
    alert_level: str | None = None,
    rule_name: str | None = None,
    unresolved_only: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """获取预算预警记录"""
    start_dt, end_dt = _parse_time_range(period, start, end)

    params: dict[str, Any] = {}
    where_clauses = ["1=1"]

    if start_dt:
        where_clauses.append("created_at >= :start_dt")
        params["start_dt"] = start_dt
    if end_dt:
        where_clauses.append("created_at <= :end_dt")
        params["end_dt"] = end_dt
    if alert_level:
        where_clauses.append("alert_level = :alert_level")
        params["alert_level"] = alert_level
    if rule_name:
        where_clauses.append("rule_name = :rule_name")
        params["rule_name"] = rule_name
    if unresolved_only:
        where_clauses.append("is_resolved = 0")

    where_sql = " AND ".join(where_clauses)

    # 查询总数
    count_sql = f"SELECT COUNT(*) FROM token_budget_alert WHERE {where_sql}"
    count_result = await db.execute(text(count_sql), params)
    total = count_result.scalar() or 0

    # 查询列表
    sql = f"""
        SELECT *
        FROM token_budget_alert
        WHERE {where_sql}
        ORDER BY created_at DESC
        LIMIT :limit_val OFFSET :offset_val
    """
    params["limit_val"] = limit
    params["offset_val"] = offset

    result = await db.execute(text(sql), params)
    rows = result.fetchall()

    alerts = []
    for row in rows:
        alert = TokenBudgetAlert(
            id=row[0],
            alert_id=row[1],
            rule_name=row[2],
            alert_level=row[3],
            current_usage=row[4],
            token_limit=row[5],
            usage_ratio=row[6],
            threshold=row[7],
            agent_name=row[8],
            user_id=row[9],
            message=row[10],
            detail=row[11],
            is_resolved=row[12],
            resolved_at=row[13],
            created_at=row[14],
        )
        alerts.append(alert.to_dict())

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": alerts,
    }


async def resolve_alert(
    db: AsyncSession,
    alert_id: str,
) -> bool:
    """将预警标记为已解决"""
    try:
        sql = "UPDATE token_budget_alert SET is_resolved = 1, resolved_at = :now WHERE alert_id = :alert_id"
        result = await db.execute(text(sql), {"alert_id": alert_id, "now": datetime.utcnow()})
        await db.commit()
        return result.rowcount > 0
    except Exception as e:
        logger.error("解决预警失败: %s", e)
        await db.rollback()
        return False


# ═══════════════════════════════════════════════════
# 5. 消费记录写入
# ═══════════════════════════════════════════════════

async def record_consumption(
    db: AsyncSession,
    agent_name: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    total_tokens: int | None = None,
    user_id: int | None = None,
    session_id: str | None = None,
    rule_name: str | None = None,
    is_truncated: bool = False,
    is_downgraded: bool = False,
    degrade_strategy: str | None = None,
    estimated_cost: float = 0.0,
    cost_per_token: float = 0.0,
    model_name: str | None = None,
    operation: str | None = None,
    status: str = "success",
    metadata_json: str | None = None,
) -> TokenConsumptionRecord | None:
    """记录一条 Token 消费记录"""
    try:
        if total_tokens is None:
            total_tokens = prompt_tokens + completion_tokens

        record = TokenConsumptionRecord(
            record_id=f"tcr_{uuid.uuid4().hex[:12]}",
            agent_name=agent_name,
            user_id=user_id,
            session_id=session_id,
            rule_name=rule_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            is_truncated=is_truncated,
            is_downgraded=is_downgraded,
            degrade_strategy=degrade_strategy,
            estimated_cost=estimated_cost,
            cost_per_token=cost_per_token,
            model_name=model_name,
            operation=operation,
            status=status,
            metadata_json=metadata_json,
            created_at=datetime.utcnow(),
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record
    except Exception as e:
        logger.error("记录 Token 消费失败: %s", e)
        await db.rollback()
        return None
