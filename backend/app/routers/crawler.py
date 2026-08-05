"""名片采集API路由 - 网页名片信息抓取与结构化提取
POST /api/crawler/scrape: 输入URL → 抓取HTML → AI解析 → 返回结构化名片信息
POST /api/crawler/batch: 批量采集多个URL → 返回结果列表

集成AI引擎做后处理:
  - AIExtractor: 正则+NLP提取姓名、电话、邮箱、公司、职位等
  - DeepSeekClient: 可选AI智能摘要（通过 rag_pipeline 模块）
"""

import asyncio
import logging
import re

import httpx
from bs4 import BeautifulSoup
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.ai.extractor import AIExtractor
from app.models.user import User
from app.routers.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/crawler", tags=["名片采集"])

# ── 请求 / 响应模型 ─────────────────────────────────────────────────


class ScrapeRequest(BaseModel):
    """单 URL 采集请求"""
    url: str = Field(..., min_length=1, max_length=2048, description="待采集的网页URL（支持 http/https）")
    use_ai_postprocess: bool = Field(True, description="是否使用 AI 引擎做智能摘要后处理")


class BatchScrapeRequest(BaseModel):
    """批量采集请求"""
    urls: list[str] = Field(..., min_length=1, max_length=50, description="待采集的URL列表（最多50个）")
    concurrency: int = Field(5, ge=1, le=20, description="并发数（默认5，最高20）")
    use_ai_postprocess: bool = Field(True, description="是否使用 AI 引擎做智能摘要后处理")


class ContactInfo(BaseModel):
    """结构化联系方式"""
    name: str | None = Field(None, description="姓名")
    phone: str | None = Field(None, description="手机号")
    email: str | None = Field(None, description="邮箱")
    wechat: str | None = Field(None, description="微信号")
    company: str | None = Field(None, description="公司名称")
    position: str | None = Field(None, description="职位")
    address: str | None = Field(None, description="地址")
    website: str | None = Field(None, description="网站")
    social_links: list[str] = Field(default_factory=list, description="社交媒体链接（LinkedIn/Twitter/微博等）")


class ScrapeResult(BaseModel):
    """单个 URL 的采集结果"""
    url: str = Field(..., description="来源URL")
    title: str = Field("", description="页面标题")
    description: str = Field("", description="页面Meta描述")
    contact: ContactInfo = Field(default_factory=ContactInfo, description="提取的联系方式")
    raw_text: str = Field("", description="页面原始文本（截取前2000字符用于预览）")
    ai_summary: str | None = Field(None, description="AI 引擎后处理摘要")


class ScrapeResponse(BaseModel):
    """单 URL 采集响应"""
    success: bool
    data: ScrapeResult | None = None
    error: str | None = None


class BatchScrapeResponse(BaseModel):
    """批量采集响应"""
    total: int = Field(..., description="总提交数")
    success_count: int = Field(..., description="成功数")
    failed_count: int = Field(..., description="失败数")
    results: list[ScrapeResponse] = Field(default_factory=list, description="每个URL的采集结果")


# ── 核心抓取引擎 ─────────────────────────────────────────────────────


async def _fetch_page(url: str, client: httpx.AsyncClient) -> tuple[str, str, str]:
    """抓取网页内容并解析，返回 (title, description, raw_text)"""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    resp = await client.get(url, headers=headers, timeout=15.0, follow_redirects=True)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")

    # 提取标题
    title = (soup.title.string.strip() if soup.title and soup.title.string else "")

    # 提取 Meta 描述
    description = ""
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content"):
        description = meta_desc["content"].strip()
    if not description:
        meta_og = soup.find("meta", attrs={"property": "og:description"})
        if meta_og and meta_og.get("content"):
            description = meta_og["content"].strip()

    # 提取纯文本（去掉脚本/样式/导航等噪音）
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        tag.decompose()
    raw_text = soup.get_text(separator="\n", strip=True)
    raw_text = re.sub(r"\n{3,}", "\n\n", raw_text)

    return title, description, raw_text[:10000]  # 最多保留前 10000 字符


async def _extract_contact(text: str) -> ContactInfo:
    """使用 AIExtractor 从文本中提取结构化联系方式"""
    extractor = AIExtractor()
    fields = extractor.extract_fields_from_text(text)

    # 补充社交链接提取
    social_links: list[str] = []
    for pat in [
        re.compile(r"https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+"),
        re.compile(r"https?://(?:www\.)?twitter\.com/[a-zA-Z0-9_]+"),
        re.compile(r"https?://(?:www\.)?weibo\.com/[a-zA-Z0-9_/]+"),
    ]:
        for m in pat.finditer(text):
            social_links.append(m.group())

    # 提取网站 URL
    website = fields.get("website")
    if not website:
        url_pat = re.compile(
            r"https?://(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}"
            r"(?:/[a-zA-Z0-9._~:/?#\[\]@!$&'()*+,;=-]*)?"
        )
        urls = url_pat.findall(text)
        if urls:
            website = urls[0]

    return ContactInfo(
        name=fields.get("name"),
        phone=fields.get("phone"),
        email=fields.get("email"),
        wechat=fields.get("wechat"),
        company=fields.get("company_name"),
        position=fields.get("position"),
        address=fields.get("address"),
        website=website,
        social_links=social_links[:5],
    )


async def _ai_postprocess(raw_text: str, url: str) -> str | None:
    """使用 DeepSeek AI 引擎对采集内容做智能摘要后处理"""
    try:
        from app.ai.rag_pipeline import DeepSeekClient

        client = DeepSeekClient()
        prompt = (
            "你是一个名片信息整理助手。请从以下网页文本中提取并整理名片信息"
            "（姓名、公司、职位、联系方式等）。\n\n"
            f"原始文本（来自 {url}）：\n{raw_text[:3000]}\n\n"
            "请输出结构化的中文摘要，包含：\n"
            "1. 姓名\n2. 公司\n3. 职位\n4. 联系方式（电话/邮箱/微信）\n"
            "5. 简介摘要\n\n如果信息不足，如实说明。"
        )
        result = await client.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1024,
        )
        if isinstance(result, dict) and "error" not in result:
            return result.get("content", "")
        return None
    except Exception:
        logger.exception("AI post-processing failed for %s", url)
        return None


async def _scrape_single(url: str, use_ai: bool = True) -> ScrapeResponse:
    """采集单个 URL 的名片信息"""
    try:
        # 补全协议
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        async with httpx.AsyncClient() as client:
            title, description, raw_text = await _fetch_page(url, client)

        # 结构化字段提取
        contact = await _extract_contact(raw_text)

        # AI 后处理（可选）
        ai_summary = None
        if use_ai:
            ai_summary = await _ai_postprocess(raw_text, url)

        return ScrapeResponse(
            success=True,
            data=ScrapeResult(
                url=url,
                title=title,
                description=description,
                contact=contact,
                raw_text=raw_text[:2000],
                ai_summary=ai_summary,
            ),
        )
    except httpx.TimeoutException:
        return ScrapeResponse(success=False, error=f"请求超时: {url}")
    except httpx.HTTPStatusError as e:
        return ScrapeResponse(
            success=False,
            error=f"HTTP错误 {e.response.status_code}: {url}",
        )
    except Exception:
        logger.exception("Error scraping %s", url)
        return ScrapeResponse(success=False, error=f"采集处理异常: {url}")


# ── API 端点 ─────────────────────────────────────────────────────────


@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_card(
    req: ScrapeRequest,
    current_user: User = Depends(get_current_user),
):
    """
    采集指定 URL 的名片信息

    - 支持个人主页、LinkedIn、企业官网、微博等
    - 自动提取姓名、公司、职位、联系方式（正则 + NLP）
    - 可选 AI 引擎后处理（DeepSeek 智能摘要）
    """
    return await _scrape_single(req.url, use_ai=req.use_ai_postprocess)


@router.post("/batch", response_model=BatchScrapeResponse)
async def batch_scrape(
    req: BatchScrapeRequest,
    current_user: User = Depends(get_current_user),
):
    """
    批量采集多个 URL 的名片信息

    - 最多支持 50 个 URL
    - 支持并发控制（默认 5 并发，最高 20）
    - 支持 AI 后处理
    """
    semaphore = asyncio.Semaphore(req.concurrency)

    async def _bounded(url: str) -> ScrapeResponse:
        async with semaphore:
            return await _scrape_single(url, use_ai=req.use_ai_postprocess)

    tasks = [_bounded(url) for url in req.urls]
    results = await asyncio.gather(*tasks)

    success_count = sum(1 for r in results if r.success)
    failed_count = sum(1 for r in results if not r.success)

    return BatchScrapeResponse(
        total=len(req.urls),
        success_count=success_count,
        failed_count=failed_count,
        results=list(results),
    )
