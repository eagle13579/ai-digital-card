"""
名片采集核心引擎 — URL → HTML 获取 → 结构化提取

基于 httpx 异步 HTTP 请求，遵循 Crawlee 的 BasicCrawler 爬虫生命周期模式：
  1. add_requests / enqueue — 添加待爬取 URL
  2. request_handler  — 用户自定义回调，处理每个页面的响应
  3. run             — 执行爬取主循环，自动管理并发与重试
  4. close           — 优雅关闭客户端与连接池

支持自定义请求头、代理、超时、重试策略、最大并发数。
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup, Tag

from app.config import settings

logger = logging.getLogger(__name__)

# ── 公共类型别名 ──────────────────────────────────────────────────────────────

RequestHandler = Callable[["CrawlerResponse"], "Awaitable[Optional[dict[str, Any]]]"]
"""用户自定义页面处理回调签名: async (response) -> extracted_data | None"""

# ── 数据类 ────────────────────────────────────────────────────────────────────


@dataclass
class CrawlerRequest:
    """单个爬取请求的元信息"""

    url: str
    """目标 URL"""
    label: str = ""
    """请求标签（用于区分不同来源 / 页面类型）"""
    retry_count: int = 0
    """当前已重试次数"""
    max_retries: int = 3
    """最大重试次数"""
    priority: int = 0
    """优先级（越大越优先，默认 0）"""
    extra: dict[str, Any] = field(default_factory=dict)
    """附加数据（用户自定义）"""


@dataclass
class CrawlerResponse:
    """单次 HTTP 响应的封装"""

    url: str
    """最终请求 URL（跟随重定向后）"""
    status_code: int
    """HTTP 状态码"""
    html: str
    """页面 HTML 文本"""
    content_type: str
    """响应 Content-Type"""
    request: CrawlerRequest
    """对应的请求元信息"""
    elapsed: float
    """请求耗时（秒）"""
    headers: dict[str, str] = field(default_factory=dict)
    """响应头字典"""

    @property
    def soup(self) -> BeautifulSoup:
        """延迟加载的 BeautifulSoup 解析对象"""
        if not hasattr(self, "_soup"):
            self._soup = BeautifulSoup(self.html, "html.parser")
        return self._soup

    @property
    def text(self) -> str:
        """页面纯文本（去标签）"""
        return self.soup.get_text(separator="\n", strip=True)

    def find(self, selector: str, **kwargs: Any) -> Optional[Tag]:
        """CSS 选择器查找首个匹配元素"""
        return self.soup.find(selector, **kwargs)

    def find_all(self, selector: str, **kwargs: Any) -> list[Tag]:
        """CSS 选择器查找所有匹配元素"""
        return self.soup.find_all(selector, **kwargs)


# ── 名片专用异常 ──────────────────────────────────────────────────────────────


class CardCrawlerError(Exception):
    """名片采集器基础异常"""


class FetchError(CardCrawlerError):
    """HTTP 请求失败"""


class ParseError(CardCrawlerError):
    """HTML 解析失败"""


# ── 名片字段匹配常量 ──────────────────────────────────────────────────────────

_NAME_PATTERN = re.compile(
    r"(?:姓名|名字|name|称呼|先生|女士)[：:\s]*([\u4e00-\u9fa5]{2,4})"
)
_PHONE_PATTERN = re.compile(r"(?:\+86[-\s]?)?1[3-9]\d{9}")
_EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
_WECHAT_PATTERN = re.compile(
    r"(?:微信|wechat|wx|VX|微)[：:\s]*([a-zA-Z0-9_]{4,20})", re.IGNORECASE
)
_TITLE_PATTERN = re.compile(
    r"(?:职位|职务|title|position|role)[：:\s]*(.{2,20})", re.IGNORECASE
)
_COMPANY_PATTERN = re.compile(
    r"(?:公司|企业|单位|company|firm|organization)[：:\s]*(.{2,30})", re.IGNORECASE
)
_QQ_PATTERN = re.compile(r"(?:QQ)[：:\s]*(\d{5,12})")


# ═══════════════════════════════════════════════════════════════════════════════
#  CardCrawler — 名片采集核心引擎
# ═══════════════════════════════════════════════════════════════════════════════


class CardCrawler:
    """名片采集核心引擎

    URL 输入 → 异步 HTTP 获取 → 结构化字段提取

    使用示例::

        from app.ai.crawler.card_crawler import CardCrawler

        async def handler(resp):
            return {"url": resp.url, "title": resp.find("title")}

        crawler = CardCrawler(max_concurrency=10)
        await crawler.add_requests(["https://example.com/card/1"])
        results = await crawler.run(handler)
        await crawler.close()

    Attributes:
        max_requests:      最大请求数上限（默认 50）
        max_concurrency:   最大并发数（默认 5）
        timeout:           单个请求超时秒数（默认 30）
        headers:           默认请求头
        proxy:             代理 URL（如 "http://127.0.0.1:7890"）
        follow_redirects:  是否跟随重定向（默认 True）
        verify_ssl:        是否验证 SSL 证书（默认 True）
    """

    # ── 默认请求头（模拟主流浏览器） ─────────────────────────────────────────
    DEFAULT_HEADERS: dict[str, str] = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;"
            "q=0.9,image/avif,image/webp,*/*;q=0.8"
        ),
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    def __init__(
        self,
        max_requests: int = 50,
        max_concurrency: int = 5,
        timeout: int = 30,
        headers: Optional[dict[str, str]] = None,
        proxy: Optional[str] = None,
        follow_redirects: bool = True,
        verify_ssl: bool = True,
    ) -> None:
        """

        Args:
            max_requests:      最大请求数上限，到达后停止（默认 50）
            max_concurrency:   最大并发 HTTP 连接数（默认 5）
            timeout:           单次请求超时秒数（默认 30）
            headers:           自定义请求头，与默认头合并
            proxy:             代理 URL（如 ``"http://127.0.0.1:7890"``）
            follow_redirects:  是否自动跟随 3xx 重定向（默认 True）
            verify_ssl:        是否验证 SSL 证书（默认 True）
        """
        self.max_requests = max_requests
        self.max_concurrency = max_concurrency
        self.timeout = timeout
        self.follow_redirects = follow_redirects
        self.verify_ssl = verify_ssl

        # 合并请求头（自定义覆盖默认）
        self.headers = dict(self.DEFAULT_HEADERS)
        if headers:
            self.headers.update(headers)

        # 代理设置
        self.proxy = proxy

        # 内部状态
        self._queue: asyncio.PriorityQueue[CrawlerRequest] = asyncio.PriorityQueue()
        self._seen_urls: set[str] = set()
        self._client: Optional[httpx.AsyncClient] = None
        self._total_requests = 0
        self._active_tasks: set[asyncio.Task] = set()
        self._semaphore: Optional[asyncio.Semaphore] = None

        logger.info(
            "CardCrawler initialized | max_requests=%d max_concurrency=%d timeout=%d",
            max_requests,
            max_concurrency,
            timeout,
        )

    # ── 公共 API ─────────────────────────────────────────────────────────────

    async def add_requests(self, urls: list[str], label: str = "") -> int:
        """添加待爬取的 URL 列表到队列

        Args:
            urls:  URL 列表
            label: 页面标签（可选，用于区分不同来源）

        Returns:
            实际入队的 URL 数量（重复 URL 会被去重）
        """
        count = 0
        for url in urls:
            normalized = self._normalize_url(url)
            if not normalized:
                continue
            if normalized in self._seen_urls:
                logger.debug("跳过已存在 URL: %s", normalized)
                continue
            self._seen_urls.add(normalized)
            request = CrawlerRequest(url=normalized, label=label)
            # asyncio.PriorityQueue 以 tuple 形式入队（priority 越小越优先）
            await self._queue.put((request.priority, request))
            count += 1
        logger.debug("入队 %d 个 URL（label=%r）", count, label)
        return count

    async def enqueue(
        self,
        urls: list[str],
        label: str = "",
        *,
        extra: Optional[dict[str, Any]] = None,
    ) -> int:
        """``add_requests`` 的别名，支持附加数据

        Args:
            urls:  URL 列表
            label: 页面标签
            extra: 附加数据字典（存入每个请求的 ``extra`` 字段）

        Returns:
            实际入队数量
        """
        count = 0
        for url in urls:
            normalized = self._normalize_url(url)
            if not normalized:
                continue
            if normalized in self._seen_urls:
                continue
            self._seen_urls.add(normalized)
            request = CrawlerRequest(
                url=normalized,
                label=label,
                extra=extra or {},
            )
            await self._queue.put((request.priority, request))
            count += 1
        return count

    async def run(
        self,
        request_handler: RequestHandler,
    ) -> list[dict[str, Any]]:
        """执行爬取主循环

        Args:
            request_handler: 异步回调函数，签名::

                async def handler(response: CrawlerResponse) -> dict | None

                返回 ``dict`` 表示提取成功，返回 ``None`` 表示跳过。

        Returns:
            所有成功处理的结果列表（request_handler 返回值的非空集合）
        """
        results: list[dict[str, Any]] = []
        self._semaphore = asyncio.Semaphore(self.max_concurrency)

        try:
            self._client = self._build_client()

            while self._total_requests < self.max_requests:
                # 检查队列是否为空
                if self._queue.empty():
                    # 没有待处理任务则退出
                    if not self._active_tasks:
                        break
                    # 有正在运行的任务，等待一个完成
                    done, _ = await asyncio.wait(
                        self._active_tasks, return_when=asyncio.FIRST_COMPLETED
                    )
                    self._active_tasks.difference_update(done)
                    for task in done:
                        result = task.result()
                        if result is not None:
                            results.append(result)
                    continue

                # 从队列取出一个请求
                _, request = await self._queue.get()

                # 控制并发：获取 semaphore 令牌
                await self._semaphore.acquire()

                task = asyncio.create_task(
                    self._process_request(request, request_handler)
                )
                self._active_tasks.add(task)
                task.add_done_callback(
                    lambda t: (
                        self._semaphore.release(),
                        self._active_tasks.discard(t),
                    )
                )

            # 等待所有未完成的任务
            if self._active_tasks:
                done, _ = await asyncio.wait(
                    self._active_tasks, return_when=asyncio.ALL_COMPLETED
                )
                for task in done:
                    result = task.result()
                    if result is not None:
                        results.append(result)

        except Exception:
            logger.exception("爬取主循环异常")
            raise
        finally:
            await self.close()

        logger.info(
            "爬取完成 | 总请求=%d 成功=%d 队列剩余=%d",
            self._total_requests,
            len(results),
            self._queue.qsize(),
        )
        return results

    async def close(self) -> None:
        """关闭异步客户端，释放连接池"""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.debug("CardCrawler 客户端已关闭")

    # ── 内置名片字段提取助手 ─────────────────────────────────────────────────

    @classmethod
    def extract_card_fields(cls, text: str) -> dict[str, Optional[str]]:
        """从文本中提取名片结构化字段

        使用正则表达式从任意文本中提取姓名、电话、邮箱、微信、职位、公司。

        Args:
            text: 原始文本内容（如页面纯文本）

        Returns:
            {
                "name": str | None,
                "phone": str | None,
                "email": str | None,
                "wechat": str | None,
                "title": str | None,
                "company": str | None,
                "qq": str | None,
            }
        """
        result: dict[str, Optional[str]] = {
            "name": None,
            "phone": None,
            "email": None,
            "wechat": None,
            "title": None,
            "company": None,
            "qq": None,
        }

        # 手机号
        phones = _PHONE_PATTERN.findall(text)
        if phones:
            result["phone"] = phones[0]

        # 邮箱
        emails = _EMAIL_PATTERN.findall(text)
        if emails:
            result["email"] = emails[0]

        # 微信
        wx_match = _WECHAT_PATTERN.search(text)
        if wx_match:
            result["wechat"] = wx_match.group(1)

        # QQ
        qq_match = _QQ_PATTERN.search(text)
        if qq_match:
            result["qq"] = qq_match.group(1)

        # 职位
        title_match = _TITLE_PATTERN.search(text)
        if title_match:
            result["title"] = title_match.group(1)

        # 公司
        company_match = _COMPANY_PATTERN.search(text)
        if company_match:
            result["company"] = company_match.group(1)

        # 姓名
        name_match = _NAME_PATTERN.search(text)
        if name_match:
            result["name"] = name_match.group(1)

        # 兜底：姓名启发式 — 找文本开头附近的中文姓名
        if result["name"] is None:
            lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
            for line in lines[:10]:  # 只看前10行
                if re.search(
                    r"(公司|企业|电话|手机|邮箱|地址|职位|微信|传真|网址|www\.|@)", line
                ):
                    continue
                cn_names = re.findall(r"^[\u4e00-\u9fa5]{2,4}$", line)
                if cn_names:
                    result["name"] = cn_names[0]
                    break

        return result

    @classmethod
    def extract_card_fields_from_html(cls, html: str) -> dict[str, Optional[str]]:
        """从 HTML 页面中提取名片字段

        自动获取页面纯文本后调用 ``extract_card_fields``。

        Args:
            html: 页面 HTML 文本

        Returns:
            与 ``extract_card_fields`` 相同的结构
        """
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        return cls.extract_card_fields(text)

    # ── 内部方法 ─────────────────────────────────────────────────────────────

    def _build_client(self) -> httpx.AsyncClient:
        """构造 httpx 异步客户端"""
        limits = httpx.Limits(
            max_keepalive_connections=self.max_concurrency,
            max_connections=self.max_concurrency * 2,
        )
        client_kwargs: dict[str, Any] = {
            "headers": self.headers,
            "timeout": httpx.Timeout(self.timeout),
            "limits": limits,
            "follow_redirects": self.follow_redirects,
            "verify": self.verify_ssl,
        }
        if self.proxy:
            client_kwargs["proxies"] = {"all://": self.proxy}
        return httpx.AsyncClient(**client_kwargs)

    async def _fetch(self, request: CrawlerRequest) -> CrawlerResponse:
        """执行 HTTP 请求，返回封装后的响应

        Args:
            request: 爬取请求

        Returns:
            封装后的响应对象

        Raises:
            FetchError: 所有 HTTP / 网络异常
        """
        if self._client is None:
            raise CardCrawlerError("客户端未初始化，请先调用 run() 或 _build_client()")

        try:
            resp = await self._client.get(request.url)
            resp.raise_for_status()

            content_type = resp.headers.get("content-type", "").split(";")[0].strip()

            # 检查是否为 HTML 内容
            if "text/html" not in content_type and "application/xhtml" not in content_type:
                logger.warning("非 HTML 响应（%s）: %s", content_type, request.url)
                # 仍尝试读取，可能有些标记为 text/plain 的实际是 HTML

            response = CrawlerResponse(
                url=str(resp.url),
                status_code=resp.status_code,
                html=resp.text,
                content_type=content_type,
                request=request,
                elapsed=resp.elapsed.total_seconds(),
                headers=dict(resp.headers),
            )
            return response

        except httpx.TimeoutException as exc:
            raise FetchError(f"请求超时: {request.url}") from exc
        except httpx.HTTPStatusError as exc:
            raise FetchError(
                f"HTTP {exc.response.status_code}: {request.url}"
            ) from exc
        except httpx.RequestError as exc:
            raise FetchError(f"请求失败: {request.url} — {exc}") from exc

    async def _process_request(
        self,
        request: CrawlerRequest,
        handler: RequestHandler,
    ) -> Optional[dict[str, Any]]:
        """处理单个请求（获取 → 回调 → 返回结果）

        自动处理重试逻辑。

        Args:
            request: 待处理的请求
            handler: 用户回调

        Returns:
            回调返回的数据，或 None（跳过/失败）
        """
        self._total_requests += 1
        logger.info("[%d/%d] 正在抓取: %s", self._total_requests, self.max_requests, request.url)

        for attempt in range(request.max_retries + 1):
            try:
                response = await self._fetch(request)
            except FetchError as exc:
                logger.warning(
                    "抓取失败 (attempt %d/%d): %s — %s",
                    attempt + 1,
                    request.max_retries + 1,
                    request.url,
                    exc,
                )
                if attempt < request.max_retries:
                    # 指数退避
                    wait = 2 ** attempt
                    logger.info("等待 %ds 后重试...", wait)
                    await asyncio.sleep(wait)
                    continue
                else:
                    logger.error("放弃抓取（已达最大重试次数）: %s", request.url)
                    return None

            try:
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(response)
                else:
                    result = handler(response)

                if result is not None and not isinstance(result, dict):
                    logger.warning(
                        "request_handler 返回非 dict 类型（%s），已跳过: %s",
                        type(result).__name__,
                        request.url,
                    )
                    return None

                return result

            except Exception as exc:
                logger.exception(
                    "request_handler 处理异常: %s — %s: %s",
                    request.url,
                    type(exc).__name__,
                    exc,
                )
                return None

        return None

    @staticmethod
    def _normalize_url(url: str) -> Optional[str]:
        """规范化 URL，无效时返回 None"""
        url = url.strip()
        if not url:
            return None
        # 补全协议
        if url.startswith("//"):
            url = "https:" + url
        elif not url.startswith(("http://", "https://")):
            url = "https://" + url
        # 去掉片段标识
        try:
            parsed = urlparse(url)
            if not parsed.netloc:
                return None
            return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        except Exception:
            return None

    # ── 上下文管理器支持 ─────────────────────────────────────────────────────

    async def __aenter__(self) -> "CardCrawler":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()


# ═══════════════════════════════════════════════════════════════════════════════
#  快捷单页面提取函数
# ═══════════════════════════════════════════════════════════════════════════════


async def fetch_card_from_url(
    url: str,
    *,
    timeout: int = 30,
    proxy: Optional[str] = None,
    headers: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    """便捷函数：单 URL → 名片字段提取（一键完成）

    适合单页面快速提取场景，内部自动管理客户端生命周期。

    Args:
        url:     目标页面 URL
        timeout: 超时秒数（默认 30）
        proxy:   代理 URL（可选）
        headers: 自定义请求头（可选）

    Returns:
        {
            "url": str,              # 最终请求 URL
            "status_code": int,      # HTTP 状态码
            "title": str | None,     # 页面 <title>
            "html_length": int,      # HTML 长度
            **card_fields,           # extract_card_fields 的全部字段
        }
    """
    async with CardCrawler(max_requests=1, max_concurrency=1, timeout=timeout,
                           proxy=proxy, headers=headers) as crawler:

        async def handler(resp: CrawlerResponse) -> dict[str, Any]:
            card = CardCrawler.extract_card_fields(resp.text)
            return {
                "url": resp.url,
                "status_code": resp.status_code,
                "title": resp.soup.title.string.strip()
                if resp.soup.title and resp.soup.title.string
                else None,
                "html_length": len(resp.html),
                **card,
            }

        await crawler.add_requests([url])
        results = await crawler.run(handler)
        if results:
            return results[0]
        return {
            "url": url,
            "status_code": 0,
            "title": None,
            "html_length": 0,
            "name": None,
            "phone": None,
            "email": None,
            "wechat": None,
            "title": None,
            "company": None,
            "qq": None,
            "error": "抓取失败或未返回结果",
        }


async def batch_fetch_cards(
    urls: list[str],
    *,
    max_concurrency: int = 5,
    timeout: int = 30,
    proxy: Optional[str] = None,
) -> list[dict[str, Any]]:
    """批量名片采集：多个 URL → 名片字段列表

    Args:
        urls:              URL 列表
        max_concurrency:   最大并发数（默认 5）
        timeout:           超时秒数（默认 30）
        proxy:             代理 URL（可选）

    Returns:
        每个 URL 对应一个结果字典（与 ``fetch_card_from_url`` 格式相同）
    """
    async with CardCrawler(
        max_requests=len(urls),
        max_concurrency=max_concurrency,
        timeout=timeout,
        proxy=proxy,
    ) as crawler:

        async def handler(resp: CrawlerResponse) -> dict[str, Any]:
            card = CardCrawler.extract_card_fields(resp.text)
            return {
                "url": resp.url,
                "status_code": resp.status_code,
                "title": resp.soup.title.string.strip()
                if resp.soup.title and resp.soup.title.string
                else None,
                "html_length": len(resp.html),
                **card,
            }

        await crawler.add_requests(urls)
        return await crawler.run(handler)


__all__ = [
    # 核心引擎
    "CardCrawler",
    # 数据类
    "CrawlerRequest",
    "CrawlerResponse",
    # 异常
    "CardCrawlerError",
    "FetchError",
    "ParseError",
    # 快捷函数
    "fetch_card_from_url",
    "batch_fetch_cards",
    # 类型
    "RequestHandler",
]
