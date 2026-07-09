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

数据说明:
  当前使用模拟数据返回。TODO: 接入真实数据源 (如 ClickHouse / 数仓)。

规范:
  - 返回格式统一: { code, message, data, timestamp }
  - 日期格式: YYYY-MM-DD
"""

from __future__ import annotations

import logging
import random
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Query

logger = logging.getLogger("chainke.growth")

router = APIRouter(prefix="/api/v1/growth", tags=["增长分析"])

# ── 模拟数据生成 ──────────────────────────────────────────────────────


def _mock_dau_series(days: int = 30) -> list[dict[str, Any]]:
    """生成过去 N 天的模拟 DAU 数据。"""
    base = 1200
    series = []
    for i in range(days - 1, -1, -1):
        date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
        dow = (datetime.utcnow() - timedelta(days=i)).weekday()
        multiplier = 1.1 if dow < 5 else 0.85
        dau = int(base * multiplier + (i % 7) * 30)
        series.append({"date": date, "dau": dau})
    return series


def _mock_mau_series(months: int = 6) -> list[dict[str, Any]]:
    """生成过去 N 个月的模拟 MAU 数据。"""
    series = []
    now = datetime.utcnow()
    for i in range(months - 1, -1, -1):
        month = (now.month - i) % 12 or 12
        year = now.year - (1 if (now.month - i) <= 0 else 0)
        mau = int(5000 + (i * 200) + random.randint(-200, 200))
        series.append({
            "month": f"{year}-{month:02d}",
            "year": year,
            "month_num": month,
            "mau": mau,
        })
    return series


def _mock_card_creation_series(days: int = 30) -> list[dict[str, Any]]:
    """生成过去 N 天的模拟名片创建数。"""
    series = []
    for i in range(days - 1, -1, -1):
        date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
        count = int(80 + random.randint(-20, 40) + (i % 5) * 10)
        series.append({"date": date, "card_creations": count})
    return series


def _mock_match_series(days: int = 30) -> list[dict[str, Any]]:
    """生成过去 N 天的模拟匹配数。"""
    series = []
    for i in range(days - 1, -1, -1):
        date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
        count = int(200 + random.randint(-40, 60) + (i % 4) * 15)
        series.append({"date": date, "matches": count})
    return series


def _mock_source_analysis() -> list[dict[str, Any]]:
    """生成模拟获客来源分析。"""
    return [
        {"source": "自然搜索", "channel": "organic", "users": 3200, "percentage": 32.0, "trend": "up"},
        {"source": "直接访问", "channel": "direct", "users": 2100, "percentage": 21.0, "trend": "stable"},
        {"source": "社交媒体", "channel": "social", "users": 1800, "percentage": 18.0, "trend": "up"},
        {"source": "推荐邀请", "channel": "referral", "users": 1500, "percentage": 15.0, "trend": "up"},
        {"source": "付费广告", "channel": "paid", "users": 800, "percentage": 8.0, "trend": "down"},
        {"source": "邮件营销", "channel": "email", "users": 400, "percentage": 4.0, "trend": "stable"},
        {"source": "其他", "channel": "other", "users": 200, "percentage": 2.0, "trend": "stable"},
    ]


def _mock_retention_data() -> dict[str, Any]:
    """生成模拟留存分析数据。"""
    cohorts = []
    now = datetime.utcnow()
    for i in range(6):
        month = (now.month - i) % 12 or 12
        year = now.year - (1 if (now.month - i) <= 0 else 0)
        cohort_id = f"{year}-{month:02d}"
        # 模拟留存率: D1 ~ D30 递减
        base_users = random.randint(800, 1500)
        day1 = round(random.uniform(0.35, 0.55), 3)
        day3 = round(day1 * random.uniform(0.55, 0.75), 3)
        day7 = round(day3 * random.uniform(0.50, 0.70), 3)
        day14 = round(day7 * random.uniform(0.45, 0.60), 3)
        day30 = round(day14 * random.uniform(0.30, 0.50), 3)
        cohorts.append({
            "cohort": cohort_id,
            "new_users": base_users,
            "retention": {
                "day_1": day1,
                "day_3": day3,
                "day_7": day7,
                "day_14": day14,
                "day_30": day30,
            },
        })
    return {
        "cohorts": sorted(cohorts, key=lambda c: c["cohort"], reverse=True),
        "average_retention": {
            "day_1": round(sum(c["retention"]["day_1"] for c in cohorts) / len(cohorts), 3),
            "day_3": round(sum(c["retention"]["day_3"] for c in cohorts) / len(cohorts), 3),
            "day_7": round(sum(c["retention"]["day_7"] for c in cohorts) / len(cohorts), 3),
            "day_14": round(sum(c["retention"]["day_14"] for c in cohorts) / len(cohorts), 3),
            "day_30": round(sum(c["retention"]["day_30"] for c in cohorts) / len(cohorts), 3),
        },
        "period": "monthly_cohort",
    }


def _compute_growth_rate(series: list[dict[str, Any]], key: str) -> float:
    """计算增长率（最近一期 vs 上期）。"""
    if len(series) < 2:
        return 0.0
    latest = series[-1].get(key, 0)
    prev = series[-2].get(key, 0)
    if prev == 0:
        return 0.0
    return round((latest - prev) / prev * 100, 2)


# ── API 端点 ──────────────────────────────────────────────────────────


@router.get("/metrics", summary="核心增长指标 — DAU/MAU/名片创建数/匹配数")
async def growth_metrics():
    """返回增长飞轮核心指标的最新值及变化率。
    """
    import os
    _env = os.getenv("ENV", "development").lower()
    _docs_disabled = os.getenv("DISABLE_DOCS", "").lower() in ("1", "true", "yes")
    if _env in ("production", "prod") or _docs_disabled:
        from fastapi.responses import JSONResponse
        return JSONResponse({"error": "metrics endpoint disabled in production"}, status_code=404)

    # ── 正式指标逻辑 ──
    dau_series = _mock_dau_series(30)
    mau_series = _mock_mau_series(6)
    card_series = _mock_card_creation_series(30)
    match_series = _mock_match_series(30)

    latest_dau = dau_series[-1]["dau"]
    latest_mau = mau_series[-1]["mau"]
    latest_cards = card_series[-1]["card_creations"]
    latest_matches = match_series[-1]["matches"]

    # 累计值
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
            "timestamp": datetime.utcnow().isoformat(),
        },
    }


@router.get("/trends", summary="增长趋势 — 7日/30日DAU及名片匹配趋势")
async def growth_trends(
    days: int = Query(30, ge=7, le=90, description="查询天数 (7~90)"),
):
    """返回指定天数的增长趋势数据。

    包括:
      - dau: 日活跃用户趋势
      - card_creations: 每日名片创建数
      - matches: 每日匹配数
      - summary: 汇总统计（总值、日均值、峰值）
    """
    dau_series = _mock_dau_series(days)
    card_series = _mock_card_creation_series(days)
    match_series = _mock_match_series(days)

    all_dau = [d["dau"] for d in dau_series]
    all_cards = [c["card_creations"] for c in card_series]
    all_matches = [m["matches"] for m in match_series]

    return {
        "code": 0,
        "message": "success",
        "data": {
            "dau": dau_series,
            "card_creations": card_series,
            "matches": match_series,
            "summary": {
                "total_dau": sum(all_dau),
                "avg_dau": round(sum(all_dau) / len(all_dau), 1),
                "peak_dau": max(all_dau),
                "total_cards": sum(all_cards),
                "avg_daily_cards": round(sum(all_cards) / len(all_cards), 1),
                "total_matches": sum(all_matches),
                "avg_daily_matches": round(sum(all_matches) / len(all_matches), 1),
            },
            "days": days,
            "timestamp": datetime.utcnow().isoformat(),
        },
    }


@router.get("/sources", summary="获客来源分析 — 各渠道用户获取分布")
async def growth_sources(
    days: int = Query(30, ge=1, le=90, description="分析周期天数"),
):
    """返回获客来源分析数据。

    渠道包括:
      - organic: 自然搜索
      - direct: 直接访问
      - social: 社交媒体
      - referral: 推荐邀请
      - paid: 付费广告
      - email: 邮件营销
      - other: 其他
    """
    sources = _mock_source_analysis()

    return {
        "code": 0,
        "message": "success",
        "data": {
            "sources": sources,
            "total_users": sum(s["users"] for s in sources),
            "period_days": days,
            "timestamp": datetime.utcnow().isoformat(),
        },
    }


@router.get("/retention", summary="留存分析 — 月度 Cohort 留存率")
async def growth_retention(
    months: int = Query(6, ge=3, le=24, description="Cohort 月数 (3~24)"),
):
    """返回月度 Cohort 留存分析。

    留存率指标:
      - day_1: 次日留存
      - day_3: 3日留存
      - day_7: 7日留存
      - day_14: 14日留存
      - day_30: 30日留存

    同时返回所有 Cohort 的平均留存率。
    """
    retention_data = _mock_retention_data()

    return {
        "code": 0,
        "message": "success",
        "data": {
            **retention_data,
            "timestamp": datetime.utcnow().isoformat(),
        },
    }


@router.get("/overview", summary="增长飞轮概览 — 综合看板数据")
async def growth_overview():
    """返回增长飞轮综合概览，聚合 metrics + trends + sources 的核心信息。"""
    dau_series = _mock_dau_series(30)
    mau_series = _mock_mau_series(6)
    card_series = _mock_card_creation_series(30)
    match_series = _mock_match_series(30)
    sources = _mock_source_analysis()
    retention = _mock_retention_data()

    latest_dau = dau_series[-1]["dau"]
    latest_mau = mau_series[-1]["mau"]

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
            "timestamp": datetime.utcnow().isoformat(),
        },
    }
