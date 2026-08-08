#!/usr/bin/env python3
"""
新闻自动采集 → 产业链影响链推演 → 日报（news_impact_daily.py）
================================================================
2026-08-08 海容方向①：自动喂新闻，每天生成影响链推演日报

数据源（阿里云实测可达）:
  - 韩联社 economy.xml + industry.xml（韩国财经/产业）
  - 法国24 五区域 RSS（全球/欧/美/非/亚太/中东）
流程:
  1. 拉 RSS → 提取标题+摘要
  2. 过滤（跳过政治/犯罪/天气/体育）
  3. 每条跑 NewsImpactEngine.analyze → 影响链
  4. 按置信度排序 → 生成 Markdown 日报
  5. 可选飞书推送（防骚扰：仅推送高分影响链，每日最多3条）

用法:
  python3 news_impact_daily.py              # 生成日报
  python3 news_impact_daily.py --push       # 生成并推送飞书
"""

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.request
from datetime import datetime
from xml.etree import ElementTree as ET

# 项目路径
BACKEND = "/var/www/ai-digital-card/backend"
sys.path.insert(0, os.path.join(BACKEND, "app", "ai"))

REPORT_DIR = os.path.join(BACKEND, "data", "time_machine_reports")
STATE_FILE = os.path.join(REPORT_DIR, "news_impact_state.json")

# RSS 源（阿里云可达性已实测）
RSS_FEEDS = [
    {"name": "韩联社经济", "url": "https://www.yna.co.kr/rss/economy.xml"},
    {"name": "韩联社产业", "url": "https://www.yna.co.kr/rss/industry.xml"},
    {"name": "法国24主站", "url": "https://www.france24.com/en/rss"},
    {"name": "法国24亚洲", "url": "https://www.france24.com/en/asia-pacific/rss"},
    {"name": "法国24中东", "url": "https://www.france24.com/en/middle-east/rss"},
]

# 排除关键词（政治/犯罪/天气/体育/娱乐等非产业新闻）
EXCLUDE_KW = [
    "足球", "世界杯", "奥运会", "选举", "投票", "议会", "总统", "总理", "首相",
    "犯罪", "枪击", "爆炸", "袭击", "天气", "台风", "地震", "洪水", "彩票",
    "娱乐", "明星", "电影", "音乐", "sport", "football", "world cup", "olympics",
    "election", "vote", "crime", "murder", "weather", "typhoon", "earthquake",
    "hollywood", "celebrity", "festival", "concert", "世界杯", "联赛", "冠军",
    "核试验", "阅兵", "军演", "人质", "绑架",
]

def fetch_rss(url: str, timeout: int = 20) -> list:
    """拉取 RSS 并解析标题/摘要"""
    items = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read()
        root = ET.fromstring(data)
        for item in root.iter("item"):
            title = (item.findtext("title") or "").strip()
            desc = (item.findtext("description") or "").strip()
            link = item.findtext("link") or ""
            if title:
                items.append({"title": title, "desc": desc, "link": link, "source": url})
    except Exception as e:
        print(f"  ⚠️ RSS失败 {url}: {e}")
    return items

def translate_ko_zh(text: str) -> str:
    """韩文 → 中文（DeepSeek 翻译，失败返回原文）"""
    try:
        env_path = os.path.join(BACKEND, ".env")
        api_key = ""
        if os.path.isfile(env_path):
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    if line.startswith("DEEPSEEK_API_KEY="):
                        api_key = line.split("=", 1)[1].strip()
        if not api_key:
            return text
        req = urllib.request.Request(
            "https://api.deepseek.com/chat/completions",
            data=json.dumps({
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": f"把下面的韩文新闻标题翻译成中文，只输出中文翻译，不要解释：\n{text}"}],
                "max_tokens": 100,
            }).encode(),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"})
        with urllib.request.urlopen(req, timeout=20) as r:
            resp = json.loads(r.read().decode())
            return (resp.get("choices") or [{}])[0].get("message", {}).get("content", "").strip() or text
    except Exception:
        return text

def is_relevant(title: str, desc: str) -> bool:
    """过滤：排除政治/犯罪/天气/娱乐等"""
    text = f"{title} {desc}".lower()
    # 优先保留财经/产业关键词
    finance_kw = ["半导体", "芯片", "出口", "进口", "关税", "投资", "工厂", "产能",
                  "涨价", "降价", "供应链", "市场", "股价", "经济", "产业", "制造",
                  "电池", "汽车", "能源", "矿产", "铜", "稀土", "石油", "天然气",
                  "AI", "人工智能", "机器人", "数据中心", "光伏", "光伏", "存储",
                  "银行", "利率", "通胀", "GDP", "贸易", "收购", "合并", "IPO",
                  "chip", "semiconductor", "export", "tariff", "investment", "factory",
                  "supply", "market", "economy", "industry", "battery", "auto", "energy",
                  "mining", "copper", "oil", "gas", "AI", "robot", "data center", "solar",
                  "bank", "rate", "inflation", "trade", "merger", "IPO"]
    if any(kw.lower() in text for kw in finance_kw):
        # 再排除纯政治类
        return not any(kw in text for kw in EXCLUDE_KW)
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--push", action="store_true", help="推送飞书")
    parser.add_argument("--limit", type=int, default=25, help="最多采集条数")
    args = parser.parse_args()

    from china_softbank_engine.news_impact import NewsImpactEngine
    eng = NewsImpactEngine()

    os.makedirs(REPORT_DIR, exist_ok=True)

    # 1. 采集
    print("📡 采集新闻...")
    raw = []
    for feed in RSS_FEEDS:
        items = fetch_rss(feed["url"])
        print(f"  {feed['name']}: {len(items)} 条")
        raw.extend(items)

    # 2. 过滤 + 去重
    seen = set()
    news = []
    for item in raw:
        h = hashlib.md5(item["title"][:60].encode()).hexdigest()[:10]
        if h in seen:
            continue
        seen.add(h)
        if is_relevant(item["title"], item.get("desc", "")):
            news.append(item)
    print(f"✅ 过滤后: {len(news)} 条相关新闻（共 {len(raw)} 条原始）")

    # 3. 每条推演（韩文先翻译成中文再识别）
    print("🧠 推演影响链...")
    results = []
    for item in news[:args.limit]:
        try:
            title = item["title"]
            desc = (item.get("desc") or "")[:200]
            # 韩文 → 中文翻译（复用 DeepSeek）
            if re.search(r'[\uac00-\ud7af]', title):
                title_zh = translate_ko_zh(title)
                if title_zh and title_zh != title:
                    title = title_zh
            r = eng.analyze(title, desc)
            det = r.get("detected") or {}
            if det.get("confidence", 0) >= 0.35:  # 低置信不入选
                results.append({
                    "title": item["title"],
                    "title_zh": title if title != item["title"] else "",
                    "desc": desc,
                    "link": item.get("link", ""),
                    "event_type": det.get("event_type"),
                    "impact_node": det.get("impact_node"),
                    "direction": det.get("direction"),
                    "confidence": det.get("confidence"),
                    "matched_keywords": det.get("matched_keywords", []),
                    "opportunities": r.get("opportunities", [])[:5],
                    "swarm_top": (r.get("swarm") or {}).get("results", [])[:5],
                })
        except Exception as e:
            print(f"  ⚠️ 推演失败: {e}")

    # 排序：置信度 × 机会数
    results.sort(key=lambda x: x["confidence"] * (1 + len(x["opportunities"]) * 0.2), reverse=True)

    # 4. 生成日报
    now = datetime.now().strftime("%Y%m%d_%H%M")
    lines = [
        "# 📰 产业链影响链日报（新闻推演）",
        "",
        f"- 生成: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"- 采集: {len(raw)} 条 → 相关 {len(news)} 条 → 推演 {len(results)} 条",
        f"- 引擎: NewsImpactEngine + 51节点产业链图谱 + 群体智能预判",
        "",
    ]
    for i, r in enumerate(results[:15], 1):
        lines.append(f"## {i}. {r['title']}")
        lines.append(f"- 识别: **{r['event_type']}** → 冲击 {r['impact_node']}（{r['direction']}）置信度 {r['confidence']*100:.0f}%")
        if r.get("matched_keywords"):
            lines.append(f"- 命中: {', '.join(r['matched_keywords'][:6])}")
        lines.append("- **受益标的 Top5**:")
        for o in r["opportunities"][:5]:
            lines.append(f"  - 🎯 {o.get('company')}({o.get('ticker')}) — {o.get('node')} 冲击分{o.get('score')}")
        lines.append("")
    report = "\n".join(lines)
    path = os.path.join(REPORT_DIR, f"news_impact_daily_{now}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"✅ 日报已生成: {path}")
    print(report[:800])

    # 5. 飞书推送（可选）
    if args.push:
        push_feishu(results[:3], path)

    return 0


def push_feishu(top3: list, report_path: str):
    """推送 Top3 高分影响链到飞书（复用时光机推送凭证）"""
    import urllib.parse
    app_id = "cli_a97803e1ba245bc9"
    chat_id = "oc_92e570b914ebd7ec0a0bb96caade03e8"
    # 从 .env 读 app_secret
    secret = ""
    env_path = "/var/www/ai-digital-card/backend/.env"
    if os.path.isfile(env_path):
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                if line.startswith("FEISHU_APP_SECRET="):
                    secret = line.split("=", 1)[1].strip()
    if not secret:
        print("⚠️ 无 FEISHU_APP_SECRET，跳过推送")
        return

    # 获取 token
    try:
        req = urllib.request.Request(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            data=json.dumps({"app_id": app_id, "app_secret": secret}).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            token = json.loads(r.read().decode()).get("tenant_access_token", "")
    except Exception as e:
        print(f"⚠️ 获取token失败: {e}")
        return

    # 组装消息
    msg_lines = ["📰 **产业链影响链日报（自动推演）**", ""]
    for r in top3:
        msg_lines.append(f"**{r['title'][:50]}**")
        msg_lines.append(f"识别: {r['event_type']} → {r['impact_node']}（{r['direction']}）置信{r['confidence']*100:.0f}%")
        for o in r["opportunities"][:3]:
            msg_lines.append(f"  🎯 {o.get('company')}({o.get('ticker')}) — {o.get('node')}")
        msg_lines.append("")
    msg = "\n".join(msg_lines)

    try:
        req = urllib.request.Request(
            "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
            data=json.dumps({"receive_id": chat_id, "msg_type": "text",
                             "content": json.dumps({"text": msg})}).encode(),
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = json.loads(r.read().decode())
            print(f"✅ 飞书推送: {resp.get('code')} {resp.get('msg')}")
    except Exception as e:
        print(f"⚠️ 推送失败: {e}")


if __name__ == "__main__":
    sys.exit(main())
