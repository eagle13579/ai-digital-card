"""
链客宝 — 高可用仪表盘 API 路由
===============================
提供 HA 仪表盘所需的后端 API 端点。

路由:
    GET  /ha/dashboard          — HA 仪表盘 HTML 页面
    GET  /ha/api/geo-status     — 当前地理区域健康状态 (JSON)
    GET  /ha/api/failover-history — 故障转移历史记录 (JSON)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

logger = logging.getLogger("chainke.ha")

router = APIRouter(tags=["高可用"])

# ── 模板目录 ──────────────────────────────────────────────────────────────
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

# ── 状态文件路径 ──────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
GEO_STATUS_FILE = PROJECT_ROOT / "deploy" / "geo" / "geo-status.json"
FAILOVER_HISTORY_FILE = PROJECT_ROOT / "deploy" / "scripts" / ".failover" / "failover_history.jsonl"


# ===================================================================
# 辅助函数
# ===================================================================

def _load_geo_status() -> dict[str, Any]:
    """加载 GeoDNS 健康检查状态。"""
    if GEO_STATUS_FILE.exists():
        try:
            return json.loads(GEO_STATUS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("加载 geo-status.json 失败: %s", exc)
    # 返回默认状态
    return {
        "timestamp": "",
        "global_healthy": True,
        "regions": {
            "cn-shanghai": {
                "region": "cn-shanghai",
                "provider": "阿里云",
                "healthy": True,
                "pg_healthy": True,
                "redis_healthy": True,
                "api_healthy": True,
                "pg_lag_ms": 0,
                "redis_hit_rate": 0,
                "latency_ms": 0,
                "weight": 100,
                "consecutive_failures": 0,
                "last_checked": "",
            },
            "ap-singapore": {
                "region": "ap-singapore",
                "provider": "AWS",
                "healthy": True,
                "pg_healthy": True,
                "redis_healthy": True,
                "api_healthy": True,
                "pg_lag_ms": 0,
                "redis_hit_rate": 0,
                "latency_ms": 0,
                "weight": 80,
                "consecutive_failures": 0,
                "last_checked": "",
            },
            "us-west": {
                "region": "us-west",
                "provider": "AWS",
                "healthy": True,
                "pg_healthy": True,
                "redis_healthy": True,
                "api_healthy": True,
                "pg_lag_ms": 0,
                "redis_hit_rate": 0,
                "latency_ms": 0,
                "weight": 60,
                "consecutive_failures": 0,
                "last_checked": "",
            },
        },
    }


def _load_failover_history() -> list[dict[str, Any]]:
    """加载故障转移历史记录。"""
    if FAILOVER_HISTORY_FILE.exists():
        try:
            lines = FAILOVER_HISTORY_FILE.read_text(encoding="utf-8").strip().split("\n")
            return [json.loads(line) for line in lines if line.strip()]
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("加载故障转移历史失败: %s", exc)
    return []


# ===================================================================
# 路由
# ===================================================================


@router.get("/ha/dashboard", response_class=HTMLResponse)
async def ha_dashboard():
    """多区域高可用仪表盘 HTML 页面。"""
    html_path = TEMPLATES_DIR / "ha_dashboard.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
    return HTMLResponse(
        content="<h1>高可用仪表盘页面未找到</h1><p>请确认 templates/ha_dashboard.html 存在</p>",
        status_code=404,
    )


@router.get("/ha/api/geo-status")
async def geo_status():
    """返回当前地理区域健康状态 (JSON)。"""
    status = _load_geo_status()
    return JSONResponse(content=status)


@router.get("/ha/api/failover-history")
async def failover_history():
    """返回故障转移历史记录 (JSON)。"""
    history = _load_failover_history()
    return JSONResponse(content=history)


@router.get("/ha/api/health")
async def ha_health():
    """HA 子系统自身的健康检查。"""
    geo = _load_geo_status()
    return JSONResponse(content={
        "status": "ok",
        "service": "chainke-ha",
        "regions_known": list(geo.get("regions", {}).keys()),
        "global_healthy": geo.get("global_healthy", True),
        "has_history": len(_load_failover_history()) > 0,
    })
