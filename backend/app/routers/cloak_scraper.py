"""
CloakBrowser 智能爬虫路由 — 名片客户网站信息采集

POST   /api/mingpian/scrape        — 爬取名片客户的网站（获取企业信息）
GET    /api/mingpian/scrape/health  — 爬虫服务状态
"""
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.cloak_scraper import SmartScraperService, health as scraper_health

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mingpian", tags=["名片爬虫"])

# 全局单例服务实例
_scraper_service: SmartScraperService | None = None


def _get_scraper() -> SmartScraperService:
    """获取/创建爬虫单例。"""
    global _scraper_service
    if _scraper_service is None:
        _scraper_service = SmartScraperService()
    return _scraper_service


# ── 请求/响应模型 ──────────────────────────────────────────────


class ScrapeRequest(BaseModel):
    """爬取请求参数。"""
    url: str = Field(..., description="目标网站 URL（需包含 http(s):// 前缀）")
    selector: str | None = Field(None, description="可选 CSS 选择器，提取指定元素文本")


class ScrapeResponse(BaseModel):
    """爬取结果。"""
    url: str = Field(..., description="爬取的 URL")
    title: str | None = Field(None, description="页面标题")
    content: str = Field("", description="页面纯文本内容")
    extracted: str | None = Field(None, description="选择器匹配的文本（若有）")
    links: list[str] = Field(default_factory=list, description="页面中发现的外部链接")
    meta: dict = Field(default_factory=dict, description="页面元信息")


class HealthResponse(BaseModel):
    """健康检查响应。"""
    service: str = "cloak_scraper"
    cloakbrowser_installed: bool = False
    cloakbrowser_version: str | None = None
    playwright_installed: bool = False


class SmartScrapeRequest(BaseModel):
    """NL命令模式请求: {"text": "帮我爬https://xxx"}"""
    text: str


# ── 端点 ──────────────────────────────────────────────────────


@router.post("/scrape", response_model=ScrapeResponse)
async def scrape(request: ScrapeRequest):
    """爬取名片客户的网站，获取企业信息。

    使用 CloakBrowser（无头浏览器）采集目标网站内容，
    自动降级为 HTTP 请求模式（当 CloakBrowser 未安装时）。
    """
    if not request.url or not request.url.startswith(("http://", "https://")):
        raise HTTPException(
            status_code=400,
            detail="无效的 URL，请提供以 http:// 或 https:// 开头的地址",
        )

    scraper = _get_scraper()
    try:
        result = await scraper.scrape_url(
            url=request.url,
            selector=request.selector,
        )
        return ScrapeResponse(**result)
    except Exception as exc:
        logger.exception("爬取失败: %s", request.url)
        raise HTTPException(
            status_code=502,
            detail=f"爬取失败: {exc}",
        )


@router.get("/scrape/health", response_model=HealthResponse)
async def scrape_health():
    """爬虫服务健康状态 — 检查 CloakBrowser / Playwright 是否已安装。"""
    return HealthResponse(**scraper_health())


# ── 新增: 进化5 全自动策略引擎端点 ──────────────────────────


@router.post("/scrape/smart", summary="NL命令模式 — 自动解析自然语言指令并爬取")
async def scrape_smart(body: SmartScrapeRequest):
    """
    接受自然语言指令，自动解析URL并执行爬取。

    示例请求:
        {"text": "帮我爬https://example.com"}
        {"text": "抓取 https://example.com 的标题"}

    使用 baize_libs.SmartScraper 解析NL并执行。
    """
    from baize_libs import SmartScraper

    smart = SmartScraper()
    result = smart.execute(body.text)

    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("error", "智能解析+爬取失败"))

    return {"status": "ok", "data": result}


@router.get("/scrape/auto-detect", summary="探测指定URL的bot防护级别")
async def auto_detect(url: str = ""):
    """
    探测指定URL的bot检测/防护级别。

    使用 baize_libs.AutoDetect 检测：
    - Cloudflare 防护
    - reCAPTCHA / hCaptcha
    - WAF
    - JS Challenge

    Query参数: ?url=https://example.com
    """
    if not url.strip():
        raise HTTPException(status_code=400, detail="URL不能为空")

    from baize_libs import AutoDetect

    detector = AutoDetect()
    result = detector.detect(url)

    return {"status": "ok", "url": url, "detection": result}
