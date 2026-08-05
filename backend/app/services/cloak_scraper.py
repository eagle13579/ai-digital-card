"""
CloakBrowser 智能爬虫服务 — 名片客户网站数据采集

提供:
  - SmartScraperService: 智能爬虫封装，支持 URL 抓取与结构化提取
  - health(): CloakBrowser 安装状态检测
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SmartScraperService:
    """CloakBrowser 智能爬虫服务。

    使用 cloakbrowser 驱动无头浏览器进行网站内容抓取，
    支持自定义 CSS 选择器提取目标信息。
    """

    def __init__(self):
        self._initialized = False
        self._browser = None
        self._playwright = None

    async def _ensure_initialized(self):
        """延迟初始化 CloakBrowser / Playwright 引擎。"""
        if self._initialized:
            return
        try:
            # 延迟导入，避免模块未安装时崩溃
            import cloakbrowser
            from playwright.async_api import async_playwright

            self._playwright = await async_playwright().start()
            # cloackbrowser 的 launch 方法签名取决于实际版本
            self._browser = await cloakbrowser.launch(
                headless=True,
                playwright=self._playwright,
            )
            self._initialized = True
            logger.info("SmartScraperService 初始化完成 (cloakbrowser=%s)", cloakbrowser.__version__)
        except ImportError as exc:
            logger.warning("cloakbrowser 或 playwright 未安装，爬虫降级为 HTTP 模式: %s", exc)
            self._initialized = True  # 标记为已初始化，后续降级
        except Exception as exc:
            logger.error("SmartScraperService 初始化失败: %s", exc)
            raise

    async def scrape_url(
        self,
        url: str,
        selector: Optional[str] = None,
    ) -> dict:
        """爬取目标 URL 并返回页面内容或结构化数据。

        Args:
            url: 目标网站 URL（需包含 scheme，如 https://example.com）
            selector: 可选 CSS 选择器，指定提取目标元素

        Returns:
            dict: {
                "url": str,
                "title": str | None,
                "content": str,          # 页面文本内容
                "extracted": str | None,  # 选择器匹配到的文本（若提供 selector）
                "links": list[str],       # 页面中的链接
                "meta": dict,             # 页面元信息
            }
        """
        await self._ensure_initialized()

        result = {
            "url": url,
            "title": None,
            "content": "",
            "extracted": None,
            "links": [],
            "meta": {},
        }

        # ── CloakBrowser 模式（优先） ──────────────────────────
        if self._browser is not None:
            try:
                page = await self._browser.new_page()
                await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                result["title"] = await page.title()
                result["content"] = await page.evaluate(
                    "() => document.body.innerText"
                ) or ""
                result["meta"] = await page.evaluate(
                    """() => ({
                        description: document.querySelector('meta[name=\"description\"]')?.content || null,
                        keywords: document.querySelector('meta[name=\"keywords\"]')?.content || null,
                        og_title: document.querySelector('meta[property=\"og:title\"]')?.content || null,
                        og_description: document.querySelector('meta[property=\"og:description\"]')?.content || null,
                    })"""
                )
                result["links"] = await page.evaluate(
                    """() => Array.from(document.querySelectorAll('a[href]'))
                        .map(a => a.href)
                        .filter(h => h.startsWith('http'))"""
                ) or []
                if selector:
                    element = await page.query_selector(selector)
                    if element:
                        result["extracted"] = await element.inner_text()
                await page.close()
                logger.info("CloakBrowser 爬取成功: %s (选择器=%s)", url, selector)
                return result
            except Exception as exc:
                logger.warning("CloakBrowser 爬取失败，回退 HTTP: %s", exc)

        # ── HTTP 降级模式（无 CloakBrowser 时使用 httpx） ─────
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                resp = await client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                                  "Chrome/120.0.0.0 Safari/537.36",
                })
                resp.raise_for_status()
                # 简单 HTML 解析提取文本
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, "html.parser")
                result["title"] = soup.title.string.strip() if soup.title else None
                # 移除无用标签
                for tag in soup(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()
                result["content"] = soup.get_text(separator="\n", strip=True)
                result["meta"] = {
                    "description": soup.find("meta", attrs={"name": "description"}) and
                                   soup.find("meta", attrs={"name": "description"}).get("content"),
                    "keywords": soup.find("meta", attrs={"name": "keywords"}) and
                                soup.find("meta", attrs={"name": "keywords"}).get("content"),
                }
                result["links"] = [a.get("href") for a in soup.find_all("a", href=True)
                                   if a.get("href", "").startswith("http")]
                if selector:
                    elem = soup.select_one(selector)
                    if elem:
                        result["extracted"] = elem.get_text(strip=True)
                logger.info("HTTP 降级爬取成功: %s", url)
        except ImportError:
            logger.error("既无 cloakbrowser 也无 httpx/bs4，无法爬取")
            result["content"] = "ERROR: 爬虫依赖未安装 (cloakbrowser/httpx/bs4)"
        except Exception as exc:
            logger.error("HTTP 降级爬取失败: %s", exc)
            result["content"] = f"ERROR: {exc}"

        return result

    async def close(self):
        """释放浏览器资源。"""
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass
        self._initialized = False
        self._browser = None
        self._playwright = None


# ── 模块级健康检查 ────────────────────────────────────────────

def health() -> dict:
    """返回 CloakBrowser 爬虫服务状态。"""
    cloak_available = False
    cloak_version = None
    try:
        import cloakbrowser
        cloak_available = True
        cloak_version = getattr(cloakbrowser, "__version__", "unknown")
    except ImportError:
        pass

    playwright_available = False
    try:
        import playwright
        playwright_available = True
    except ImportError:
        pass

    return {
        "service": "cloak_scraper",
        "cloakbrowser_installed": cloak_available,
        "cloakbrowser_version": cloak_version,
        "playwright_installed": playwright_available,
    }
