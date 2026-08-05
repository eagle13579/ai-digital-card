"""
三蛋蛋 · 企业匹配引擎 Router — AI数智名片
========================================
将外部 1000万 企业库匹配能力暴露为后端 API，供小程序匹配Tab等调用。

端点:
    GET  /api/transphee/health   — 探活 (无需登录)
    GET  /api/transphee/quota    — 今日配额 (100次/天)
    POST /api/transphee/match    — 输入卖家 → 潜在买家名单 (按 rank 排序)

用法 (小程序 wx.request):
    wx.request({ url: 'https://api.liankebao.top/api/transphee/match', method: 'POST',
        data: { company_name, product, business, typical_customers, page, province: [] },
        header: { 'Authorization': 'Bearer ' + token } })
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.services.transphee_client import (
    TranspheeAuthError,
    TranspheeClient,
    TranspheeError,
    TranspheeQuotaExceeded,
    get_transphee_client,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/transphee", tags=["三蛋蛋匹配引擎"])


# ── 请求模型 ─────────────────────────────────────────────────────────────

class TranspheeMatchRequest(BaseModel):
    """匹配查询请求 (对齐上游 /api/match_customers)"""
    company_name: str = Field(..., description="本公司名 (上游实测必填, 会把自己从结果里排除)")
    product: str = Field("", max_length=500, description="你卖什么")
    business: str = Field("", max_length=500, description="主营业务")
    typical_customers: str = Field("", max_length=500, description="典型客户")
    page: int = Field(1, ge=1, le=500, description="页码 1..500")
    province: Optional[list[str]] = Field(None, description="限定省份, 如 ['江苏省']")

    class Config:
        json_schema_extra = {
            "example": {
                "company_name": "苏州康陪智能科技有限公司",
                "product": "陪护型养老服务机器人",
                "business": "研发生产销售养老服务机器人整机及软件平台",
                "typical_customers": "养老院、护理院、康复医院",
                "page": 1,
                "province": ["江苏省"],
            }
        }


# ── 业务端点 ─────────────────────────────────────────────────────────────

@router.get("/health")
async def transphee_health():
    """三蛋蛋企业匹配引擎探活 (无需登录, 不耗配额)"""
    client = get_transphee_client()
    try:
        return client.health()
    except Exception as e:
        logger.error("transphee health failed: %s", e)
        raise HTTPException(status_code=503, detail=f"三蛋蛋服务不可达: {e}")


@router.get("/quota")
async def transphee_quota():
    """今日配额使用情况 (100次/天, 北京时间0点重置)"""
    client = get_transphee_client()
    try:
        return {"success": True, "data": client.quota_status()}
    except Exception as e:
        logger.error("transphee quota failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/match")
async def transphee_match(req: TranspheeMatchRequest):
    """
    输入卖家信息 → 返回潜在买家名单 (三蛋蛋 1000万 企业库)。
    - product/business/typical_customers 至少填一个
    - 返回 list 按 rank 排序 (别按 score 重排)
    - contacts 恒为脱敏形态; 跨页去重按 cname
    - 每天 100 次查询配额
    """
    client = get_transphee_client()
    try:
        data = client.match_customers(
            company_name=req.company_name,
            product=req.product,
            business=req.business,
            typical_customers=req.typical_customers,
            page=req.page,
            filters={"province": req.province} if req.province else None,
        )
        return {
            "success": True,
            "data": {
                "list": data.get("list", []),
                "total": data.get("total", 0),
                "total_is_lower_bound": data.get("total_is_lower_bound", False),
                "page": data.get("page", req.page),
                "whitelist_shown": data.get("whitelist_shown", 0),
                "degraded": data.get("degraded", False),
                "buyer_profile": data.get("buyer_profile", {}),
            },
            "quota": client.quota_status(),
        }
    except TranspheeQuotaExceeded as e:
        raise HTTPException(status_code=429, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TranspheeAuthError as e:
        logger.error("transphee auth error: %s", e)
        raise HTTPException(status_code=502, detail=f"三蛋蛋认证失败: {e}")
    except TranspheeError as e:
        logger.error("transphee error: status=%s error_id=%s msg=%s",
                     e.status_code, e.error_id, e)
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.exception("transphee match unexpected error")
        raise HTTPException(status_code=500, detail=f"匹配服务异常: {e}")
