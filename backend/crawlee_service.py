r"""
crawlee_service.py — Crawlee 爬虫服务模块 (AI数字名片)

基于 baize_libs.crawlee_service (Crawlee Essence Python 移植版) 构建。
提供:
  - RichCardCrawler:   名片URL采集爬虫, 使用 CrawlerEngine + RequestQueue + SessionPool
  - CardExtractor:     从页面提取名片结构化数据
  - 异步接口:          scrape_card(), batch_scrape(), health_check()

依赖:
  - baize_libs.crawlee_service 包（位于 D:\向海容的知识库\...\baize_libs\crawlee_service\）
  - httpx / aiohttp 用于 HTTP 请求
  - lxml / beautifulsoup4 用于 HTML 解析

用法:
    from crawlee_service import crawl_service
    result = await crawl_service.scrape_card("https://example.com/card")
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import sys
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional
from urllib.parse import urljoin, urlparse

# ── baize_libs 路径注入 ────────────────────────────────────────
_BAZE_LIBS_DIR = Path(
    r"D:\向海容的知识库\wiki\wiki\记忆宫殿\L3兵器库\代码资产\baize_libs"
)
if _BAZE_LIBS_DIR.exists() and str(_BAZE_LIBS_DIR) not in sys.path:
    sys.path.insert(0, str(_BAZE_LIBS_DIR))

logger = logging.getLogger(__name__)

# ── 尝试导入 baize_libs.crawlee_service 组件 ──────────────────
_HAS_CRAWLEE = False
try:
    from baize_libs.crawlee_service import (          # type: ignore[import-untyped]
        CrawlerEngine,
        Request,
        RequestQueue,
        Session,
        SessionPool,
        ErrorTracker,
        MemoryStorage,
        Dataset,
        KeyValueStore,
        Router,
    )

    _HAS_CRAWLEE = True
    logger.info("baize_libs.crawlee_service 加载成功")
except ImportError as exc:
    logger.warning("baize_libs.crawlee_service 不可用，降级为独立模式: %s", exc)
    # 独立模式下定义最小占位类，保证模块可导入
    class CrawlerEngine:   # type: ignore[no-redef]
        async def run(self, urls, handler, concurrency=5): return {"processed": 0, "failed": 0, "total": 0, "elapsed_secs": 0}
    class RequestQueue:    pass
    class SessionPool:     pass
    class ErrorTracker:    pass
    class MemoryStorage:   pass
    class Router:          pass

# ═══════════════════════════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════════════════════════


@dataclass
class CardContact:
    """名片联系人信息。"""
    name: str = ""
    title: str = ""
    company: str = ""
    department: str = ""
    email: str = ""
    phone: str = ""
    mobile: str = ""
    wechat: str = ""
    website: str = ""
    address: str = ""
    social_links: list[str] = field(default_factory=list)


@dataclass
class CardResult:
    """名片爬取结果。"""
    url: str = ""
    status: str = "pending"           # pending | success | error
    error_message: str = ""
    contact: CardContact = field(default_factory=CardContact)
    raw_html_snippet: str = ""
    meta: dict = field(default_factory=dict)
    extracted_at: str = ""
    source: str = "http"               # http | playwright
    request_id: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["extracted_at"] = d["extracted_at"] or datetime.utcnow().isoformat()
        return d


# ═══════════════════════════════════════════════════════════════
# CardExtractor — 从 HTML 中提取名片结构化数据
# ═══════════════════════════════════════════════════════════════


class CardExtractor:
    """从 HTML 页面提取名片结构化数据。

    支持多种名片格式检测:
      - vCard / hCard 微格式
      - JSON-LD (schema.org/Person, schema.org/Organization)
      - Meta 标签 (open graph, twitter card)
      - 常见中文名片 HTML 模式 (类名包含 card/contact/profile)
      - 纯文本启发式提取 (手机号/邮箱/姓名等 regex 模式)
    """

    # ── 正则模式 ──────────────────────────────────────────────
    _PHONE_PATTERN = re.compile(
        r'(?:(?:\+?86)?[\s-]?)?1[3-9]\d{9}(?!\d)'
    )
    _EMAIL_PATTERN = re.compile(
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    )
    _WECHAT_PATTERN = re.compile(
        r'(?:微信号?|微信|WeChat|wechat)[：:\s]*([a-zA-Z0-9_\-]{4,30})',
        re.IGNORECASE,
    )
    _PHONE_LANDLINE = re.compile(
        r'(?:0\d{2,3}[\s-]?)?\d{7,8}(?:[\s-]?\d{1,4})?'
    )
    # 中文姓名启发式 (2-4 个汉字, 排除常见非姓名词)
    _CHINESE_NAME = re.compile(
        r'(?:姓名|名字|称呼|Name)[：:\s]*([\u4e00-\u9fa5]{2,4})'
    )
    _TITLE_PATTERN = re.compile(
        r'(?:职位|职务|职称|头衔|Title|Position)[：:\s]*([\u4e00-\u9fa5\w\-]{2,30})'
    )
    _COMPANY_PATTERN = re.compile(
        r'(?:公司|企业|单位|组织|Company|Organization)[：:\s]*([\u4e00-\u9fa5\w\-]{2,60})'
    )

    # ── 名片相关 CSS 类/ID 关键词 ─────────────────────────────
    _CARD_KEYWORDS = [
        "card", "vcard", "hcard", "business-card", "contact",
        "profile", "名片", "联系方式", "contact-info", "personal-info",
    ]

    def __init__(self, use_ai_extraction: bool = False):
        self.use_ai_extraction = use_ai_extraction
        self._stats = {"extracted": 0, "failed": 0}

    async def extract(self, url: str, html: str, meta: Optional[dict] = None) -> CardResult:
        """从 HTML 页面中提取名片信息。"""
        result = CardResult(
            url=url,
            status="success",
            extracted_at=datetime.utcnow().isoformat(),
            meta=meta or {},
        )

        if not html or len(html.strip()) < 50:
            result.status = "error"
            result.error_message = "HTML 内容为空或过短"
            self._stats["failed"] += 1
            return result

        contact = CardContact()

        try:
            # 策略 1: 尝试结构化数据提取
            extracted_schema = self._extract_json_ld(html)
            if extracted_schema:
                self._merge_contact(contact, extracted_schema)

            # 策略 2: 尝试 vCard / hCard 微格式
            extracted_hcard = self._extract_hcard(html)
            if extracted_hcard:
                self._merge_contact(contact, extracted_hcard)

            # 策略 3: 尝试 Meta / OG 标签
            extracted_meta = self._extract_meta_tags(html)
            if extracted_meta:
                self._merge_contact(contact, extracted_meta)

            # 策略 4: 正则提取 (兜底)
            extracted_regex = self._extract_regex(html)
            if extracted_regex:
                self._merge_contact(contact, extracted_regex)

            # 策略 5: 启发式名片区域检测
            if not any([contact.name, contact.phone, contact.email]):
                extracted_heuristic = self._extract_heuristic(html)
                if extracted_heuristic:
                    self._merge_contact(contact, extracted_heuristic)

            result.contact = contact
            result.raw_html_snippet = html[:500] if len(html) > 500 else html

            # 检查是否至少提取到一些信息
            has_data = any([
                contact.name, contact.phone, contact.mobile,
                contact.email, contact.company,
            ])
            if not has_data:
                result.meta["extraction_confidence"] = "low"
                result.meta["note"] = "未能提取到明确的名片字段"
            else:
                result.meta["extraction_confidence"] = "medium"
                if contact.name and contact.phone:
                    result.meta["extraction_confidence"] = "high"

            self._stats["extracted"] += 1

        except Exception as exc:
            logger.exception("提取失败: %s", url)
            result.status = "error"
            result.error_message = f"提取异常: {exc}"
            self._stats["failed"] += 1

        return result

    # ── JSON-LD 提取 ──────────────────────────────────────────

    def _extract_json_ld(self, html: str) -> Optional[dict]:
        """从 JSON-LD script 标签提取结构化数据。"""
        contact: dict[str, str] = {}
        pattern = re.compile(
            r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            re.DOTALL | re.IGNORECASE,
        )
        for match in pattern.finditer(html):
            try:
                data = json.loads(match.group(1).strip())
                if not isinstance(data, dict):
                    continue
                # 展开 @graph
                items = [data]
                if "@graph" in data:
                    items = data["@graph"]
                for item in (items if isinstance(items, list) else [items]):
                    if not isinstance(item, dict):
                        continue
                    item_type = item.get("@type", "")
                    if "Person" in item_type:
                        contact["name"] = item.get("name", "")
                        contact["email"] = item.get("email", "")
                        contact["telephone"] = item.get("telephone", "")
                        contact["jobTitle"] = item.get("jobTitle", "")
                        if "worksFor" in item and isinstance(item["worksFor"], dict):
                            contact["company"] = item["worksFor"].get("name", "")
                        if "address" in item and isinstance(item["address"], dict):
                            contact["address"] = item["address"].get("streetAddress", "")
                            if item["address"].get("addressLocality"):
                                contact["address"] += f" {item['address']['addressLocality']}"
                    elif "Organization" in item_type:
                        if not contact.get("company"):
                            contact["company"] = item.get("name", "")
                        if not contact.get("email"):
                            contact["email"] = item.get("email", "")
                        if not contact.get("telephone"):
                            contact["telephone"] = item.get("telephone", "")
                        contact["url"] = item.get("url", "")
            except (json.JSONDecodeError, AttributeError):
                continue
        return self._normalize_contact(contact) if any(contact.values()) else None

    # ── hCard 微格式提取 ──────────────────────────────────────

    def _extract_hcard(self, html: str) -> Optional[dict]:
        """从 hCard 微格式 HTML 提取联系人信息。"""
        contact: dict[str, str] = {}
        # 简单 hCard 类名匹配
        class_patterns = {
            "fn": "name",
            "n": "name",
            "org": "company",
            "title": "title",
            "email": "email",
            "tel": "phone",
            "adr": "address",
            "url": "website",
            "photo": "photo",
        }
        for cls, field_name in class_patterns.items():
            # 匹配 <.* class="... vcard ..."> 等模式中的字段
            patterns = [
                re.compile(
                    rf'<[^>]*class=["\'][^"\']*{cls}[^"\']*["\'][^>]*>'
                    rf'\s*(.*?)\s*</',
                    re.DOTALL | re.IGNORECASE,
                ),
                re.compile(
                    rf'class=["\'][^"\']*{cls}[^"\']*["\']\s*>\s*(.*?)\s*<',
                    re.DOTALL | re.IGNORECASE,
                ),
            ]
            for pat in patterns:
                m = pat.search(html)
                if m:
                    val = re.sub(r'<[^>]+>', '', m.group(1)).strip()
                    if val and not contact.get(field_name):
                        contact[field_name] = val
                        break
        return self._normalize_contact(contact) if any(contact.values()) else None

    # ── Meta / OG 标签提取 ────────────────────────────────────

    def _extract_meta_tags(self, html: str) -> Optional[dict]:
        """从 Open Graph / Twitter Card / Meta 标签提取信息。"""
        contact: dict[str, str] = {}
        meta_map = {
            "og:title": "name",
            "twitter:title": "name",
            "og:description": "description",
            "twitter:description": "description",
            "og:email": "email",
            "og:phone_number": "phone",
        }
        # <meta property="..." content="...">
        for prop in re.finditer(
            r'<meta\s+(?:property|name)=["\']([^"\']+)["\']\s+content=["\']([^"\']*)["\']',
            html, re.IGNORECASE,
        ):
            pname = prop.group(1).lower()
            value = prop.group(2).strip()
            target = meta_map.get(pname)
            if target and value and not contact.get(target):
                contact[target] = value
        return self._normalize_contact(contact) if any(contact.values()) else None

    # ── 正则提取（兜底）───────────────────────────────────────

    def _extract_regex(self, html: str) -> Optional[dict]:
        """使用正则模式提取常见名片字段（降级兜底）。"""
        contact: dict[str, str] = {}
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'\s+', ' ', text).strip()

        # 姓名
        name_m = self._CHINESE_NAME.search(text)
        if name_m:
            contact["name"] = name_m.group(1).strip()

        # 职位
        title_m = self._TITLE_PATTERN.search(text)
        if title_m:
            contact["title"] = title_m.group(1).strip()

        # 公司
        company_m = self._COMPANY_PATTERN.search(text)
        if company_m:
            contact["company"] = company_m.group(1).strip()

        # 手机号
        phones = self._PHONE_PATTERN.findall(text)
        if phones:
            contact["mobile"] = phones[0]

        # 座机
        if not contact.get("phone"):
            landlines = self._PHONE_LANDLINE.findall(text)
            if landlines:
                contact["phone"] = landlines[0]

        # 邮箱
        emails = self._EMAIL_PATTERN.findall(text)
        if emails:
            contact["email"] = emails[0]

        # 微信
        wechat_m = self._WECHAT_PATTERN.search(text)
        if wechat_m:
            contact["wechat"] = wechat_m.group(1).strip()

        # 网址
        url_pattern = re.compile(
            r'https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=%]+',
        )
        urls = url_pattern.findall(text)
        if urls:
            contact["website"] = urls[0]

        return self._normalize_contact(contact) if any(contact.values()) else None

    # ── 启发式名片区域检测 ────────────────────────────────────

    def _extract_heuristic(self, html: str) -> Optional[dict]:
        """检测常见名片布局区域（卡片容器内的文本）。"""
        contact: dict[str, str] = {}

        # 尝试匹配已知的名片容器
        for keyword in self._CARD_KEYWORDS:
            patterns = [
                re.compile(
                    rf'<div[^>]*class=["\'][^"\']*{keyword}[^"\']*["\'][^>]*>'
                    rf'(.*?)</div>',
                    re.DOTALL | re.IGNORECASE,
                ),
                re.compile(
                    rf'<section[^>]*class=["\'][^"\']*{keyword}[^"\']*["\'][^>]*>'
                    rf'(.*?)</section>',
                    re.DOTALL | re.IGNORECASE,
                ),
            ]
            for pat in patterns:
                m = pat.search(html)
                if m:
                    card_html = m.group(1)
                    card_text = re.sub(r'<[^>]+>', ' ', card_html)
                    card_text = re.sub(r'\s+', ' ', card_text).strip()
                    if card_text:
                        # 从卡片区域内提取字段
                        phones = self._PHONE_PATTERN.findall(card_text)
                        if phones and not contact.get("mobile"):
                            contact["mobile"] = phones[0]
                        emails = self._EMAIL_PATTERN.findall(card_text)
                        if emails and not contact.get("email"):
                            contact["email"] = emails[0]
                        # 第一行通常是姓名
                        lines = [l.strip() for l in card_text.split('\n') if l.strip()]
                        if lines and not contact.get("name"):
                            first_line = lines[0]
                            # 如果第一行是2-4个汉字, 则视为姓名
                            if re.match(r'^[\u4e00-\u9fa5]{2,4}$', first_line):
                                contact["name"] = first_line
                        break
        return self._normalize_contact(contact) if any(contact.values()) else None

    # ── 辅助方法 ──────────────────────────────────────────────

    def _normalize_contact(self, raw: dict) -> dict:
        """标准化联系人字段映射到 CardContact 字段。"""
        mapping = {
            "name": ["name", "fn", "fullname", "姓名"],
            "title": ["title", "jobTitle", "position", "职位", "职务"],
            "company": ["company", "org", "organization", "worksFor", "公司", "企业"],
            "email": ["email", "e-mail", "mail"],
            "phone": ["phone", "tel", "telephone", "phone_number", "电话"],
            "mobile": ["mobile", "cell", "手机"],
            "wechat": ["wechat", "微信", "WeChat"],
            "website": ["website", "url", "site", "网址"],
            "address": ["address", "adr", "location", "地址"],
        }
        normalized: dict[str, str] = {}
        for target_field, aliases in mapping.items():
            for alias in aliases:
                val = raw.get(alias, raw.get(alias.lower(), ""))
                if val:
                    normalized[target_field] = val.strip()
                    break
        return normalized

    def _merge_contact(self, target: CardContact, source: dict):
        """将提取的字段合并到 CardContact。"""
        for field_name in ("name", "title", "company", "department",
                           "email", "phone", "mobile", "wechat",
                           "website", "address"):
            val = source.get(field_name, "")
            if val and not getattr(target, field_name):
                setattr(target, field_name, val)

    def get_stats(self) -> dict:
        return {**self._stats}


# ═══════════════════════════════════════════════════════════════
# RichCardCrawler — 名片 URL 采集爬虫
# ═══════════════════════════════════════════════════════════════


class RichCardCrawler:
    """名片 URL 采集爬虫。

    使用 CrawlerEngine + RequestQueue + SessionPool 构建生产级爬虫。

    特性:
      - 基于 baize_libs.crawlee_service 的三阶段爬虫循环
      - RequestQueue 去重 (SHA256 uniqueKey)
      - SessionPool 会话管理 + domain cooldown
      - ErrorTracker 错误聚合 (LCS 合并)
      - MemoryStorage 持久化存储 (Dataset + KeyValueStore)
      - 自动降级: 支持 httpx 和 playwright 两种引擎
      - 可插拔提取器: 默认 CardExtractor
    """

    def __init__(
        self,
        storage_dir: str = "",
        use_playwright: bool = False,
        concurrency: int = 5,
        max_retries: int = 3,
        request_timeout: int = 30,
        user_agent: str = "",
    ):
        self.concurrency = concurrency
        self.max_retries = max_retries
        self.request_timeout = request_timeout
        self.use_playwright = use_playwright

        # 持久化存储
        if not storage_dir:
            storage_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..", "data", "crawlee_storage",
            )
        self.storage_dir = storage_dir

        # Crawlee 核心组件
        self.engine = CrawlerEngine()
        self.request_queue = RequestQueue()
        self.session_pool = SessionPool(max_pool_size=50)
        self.error_tracker = ErrorTracker()
        self.storage = MemoryStorage(
            local_data_directory=os.path.abspath(storage_dir),
            persist_storage=True,
        )

        # 数据集和键值存储
        self._dataset: Optional[Dataset] = None
        self._kv_store: Optional[KeyValueStore] = None

        # 提取器
        self.extractor = CardExtractor()

        # HTTP 客户端会话
        self._http_session: Optional[Any] = None
        self._playwright_context: Optional[Any] = None

        # 爬虫状态
        self._running = False
        self._stats: dict[str, Any] = {
            "total_requests": 0,
            "successful": 0,
            "failed": 0,
            "started_at": "",
            "elapsed": 0,
        }

        # User-Agent
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        )

    # ── 生命周期 ──────────────────────────────────────────────

    async def _ensure_http_session(self):
        """确保 HTTP 客户端可用。"""
        if self._http_session is not None:
            return
        try:
            import httpx
            self._http_session = httpx.AsyncClient(
                timeout=httpx.Timeout(self.request_timeout),
                follow_redirects=True,
                headers={"User-Agent": self.user_agent},
            )
        except ImportError:
            try:
                import aiohttp
                self._http_session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=self.request_timeout),
                    headers={"User-Agent": self.user_agent},
                )
            except ImportError:
                logger.error("需要 httpx 或 aiohttp 库")

    async def _ensure_playwright(self):
        """确保 Playwright 可用。"""
        if self._playwright_context is not None:
            return
        if not self.use_playwright:
            return
        try:
            from playwright.async_api import async_playwright
            p = await async_playwright().start()
            browser = await p.chromium.launch(headless=True)
            self._playwright_context = await browser.new_context(
                user_agent=self.user_agent,
                viewport={"width": 1280, "height": 800},
            )
        except ImportError:
            logger.warning("playwright 未安装，降级为 httpx 模式")
            self.use_playwright = False
        except Exception as exc:
            logger.warning("Playwright 启动失败，降级为 httpx 模式: %s", exc)
            self.use_playwright = False

    async def _get_dataset(self) -> Dataset:
        """获取 Dataset 实例。"""
        if self._dataset is None:
            self._dataset = self.storage.open_dataset("card_results")
        return self._dataset

    async def _get_kv_store(self) -> KeyValueStore:
        """获取 KeyValueStore 实例。"""
        if self._kv_store is None:
            self._kv_store = self.storage.open_kv_store("crawler_meta")
        return self._kv_store

    async def close(self):
        """关闭所有资源。"""
        if self._http_session is not None:
            try:
                await self._http_session.aclose()
            except Exception:
                pass
            self._http_session = None
        if self._playwright_context is not None:
            try:
                await self._playwright_context.close()
            except Exception:
                pass
            self._playwright_context = None

    # ── 单 URL 爬取 ───────────────────────────────────────────

    async def fetch_url(self, url: str) -> tuple[str, dict]:
        """获取单个 URL 的 HTML 内容。

        Returns:
            (html_content, meta_dict)
        """
        await self._ensure_http_session()
        meta: dict[str, Any] = {"fetched_at": datetime.utcnow().isoformat()}

        if self.use_playwright:
            await self._ensure_playwright()
            if self._playwright_context:
                try:
                    page = await self._playwright_context.new_page()
                    await page.goto(url, timeout=self.request_timeout * 1000)
                    await page.wait_for_load_state("networkidle")
                    html = await page.content()
                    meta["source"] = "playwright"
                    meta["title"] = await page.title()
                    meta["final_url"] = page.url
                    await page.close()
                    return html, meta
                except Exception as exc:
                    logger.warning("Playwright 抓取失败，降级为 HTTP: %s", exc)

        # HTTP 模式 (httpx / aiohttp)
        try:
            # 尝试 httpx
            if hasattr(self._http_session, "get"):
                resp = await self._http_session.get(url)
                resp.raise_for_status()
                html = resp.text
                meta["source"] = "httpx"
                meta["status_code"] = resp.status_code
                meta["final_url"] = str(resp.url)
                return html, meta
            # 尝试 aiohttp
            elif hasattr(self._http_session, "_connector"):
                async with self._http_session.get(url) as resp:
                    resp.raise_for_status()
                    html = await resp.text()
                    meta["source"] = "aiohttp"
                    meta["status_code"] = resp.status
                    meta["final_url"] = str(resp.url)
                    return html, meta
        except Exception as exc:
            logger.error("HTTP 抓取失败 %s: %s", url, exc)
            raise

        return "", {"error": "No HTTP client available"}

    async def scrape_card(self, url: str) -> CardResult:
        """爬取并提取单张名片信息。"""
        self._stats["total_requests"] += 1

        # 验证 URL
        if not url or not url.startswith(("http://", "https://")):
            return CardResult(
                url=url,
                status="error",
                error_message="无效 URL，需要 http:// 或 https:// 前缀",
                extracted_at=datetime.utcnow().isoformat(),
            )

        # 通过 RequestQueue 去重
        queue_result = await self.request_queue.add_request(url)
        if queue_result.get("was_already_present"):
            logger.info("URL 已在队列中（跳过重复）: %s", url)

        # 生成 request_id
        request_id = hashlib.md5(url.encode()).hexdigest()[:12]

        try:
            # 获取 Session
            domain = urlparse(url).netloc
            session = await self.session_pool.get_session(domain)
            if session is None:
                session = Session(usage_count=0)
                await self.session_pool.add_session(session)

            # 阶段 1: 抓取 HTML
            html, meta = await self.fetch_url(url)
            meta["request_id"] = request_id
            meta["domain"] = domain

            # 阶段 2: 提取名片信息
            result = await self.extractor.extract(url, html, meta)
            result.request_id = request_id
            result.source = meta.get("source", "http")

            # 阶段 3: 持久化存储
            dataset = await self._get_dataset()
            await dataset.push_data(result.to_dict())

            # Session 健康标记
            if result.status == "success":
                session.mark_good()
            else:
                session.mark_bad()
                if session.is_blocked():
                    self.session_pool.retire_session(session)

            # 标记 RequestQueue
            await self.request_queue.mark_handled(queue_result.get("request_id", request_id))

            self._stats["successful"] += 1
            return result

        except Exception as exc:
            logger.exception("名片爬取失败: %s", url)
            self.error_tracker.add(exc, url=url)
            self._stats["failed"] += 1

            return CardResult(
                url=url,
                status="error",
                error_message=f"爬取异常: {exc}",
                extracted_at=datetime.utcnow().isoformat(),
                request_id=request_id,
            )

    async def batch_scrape(self, urls: list[str]) -> list[CardResult]:
        """批量爬取多张名片信息。

        使用 CrawlerEngine 并发控制。
        """
        if not urls:
            return []

        self._stats["started_at"] = datetime.utcnow().isoformat()
        start_time = time.time()

        # 使用 CrawlerEngine 执行批量爬取
        async def handler(request: Request) -> Optional[list[str]]:
            result = await self.scrape_card(request.url)
            return None  # 不产生新 URL

        stats = await self.engine.run(
            urls=urls,
            handler=handler,
            concurrency=self.concurrency,
        )

        self._stats["elapsed"] = time.time() - start_time

        # 从 Dataset 读取结果
        dataset = await self._get_dataset()
        raw_data = dataset.get_data(limit=len(urls))

        results: list[CardResult] = []
        for item in raw_data:
            try:
                card = CardResult(
                    url=item.get("url", ""),
                    status=item.get("status", "success"),
                    error_message=item.get("error_message", ""),
                    extracted_at=item.get("extracted_at", ""),
                    source=item.get("source", "http"),
                    request_id=item.get("request_id", ""),
                )
                if "contact" in item and isinstance(item["contact"], dict):
                    card.contact = CardContact(**item["contact"])
                results.append(card)
            except Exception:
                continue

        return results

    # ── 状态 / 健康检查 ───────────────────────────────────────

    def health_check(self) -> dict:
        """爬虫服务健康检查。"""
        baize_available = _HAS_CRAWLEE

        http_available = False
        playwright_available = False
        try:
            import httpx
            http_available = True
        except ImportError:
            try:
                import aiohttp
                http_available = True
            except ImportError:
                pass

        try:
            import playwright
            playwright_available = True
        except ImportError:
            pass

        # 存储目录
        storage_exists = os.path.isdir(self.storage_dir)

        return {
            "service": "crawlee_service",
            "status": "ok" if (baize_available or http_available) else "degraded",
            "baize_libs_crawlee": baize_available,
            "http_client": http_available,
            "playwright": playwright_available,
            "storage_dir": os.path.abspath(self.storage_dir),
            "storage_exists": storage_exists,
            "concurrency": self.concurrency,
            "engine_stats": {
                "processed": self._stats.get("successful", 0),
                "failed": self._stats.get("failed", 0),
                "total": self._stats.get("total_requests", 0),
                "elapsed": self._stats.get("elapsed", 0),
            },
            "extractor_stats": self.extractor.get_stats(),
            "error_summary": self.error_tracker.get_summary(top_n=3) if hasattr(self.error_tracker, "get_summary") else [],
        }

    def get_stats(self) -> dict:
        return {**self._stats}


# ═══════════════════════════════════════════════════════════════
# 全局单例服务
# ═══════════════════════════════════════════════════════════════

class CrawleeService:
    """爬虫服务外观 (Facade) — 模块级单例入口。"""

    def __init__(self):
        self._crawler: Optional[RichCardCrawler] = None
        self._lock = asyncio.Lock()

    async def _ensure_crawler(self) -> RichCardCrawler:
        if self._crawler is None:
            async with self._lock:
                if self._crawler is None:
                    self._crawler = RichCardCrawler()
        return self._crawler

    async def scrape_card(self, url: str) -> CardResult:
        """爬取单张名片。"""
        crawler = await self._ensure_crawler()
        return await crawler.scrape_card(url)

    async def batch_scrape(self, urls: list[str]) -> list[CardResult]:
        """批量爬取名片。"""
        if not urls:
            return []
        crawler = await self._ensure_crawler()
        return await crawler.batch_scrape(urls)

    async def health_check(self) -> dict:
        """健康检查。"""
        crawler = await self._ensure_crawler()
        return crawler.health_check()

    async def close(self):
        """关闭服务。"""
        if self._crawler is not None:
            await self._crawler.close()


# 全局单例
crawl_service = CrawleeService()


# ═══════════════════════════════════════════════════════════════
# 便捷函数 (可直接导入使用)
# ═══════════════════════════════════════════════════════════════

async def scrape_card(url: str) -> CardResult:
    """便捷函数 — 爬取单张名片。"""
    return await crawl_service.scrape_card(url)


async def batch_scrape(urls: list[str]) -> list[CardResult]:
    """便捷函数 — 批量爬取名片。"""
    return await crawl_service.batch_scrape(urls)


async def health_check() -> dict:
    """便捷函数 — 健康检查。"""
    return await crawl_service.health_check()
