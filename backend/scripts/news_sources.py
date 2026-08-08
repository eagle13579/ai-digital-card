#!/usr/bin/env python3
"""
多源新闻采集器 (news_sources.py)
================================
2026-08-08 海容要求：除了国外新闻源，增加国内财经源（凤凰/新华/东财/和讯等），
覆盖全球 → 立体事件网络采集层。

数据源:
  国外 RSS:
    - 韩联社 economy.xml + industry.xml（韩国财经/产业）
    - 法国24 五区域 RSS（全球/欧/美/非/亚太/中东）
  国内 HTML（阿里云实测全部可达）:
    - 凤凰财经 finance.ifeng.com
    - 新华财经 news.cn/fortune
    - 东方财富 eastmoney.com
    - 和讯网 hexun.com
    - 财联社电报 cls.cn/telegraph
    - 新浪财经 finance.sina.com.cn
    - 第一财经 yicai.com
    - 华尔街见闻 wallstreetcn.com

统一输出: [{"title","desc","link","source","lang","ts"}, ...]
用法:
  from news_sources import fetch_all_sources, fetch_html_news
  items = fetch_all_sources()
"""

import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timedelta
from xml.etree import ElementTree as ET

BACKEND = "/var/www/ai-digital-card/backend"

# ============================================================
# 国外 RSS 源
# ============================================================
RSS_FEEDS = [
    {"name": "韩联社经济", "url": "https://www.yna.co.kr/rss/economy.xml", "lang": "ko"},
    {"name": "韩联社产业", "url": "https://www.yna.co.kr/rss/industry.xml", "lang": "ko"},
    {"name": "法国24主站", "url": "https://www.france24.com/en/rss", "lang": "en"},
    {"name": "法国24亚洲", "url": "https://www.france24.com/en/asia-pacific/rss", "lang": "en"},
    {"name": "法国24中东", "url": "https://www.france24.com/en/middle-east/rss", "lang": "en"},
]

# ============================================================
# 国内 HTML 源（阿里云 47.116.116.87 实测全部 200）
# ============================================================
HTML_SOURCES = [
    {"name": "凤凰财经", "url": "https://finance.ifeng.com/", "lang": "zh",
     "patterns": [r'<a[^>]*href="([^"]*)"[^>]*>([^<]{8,60})</a>']},
    # 新华财经 PC 版 index.htm（实测 /fortune/ 是 580B 空壳，index.htm 有 90 条）
    {"name": "新华财经", "url": "http://www.news.cn/fortune/index.htm", "lang": "zh",
     "patterns": [r'<a[^>]*href="([^"]*)"[^>]*>([^<]{8,60})</a>']},
    {"name": "东方财富", "url": "https://www.eastmoney.com/", "lang": "zh",
     "patterns": [r'<a[^>]*href="([^"]*)"[^>]*>([^<]{8,60})</a>']},
    {"name": "和讯网", "url": "http://www.hexun.com/", "lang": "zh",
     "patterns": [r'<a[^>]*href="([^"]*)"[^>]*>([^<]{8,60})</a>']},
    # 财联社电报是 JS 渲染壳 + API 签名反爬（实测 nodeapi 404）→ 降级为可选，抓不到不报错
    {"name": "财联社电报", "url": "https://www.cls.cn/telegraph", "lang": "zh",
     "patterns": [], "optional": True},
    {"name": "新浪财经", "url": "https://finance.sina.com.cn/", "lang": "zh",
     "patterns": [r'<a[^>]*href="([^"]*)"[^>]*>([^<]{8,60})</a>']},
    {"name": "第一财经", "url": "https://www.yicai.com/", "lang": "zh",
     "patterns": [r'<a[^>]*href="([^"]*)"[^>]*>([^<]{8,60})</a>']},
    # 华尔街见闻 JS 渲染壳 → 走公开 API（api-one.wallstcn.com，实测可用）
    {"name": "华尔街见闻", "url": "https://api-one.wallstcn.com/apiv1/content/lives?channel=global-channel&limit=60",
     "lang": "zh", "api": True},
]

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}

# 导航/噪音链接过滤（标题太泛或非新闻）
NAV_NOISE = [
    "首页", "新闻", "财经", "更多", "登录", "注册", "搜索", "客户端", "APP", "下载",
    "关于我们", "联系我们", "版权", "免责声明", "隐私", "股票", "基金", "期货", "债券",
    "黄金", "外汇", "港股", "美股", "A股", "专题", "专栏", "观点", "视频", "直播",
    "排行", "热门", "最新", "滚动", "首页 >", "设为首页", "加入收藏", "English", "无障碍",
]


def _http_get(url: str, timeout: int = 15) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_rss(url: str, source_name: str = "", lang: str = "") -> list:
    """拉取 RSS 并解析标题/摘要"""
    items = []
    try:
        data = _http_get(url)
        root = ET.fromstring(data)
        for item in root.iter("item"):
            title = (item.findtext("title") or "").strip()
            desc = (item.findtext("description") or "").strip()
            link = item.findtext("link") or ""
            if title:
                items.append({"title": title, "desc": desc, "link": link,
                              "source": source_name or url, "lang": lang,
                              "ts": datetime.now().isoformat(timespec="seconds")})
    except Exception as e:
        print(f"  ⚠️ RSS失败 {url}: {e}")
    return items


def fetch_html_news(src: dict, timeout: int = 15) -> list:
    """抓国内源 → 提取新闻标题+链接（支持 HTML 正则 / API JSON 两种模式）"""
    items = []
    name, url, lang = src["name"], src["url"], src["lang"]
    # API 型源（华尔街见闻 lives 接口）
    if src.get("api"):
        return _fetch_api_news(src, timeout)
    try:
        data = _http_get(url, timeout)
        raw = data.decode("utf-8", "ignore")
        # GBK 源（和讯等老站 utf-8 解码会乱码）：检测典型 GBK 乱码特征
        if re.search(r"[\u00c0-\u00ff]{2,}", raw) and not re.search(r"[\u4e00-\u9fff]", raw[:2000]):
            try:
                raw = data.decode("gbk", "ignore")
            except Exception:
                pass
        text = raw
    except Exception as e:
        print(f"  ⚠️ HTML失败 {name} {url}: {e}")
        return items
    seen = set()
    for pat in src.get("patterns", []):
        for href, title in re.findall(pat, text):
            t = re.sub(r"<[^>]+>", "", title).strip()
            # 过滤噪音
            if not t or len(t) < 8 or len(t) > 80:
                continue
            if any(n in t for n in NAV_NOISE):
                continue
            if t in seen:
                continue
            seen.add(t)
            # 补全相对链接
            if href.startswith("/"):
                from urllib.parse import urljoin
                href = urljoin(url, href)
            if not href.startswith("http"):
                continue
            items.append({"title": t, "desc": "", "link": href,
                          "source": name, "lang": lang,
                          "ts": datetime.now().isoformat(timespec="seconds")})
    return items


def _fetch_api_news(src: dict, timeout: int = 15) -> list:
    """API 型源：拉 JSON → 提取 content_text 作为新闻标题"""
    items = []
    name, url, lang = src["name"], src["url"], src["lang"]
    try:
        data = _http_get(url, timeout)
        text = data.decode("utf-8", "ignore")
        payload = json.loads(text)
        # 华尔街见闻 lives: data.items[].content_text
        items_data = (payload.get("data") or {}).get("items") or []
        for it in items_data[:60]:
            t = (it.get("content_text") or "").strip()
            if not t or len(t) < 8:
                continue
            # 只取首句/首行作为标题
            t = re.split(r"[。！？\n]", t)[0][:60]
            if len(t) < 8:
                continue
            items.append({"title": t, "desc": "", "link": it.get("uri") or url,
                          "source": name, "lang": lang,
                          "ts": datetime.now().isoformat(timespec="seconds")})
    except Exception as e:
        print(f"  ⚠️ API失败 {name}: {e}")
    return items


def fetch_all_sources() -> list:
    """拉全部源，返回统一新闻列表（去重）"""
    all_items = []
    for feed in RSS_FEEDS:
        all_items += fetch_rss(feed["url"], feed["name"], feed["lang"])
    for src in HTML_SOURCES:
        all_items += fetch_html_news(src)
    # HTML 源无真实发布时间：按同源顺序递减时间梯度（首页越靠前越新）
    now = datetime.now()
    from collections import defaultdict
    per_source = defaultdict(int)
    for it in all_items:
        if it["lang"] == "zh" and it.get("source"):
            per_source[it["source"]] += 1
            # 每源第n条 = now - n*8分钟（模拟时间梯度，保证 timeline 排序稳定）
            idx = per_source[it["source"]]
            it["ts"] = (now - timedelta(minutes=idx * 8)).isoformat(timespec="seconds")
    # 去重（标题相似度）
    seen_titles = set()
    deduped = []
    for it in all_items:
        key = re.sub(r"\s+", "", it["title"])[:40]
        if key in seen_titles:
            continue
        seen_titles.add(key)
        deduped.append(it)
    return deduped


def source_stats(items: list) -> dict:
    """按源统计数量"""
    stats = {}
    for it in items:
        stats[it["source"]] = stats.get(it["source"], 0) + 1
    return stats


if __name__ == "__main__":
    items = fetch_all_sources()
    print(f"共采集 {len(items)} 条新闻:")
    for s, c in sorted(source_stats(items).items(), key=lambda x: -x[1]):
        print(f"  {s}: {c}条")
    print("\n前10条:")
    for it in items[:10]:
        print(f"  [{it['lang']}] {it['title'][:45]}")
