"""
三蛋蛋 · 企业匹配引擎 MCP 工具 — AI数智名片
==========================================
将外部 1000万 企业库匹配能力 (transphee.com) 暴露为 MCP 工具，
供 Hermes Agent / 数字员工直接调用。

工具:
    transphee_health   — 探活 (无需票)
    transphee_quota    — 今日配额使用情况 (100次/天)
    transphee_match    — 输入卖家信息 → 潜在买家名单 (按 rank 排序)
    transphee_match_page — 翻页查询 (配合 cname 去重)

注册到 ~/.hermes/config.yaml:
    transphee-match-engine:
      command: python
      args: ["D:\\AI数智名片\\mcp_servers\\transphee_mcp_server.py"]
      timeout: 60
"""
import os
import sys
from typing import Optional

# 让 SDK 可被 import (MCP server 在 mcp_servers/, SDK 在 backend/app/services/, 需要 backend 在 path 上)
BACKEND_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from mcp.server.fastmcp import FastMCP
from app.services.transphee_client import (
    TranspheeClient,
    TranspheeAuthError,
    TranspheeError,
    TranspheeQuotaExceeded,
    get_transphee_client,
)

mcp = FastMCP("三蛋蛋 · 企业匹配引擎")


def _client() -> TranspheeClient:
    return get_transphee_client()


def _err(e: Exception) -> dict:
    if isinstance(e, TranspheeQuotaExceeded):
        return {"success": False, "error": f"配额耗尽: {e}", "retry_after": getattr(e, "retry_after", None)}
    if isinstance(e, TranspheeAuthError):
        return {"success": False, "error": f"认证失败: {e}", "hint": "检查 .env 中 TRANSHEE_APP_ID / TRANSHEE_APP_SECRET"}
    if isinstance(e, TranspheeError):
        return {"success": False, "error": str(e), "status_code": getattr(e, "status_code", 0),
                "error_id": getattr(e, "error_id", "")}
    return {"success": False, "error": str(e)}


@mcp.tool()
def transphee_health() -> dict:
    """三蛋蛋企业匹配引擎探活 (无需票)。返回上游服务状态。"""
    try:
        return _client().health()
    except Exception as e:
        return _err(e)


@mcp.tool()
def transphee_quota() -> dict:
    """三蛋蛋企业匹配引擎今日配额使用情况 (100次/天, 北京时间0点重置)。"""
    try:
        return {"success": True, "data": _client().quota_status()}
    except Exception as e:
        return _err(e)


@mcp.tool()
def transphee_match(
    product: str = "",
    business: str = "",
    typical_customers: str = "",
    company_name: str = "",
    province: Optional[list[str]] = None,
    page: int = 1,
    max_retries: int = 2,
) -> dict:
    """
    输入卖家信息 → 返回潜在买家名单 (三蛋蛋 1000万 企业库)。

    参数:
        product: 你卖什么 (product/business/typical_customers 至少填一个)
        business: 主营业务
        typical_customers: 现在的典型客户是谁
        company_name: 本公司名 (填了会把自己从结果里排除)
        province: 限定省份, 如 ["江苏省"]
        page: 页码 1..500, 默认 1 (第1页可能含置顶联盟企业, 最多30条)
        max_retries: 对频率限制/5xx 的重试次数 (默认2)

    返回 data.list[] 按 rank 排序 (别按 score 重排), 每条含:
        rank/cname/province/city/url/industryType/industryMain/product/business/typical_customers/score/source/pinned/contacts[]
    注意: contacts 恒为脱敏形态 (name_masked/position/email_masked/phone=null),
    跨页去重请按 cname 而不是 id。

    配额: 每天 100 次查询, 配额用完返回 429 提示。
    """
    try:
        data = _client().match_customers(
            company_name=company_name,
            product=product,
            business=business,
            typical_customers=typical_customers,
            page=page,
            filters={"province": province} if province else None,
            max_retries=max_retries,
        )
        return {
            "success": True,
            "data": {
                "list": data.get("list", []),
                "total": data.get("total", 0),
                "total_is_lower_bound": data.get("total_is_lower_bound", False),
                "page": data.get("page", page),
                "whitelist_shown": data.get("whitelist_shown", 0),
                "degraded": data.get("degraded", False),
                "buyer_profile": data.get("buyer_profile", {}),
            },
            "hint": "按 rank 排序展示; 跨页按 cname 去重; total 为下限时显示 '10000+'",
        }
    except TranspheeQuotaExceeded as e:
        return _err(e)
    except Exception as e:
        return _err(e)


@mcp.tool()
def transphee_match_page(
    product: str = "",
    business: str = "",
    typical_customers: str = "",
    company_name: str = "",
    province: Optional[list[str]] = None,
    page: int = 2,
    max_retries: int = 2,
) -> dict:
    """
    翻页查询潜在买家 (page ≥ 2 时每页恒 20 条, 无置顶)。

    用法: 先 transphee_match(page=1) 拿首页 + total, 再按需翻页;
    跨页去重按 cname (同公司置顶/被检索时 id 不一样)。
    分页最深 500 页; 每天 100 次查询配额。
    """
    try:
        data = _client().match_customers(
            company_name=company_name,
            product=product,
            business=business,
            typical_customers=typical_customers,
            page=page,
            filters={"province": province} if province else None,
            max_retries=max_retries,
        )
        return {
            "success": True,
            "data": {
                "list": data.get("list", []),
                "total": data.get("total", 0),
                "total_is_lower_bound": data.get("total_is_lower_bound", False),
                "page": data.get("page", page),
            },
        }
    except TranspheeQuotaExceeded as e:
        return _err(e)
    except Exception as e:
        return _err(e)


if __name__ == "__main__":
    mcp.run(transport="stdio")
