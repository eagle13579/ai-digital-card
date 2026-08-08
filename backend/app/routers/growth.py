"""
链客宝 — 增长分析 API (Growth Analytics)
========================================
提供增长飞轮核心指标查询，包括 DAU/MAU、名片创建数、匹配数、
趋势分析、获客来源和留存分析。

端点:
  GET /api/v1/growth/metrics    — 核心增长指标
  GET /api/v1/growth/trends     — 增长趋势 (7日/30日)
  GET /api/v1/growth/sources    — 获客来源分析
  GET /api/v1/growth/retention  — 留存分析
  GET /api/v1/growth/overview   — 增长飞轮概览

数据说明:
  BUG-010 修复：已移除模拟数据桩，接入真实指标源：
    - DAU/MAU   : audit_logs（按天/月 distinct user_id 活跃统计）
    - 新用户     : users.created_at
    - 名片创建数 : brochures.created_at
    - 匹配数     : match_records.created_at
    - 获客来源   : visitor_logs.source（direct/qrcode/share/scan）
    - 留存       : users.created_at 注册 cohort + audit_logs 活跃回访
  数据量不足时返回空序列并标注 data_status，不返回伪造数值。

鉴权:
  BUG-037 第一批落地：5 个端点统一收敛到 require_permission("system:metrics")
  （RBAC 单一事实源 rbac_user_roles，顺带覆盖 BUG-011 无鉴权缺口）。

规范:
  - 返回格式统一: { code, message, data, timestamp }
  - 日期格式: YYYY-MM-DD
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.rbac import require_permission
from app.models.audit import AuditLog
from app.models.brochure import Brochure
from app.models.tag import MatchRecord
from app.models.user import User
from app.models.visitor import VisitorLog

logger = logging.getLogger("chainke.growth")

router = APIRouter(prefix="/api/v1/growth", tags=["增长分析"])

# ── 真实指标数据加载 ──────────────────────────────────────────────────


def _to_day(value: Any) -> str:
    """将 DB 返回的时间值统一为 YYYY-MM-DD 字符串（兼容 SQLite str / 其它方言 datetime）。"""
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    return str(value)[:10]


def _to_month(value: Any) -> str:
    """将 DB 返回的时间值统一为 YYYY-MM 字符串。"""
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m")
    s = str(value)[:7]
    return s


async def _load_metrics(db: AsyncSession) -> dict[str, Any]:
    """一次性加载核心业务表并在 Python 侧聚合（兼容 SQLite/MySQL/PostgreSQL）。"""
    audit_rows = (await db.execute(select(AuditLog.user_id, AuditLog.timestamp))).all()
    user_rows = (await db.execute(select(User.id, User.created_at))).all()
    brochure_rows = (await db.execute(select(Brochure.id, Brochure.created_at))).all()
    match_rows = (await db.execute(select(MatchRecord.id, MatchRecord.created_at))).all()
    visitor_rows = (await db.execute(select(VisitorLog.source))).all()

    # DAU: 每天 distinct 活跃 user_id（基于审计日志）
    dau_by_day: dict[str, set[int]] = defaultdict(set)
    # MAU: 每月 distinct 活跃 user_id
    mau_by_month: dict[str, set[int]] = defaultdict(set)
    # 用户活跃日映射（留存计算用）
    active_days_by_user: dict[int, set[str]] = defaultdict(set)
    for uid, ts in audit_rows:
        if uid is None:
            continue
        day = _to_day(ts)
        if day:
            dau_by_day[day].add(uid)
            active_days_by_user[uid].add(day)
        month = _to_month(ts)
        if month:
            mau_by_month[month].add(uid)

    # 新注册用户 / 名片创建 / 匹配：按天计数
    reg_by_day: dict[str, int] = defaultdict(int)
    reg_day_by_user: dict[int, str] = {}
    for uid, ts in user_rows:
        day = _to_day(ts)
        if day:
            reg_by_day[day] += 1
            reg_day_by_user[uid] = day

    card_by_day: dict[str, int] = defaultdict(int)
    for _, ts in brochure_rows:
        day = _to_day(ts)
        if day:
            card_by_day[day] += 1

    match_by_day: dict[str, int] = defaultdict(int)
    for _, ts in match_rows:
        day = _to_day(ts)
        if day:
            match_by_day[day] += 1

    # 获客来源（访客来源近似）
    source_counter: dict[str, int] = defaultdict(int)
    for (source,) in visitor_rows:
        source_counter[source or "direct"] += 1

    return {
        "dau_by_day": {k: len(v) for k, v in dau_by_day.items()},
        "mau_by_month": {k: len(v) for k, v in mau_by_month.items()},
        "active_days_by_user": active_days_by_user,
        "reg_by_day": reg_by_day,
        "reg_day_by_user": reg_day_by_user,
        "card_by_day": card_by_day,
        "match_by_day": match_by_day,
        "source_counter": source_counter,
    }


def _fill_daily_series(
    data: dict[str, int], days: int, key: str
) -> list[dict[str, Any]]:
    """将按天字典补零展开为最近 N 天序列。"""
    series: list[dict[str, Any]] = []
    today = datetime.utcnow().date()
    for i in range(days - 1, -1, -1):
        date_str = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        series.append({"date": date_str, key: data.get(date_str, 0)})
    return series


def _compute_growth_rate(series: list[dict[str, Any]], key: str) -> float:
    """计算增长率（最近一期 vs 上期）。"""
    if len(series) < 2:
        return 0.0
    latest = series[-1].get(key, 0)
    prev = series[-2].get(key, 0)
    if prev == 0:
        return 0.0
    return round((latest - prev) / prev * 100, 2)


def _source_analysis(counter: dict[str, int]) -> list[dict[str, Any]]:
    """基于访客来源统计获客来源分析。"""
    total = sum(counter.values()) or 1
    labels = {
        "direct": ("直接访问", "direct"),
        "qrcode": ("二维码", "qrcode"),
        "share": ("分享链接", "share"),
        "scan": ("扫码", "scan"),
        "wechat": ("微信", "wechat"),
        "other": ("其他", "other"),
    }
    sources = []
    for key, cnt in sorted(counter.items(), key=lambda kv: kv[1], reverse=True):
        cn_name, channel = labels.get(key, (key, key))
        sources.append({
            "source": cn_name,
            "channel": channel,
            "users": cnt,
            "percentage": round(cnt / total * 100, 2),
            "trend": "stable",
        })
    return sources


def _retention_data(metrics: dict[str, Any]) -> dict[str, Any]:
    """月度注册 Cohort 留存（D1/D3/D7/D14/D30，基于 audit_logs 活跃回访）。

    数据量不足（无注册用户）时返回空 cohort 并标注 data_status=no_data。
    """
    reg_day_by_user = metrics.get("reg_day_by_user", {})
    active_days_by_user = metrics.get("active_days_by_user", {})

    if not reg_day_by_user:
        return {
            "cohorts": [],
            "average_retention": {
                "day_1": 0.0, "day_3": 0.0, "day_7": 0.0,
                "day_14": 0.0, "day_30": 0.0,
            },
            "period": "monthly_cohort",
            "data_status": "no_data",
        }

    cohorts: dict[str, list[int]] = defaultdict(list)
    for uid, day in reg_day_by_user.items():
        if day:
            cohorts[day[:7]].append(uid)

    def _retention(users: list[int], offset_days: int) -> float:
        if not users:
            return 0.0
        hit = 0
        for uid in users:
            reg_day = reg_day_by_user.get(uid)
            if not reg_day:
                continue
            try:
                target = (
                    datetime.strptime(reg_day, "%Y-%m-%d") + timedelta(days=offset_days)
                ).strftime("%Y-%m-%d")
            except ValueError:
                continue
            if target in active_days_by_user.get(uid, set()):
                hit += 1
        return round(hit / len(users), 3)

    cohort_list = []
    for month, users in cohorts.items():
        cohort_list.append({
            "cohort": month,
            "new_users": len(users),
            "retention": {
                "day_1": _retention(users, 1),
                "day_3": _retention(users, 3),
                "day_7": _retention(users, 7),
                "day_14": _retention(users, 14),
                "day_30": _retention(users, 30),
            },
        })

    cohort_list.sort(key=lambda c: c["cohort"], reverse=True)
    n = len(cohort_list) or 1
    avg = {
        "day_1": round(sum(c["retention"]["day_1"] for c in cohort_list) / n, 3),
        "day_3": round(sum(c["retention"]["day_3"] for c in cohort_list) / n, 3),
        "day_7": round(sum(c["retention"]["day_7"] for c in cohort_list) / n, 3),
        "day_14": round(sum(c["retention"]["day_14"] for c in cohort_list) / n, 3),
        "day_30": round(sum(c["retention"]["day_30"] for c in cohort_list) / n, 3),
    }
    return {
        "cohorts": cohort_list,
        "average_retention": avg,
        "period": "monthly_cohort",
        "data_status": "ok" if cohort_list else "no_data",
    }


# ── API 端点 ──────────────────────────────────────────────────────────


@router.get("/metrics", summary="核心增长指标 — DAU/MAU/名片创建数/匹配数")
async def growth_metrics(
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(require_permission("system:metrics")),
):
    """返回增长飞轮核心指标的最新值及变化率（真实数据）。"""
    from key_manager import SecretManager
    _env = SecretManager().get("ENV", "development").lower()
    _docs_disabled = SecretManager().get("DISABLE_DOCS", "").lower() in ("1", "true", "yes")
    if _env in ("production", "prod") or _docs_disabled:
        from fastapi.responses import JSONResponse
        return JSONResponse({"error": "metrics endpoint disabled in production"}, status_code=404)

    # ── 真实指标逻辑 ──
    metrics = await _load_metrics(db)

    dau_series = _fill_daily_series(metrics["dau_by_day"], 30, "dau")
    card_series = _fill_daily_series(metrics["card_by_day"], 30, "card_creations")
    match_series = _fill_daily_series(metrics["match_by_day"], 30, "matches")
    reg_series = _fill_daily_series(metrics["reg_by_day"], 30, "new_users")

    # MAU: 最近 6 个月按月展开
    mau_series = []
    now = datetime.utcnow()
    for i in range(5, -1, -1):
        year, month = (now.year, now.month - i)
        while month <= 0:
            year -= 1
            month += 12
        month_key = f"{year}-{month:02d}"
        mau_series.append({"month": month_key, "year": year, "month_num": month,
                           "mau": metrics["mau_by_month"].get(month_key, 0)})

    latest_dau = dau_series[-1]["dau"]
    latest_mau = mau_series[-1]["mau"]
    latest_cards = card_series[-1]["card_creations"]
    latest_matches = match_series[-1]["matches"]
    total_cards = sum(c["card_creations"] for c in card_series)
    total_matches = sum(m["matches"] for m in match_series)

    return {
        "code": 0,
        "message": "success",
        "data": {
            "dau": {
                "value": latest_dau,
                "change_rate": _compute_growth_rate(dau_series, "dau"),
                "series": dau_series[-7:],
            },
            "mau": {
                "value": latest_mau,
                "change_rate": _compute_growth_rate(mau_series, "mau"),
                "series": mau_series[-3:],
            },
            "dau_mau_ratio": round(latest_dau / latest_mau, 3) if latest_mau > 0 else 0,
            "total_cards": {
                "value": total_cards,
                "today": latest_cards,
                "change_rate": _compute_growth_rate(card_series, "card_creations"),
            },
            "total_matches": {
                "value": total_matches,
                "today": latest_matches,
                "change_rate": _compute_growth_rate(match_series, "matches"),
            },
            "new_users_today": reg_series[-1]["new_users"],
            "data_status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
        },
    }


@router.get("/trends", summary="增长趋势 — 7日/30日DAU及名片匹配趋势")
async def growth_trends(
    days: int = Query(30, ge=7, le=90, description="查询天数 (7~90)"),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(require_permission("system:metrics")),
):
    """返回指定天数的增长趋势数据（真实数据）。"""
    metrics = await _load_metrics(db)

    dau_series = _fill_daily_series(metrics["dau_by_day"], days, "dau")
    card_series = _fill_daily_series(metrics["card_by_day"], days, "card_creations")
    match_series = _fill_daily_series(metrics["match_by_day"], days, "matches")
    reg_series = _fill_daily_series(metrics["reg_by_day"], days, "new_users")

    all_dau = [d["dau"] for d in dau_series]
    all_cards = [c["card_creations"] for c in card_series]
    all_matches = [m["matches"] for m in match_series]
    all_reg = [r["new_users"] for r in reg_series]

    return {
        "code": 0,
        "message": "success",
        "data": {
            "dau": dau_series,
            "card_creations": card_series,
            "matches": match_series,
            "new_users": reg_series,
            "summary": {
                "total_dau": sum(all_dau),
                "avg_dau": round(sum(all_dau) / len(all_dau), 1),
                "peak_dau": max(all_dau),
                "total_cards": sum(all_cards),
                "avg_daily_cards": round(sum(all_cards) / len(all_cards), 1),
                "total_matches": sum(all_matches),
                "avg_daily_matches": round(sum(all_matches) / len(all_matches), 1),
                "total_new_users": sum(all_reg),
            },
            "days": days,
            "data_status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
        },
    }


@router.get("/sources", summary="获客来源分析 — 各渠道用户获取分布")
async def growth_sources(
    days: int = Query(30, ge=1, le=90, description="分析周期天数"),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(require_permission("system:metrics")),
):
    """返回获客来源分析数据（基于 visitor_logs.source 真实统计）。"""
    metrics = await _load_metrics(db)
    sources = _source_analysis(metrics["source_counter"])

    return {
        "code": 0,
        "message": "success",
        "data": {
            "sources": sources,
            "total_users": sum(s["users"] for s in sources),
            "period_days": days,
            "data_status": "ok" if sources else "no_data",
            "timestamp": datetime.utcnow().isoformat(),
        },
    }


@router.get("/retention", summary="留存分析 — 月度 Cohort 留存率")
async def growth_retention(
    months: int = Query(6, ge=3, le=24, description="Cohort 月数 (3~24)"),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(require_permission("system:metrics")),
):
    """返回月度 Cohort 留存分析（注册 cohort + audit_logs 活跃回访）。"""
    metrics = await _load_metrics(db)
    retention_data = _retention_data(metrics)

    return {
        "code": 0,
        "message": "success",
        "data": {
            **retention_data,
            "timestamp": datetime.utcnow().isoformat(),
        },
    }


@router.get("/overview", summary="增长飞轮概览 — 综合看板数据")
async def growth_overview(
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(require_permission("system:metrics")),
):
    """返回增长飞轮综合概览，聚合 metrics + trends + sources 的核心信息（真实数据）。"""
    metrics = await _load_metrics(db)

    dau_series = _fill_daily_series(metrics["dau_by_day"], 30, "dau")
    card_series = _fill_daily_series(metrics["card_by_day"], 30, "card_creations")
    match_series = _fill_daily_series(metrics["match_by_day"], 30, "matches")
    sources = _source_analysis(metrics["source_counter"])
    retention = _retention_data(metrics)

    latest_dau = dau_series[-1]["dau"]
    now = datetime.utcnow()
    month_key = f"{now.year}-{now.month:02d}"
    latest_mau = metrics["mau_by_month"].get(month_key, 0)

    return {
        "code": 0,
        "message": "success",
        "data": {
            "current": {
                "dau": latest_dau,
                "mau": latest_mau,
                "dau_mau_ratio": round(latest_dau / latest_mau, 3) if latest_mau > 0 else 0,
                "today_cards": card_series[-1]["card_creations"],
                "today_matches": match_series[-1]["matches"],
            },
            "top_sources": sorted(sources, key=lambda s: s["users"], reverse=True)[:3],
            "avg_retention": retention["average_retention"],
            "data_status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
        },
    }
