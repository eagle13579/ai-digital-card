"""
AI 名片采集器 — 爬虫模块

URL 输入 → 异步 HTTP 请求 → HTML 解析 → 名片字段结构化提取

基于 httpx 异步客户端实现，遵循 Crawlee BasicCrawler 生命周期模式。
支持自定义请求头、代理、超时配置、重试与并发控制。

快捷使用::

    from app.ai.crawler import fetch_card_from_url

    card = await fetch_card_from_url("https://example.com/profile")
    print(card["name"], card["phone"])

完整引擎::

    from app.ai.crawler import CardCrawler

    async def handler(resp):
        return {"url": resp.url, "title": resp.find("title")}

    crawler = CardCrawler(max_concurrency=10)
    await crawler.add_requests(["https://example.com/card/1"])
    results = await crawler.run(handler)
    await crawler.close()
"""

import importlib
import logging

logger = logging.getLogger(__name__)

# ── Lazy imports via __getattr__ ─────────────────────────────────────────────
# 遵循 top-level app/ai/__init__.py 的懒加载模式

_MODULE_MAP = {
    "CardCrawler": ("app.ai.crawler.card_crawler", "CardCrawler"),
    "CrawlerRequest": ("app.ai.crawler.card_crawler", "CrawlerRequest"),
    "CrawlerResponse": ("app.ai.crawler.card_crawler", "CrawlerResponse"),
    "CardCrawlerError": ("app.ai.crawler.card_crawler", "CardCrawlerError"),
    "FetchError": ("app.ai.crawler.card_crawler", "FetchError"),
    "ParseError": ("app.ai.crawler.card_crawler", "ParseError"),
    "fetch_card_from_url": ("app.ai.crawler.card_crawler", "fetch_card_from_url"),
    "batch_fetch_cards": ("app.ai.crawler.card_crawler", "batch_fetch_cards"),
    "RequestHandler": ("app.ai.crawler.card_crawler", "RequestHandler"),
}


def __getattr__(name):
    """Lazy import: 首次访问属性时触发实际导入"""
    if name in _MODULE_MAP:
        package, attr = _MODULE_MAP[name]
        mod = importlib.import_module(package)
        result = getattr(mod, attr)
        # 缓存到模块命名空间，下次直接访问
        globals()[name] = result
        return result
    if name.startswith("_"):
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r}. "
        f"Try `from app.ai.crawler.{name.lower()} import {name}`"
    )


__all__ = list(_MODULE_MAP.keys())
