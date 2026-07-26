"""crawlee_router.py — Crawlee 爬虫服务 API 路由

POST   /api/crawlee/scrape     — 单名片爬取
POST   /api/crawlee/batch      — 批量爬取
GET    /api/crawlee/health     — 健康检查

依赖:
  - backend.crawlee_service: crawl_service (全局单例)
"""
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.crawlee_service import crawl_service, CardResult, health_check as svc_health

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/crawlee", tags=["Crawlee爬虫服务"])


# ── 请求/响应模型 ──────────────────────────────────────────────


class ScrapeRequest(BaseModel):
    """单名片爬取请求。"""
    url: str = Field(..., description="目标网页 URL（需包含 http(s):// 前缀）", min_length=1)


class BatchScrapeRequest(BaseModel):
    """批量爬取请求。"""
    urls: list[str] = Field(..., description="URL 列表，至少 1 个，最多 100 个", min_length=1, max_length=100)


class ScrapeResponse(BaseModel):
    """单名片爬取响应。"""
    code: int = 0
    message: str = "success"
    data: dict | None = None


class BatchScrapeResponse(BaseModel):
    """批量爬取响应。"""
    code: int = 0
    message: str = "success"
    data: list[dict] = Field(default_factory=list)
    total: int = 0
    success_count: int = 0
    error_count: int = 0


class HealthResponse(BaseModel):
    """健康检查响应。"""
    code: int = 0
    message: str = "success"
    data: dict | None = None


# ── 端点 ──────────────────────────────────────────────────────


@router.post("/scrape", response_model=ScrapeResponse, summary="单名片爬取")
async def api_scrape_card(request: ScrapeRequest):
    """爬取并提取单张名片信息。

    输入一个名片网页 URL，返回结构化名片数据（姓名、公司、职位、电话等）。
    自动检测 JSON-LD / hCard / Meta 标签 / 正则提取等多种格式。
    """
    url = request.url.strip()
    if not url.startswith(("http://", "https://")):
        raise HTTPException(
            status_code=400,
            detail="无效的 URL，请提供以 http:// 或 https:// 开头的地址",
        )

    try:
        result: CardResult = await crawl_service.scrape_card(url)

        if result.status == "error":
            return ScrapeResponse(
                code=1,
                message=f"爬取失败: {result.error_message}",
                data=result.to_dict(),
            )

        return ScrapeResponse(
            code=0,
            message="success",
            data=result.to_dict(),
        )

    except Exception as exc:
        logger.exception("单名片爬取异常: %s", url)
        raise HTTPException(
            status_code=502,
            detail=f"爬取服务异常: {exc}",
        )


@router.post("/batch", response_model=BatchScrapeResponse, summary="批量爬取")
async def api_batch_scrape(request: BatchScrapeRequest):
    """批量爬取多张名片信息。

    并发爬取多个名片网页，返回结构化名片数据列表。
    最多支持 100 个 URL。
    """
    urls = [u.strip() for u in request.urls if u.strip().startswith(("http://", "https://"))]
    if not urls:
        raise HTTPException(
            status_code=400,
            detail="未提供有效的 URL（需要 http:// 或 https:// 前缀）",
        )

    try:
        results: list[CardResult] = await crawl_service.batch_scrape(urls)

        data = [r.to_dict() for r in results]
        success_count = sum(1 for r in results if r.status == "success")
        error_count = sum(1 for r in results if r.status == "error")

        return BatchScrapeResponse(
            code=0,
            message="success",
            data=data,
            total=len(results),
            success_count=success_count,
            error_count=error_count,
        )

    except Exception as exc:
        logger.exception("批量爬取异常")
        raise HTTPException(
            status_code=502,
            detail=f"批量爬取服务异常: {exc}",
        )


@router.get("/health", response_model=HealthResponse, summary="健康检查")
async def api_health():
    """爬虫服务健康检查。

    返回 crawlee_service 的运行状态、组件可用性和统计信息。
    """
    try:
        health_data = await crawl_service.health_check()
        return HealthResponse(code=0, message="success", data=health_data)
    except Exception as exc:
        logger.exception("健康检查异常")
        return HealthResponse(
            code=1,
            message=f"健康检查异常: {exc}",
            data={"status": "error", "error": str(exc)},
        )
