#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中韩机会飞轮 — 自动化闭环 (2026-08-08)
======================================
每个周期:
  1. 采集: 韩联社经济/产业 RSS + HN + GitHub (复用 v2 引擎信号) + 中韩报告生成
  2. 信度评估: 规则过滤(关键词/来源权重) + Global/环境模型置信度
  3. 反哺: 高信度机会 ingest_one 入盖娅知识库 (source=kr_cn_flywheel)
  4. 报告: 更新中韩双向产业报告 + 飞轮状态
设计目标: 数据越来越多 → 知识自我净化 → 引擎越用越准 (海容循环理论)

用法:
  cd backend && ./venv/bin/python3 scripts/kr_cn_flywheel.py --cycle daily
  --cycle daily  : 每日完整报告 + 反哺 (cron 08:00)
  --cycle hourly : 仅采集+反哺增量 (cron 每小时, 与 time_machine_hourly 互补)
"""
import sys, os, json, time, hashlib, argparse, re
sys.path.insert(0, "/var/www/ai-digital-card/backend/app/ai")
sys.path.insert(0, "/var/www/ai-digital-card/backend/scripts")

BACKEND = "/var/www/ai-digital-card/backend"
STATE_FILE = os.path.join(BACKEND, "data/time_machine_reports/kr_cn_flywheel_state.json")

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_state(s):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=2)

# ── 1. 采集：韩联社经济/产业 RSS (阿里云实测可达) ──
def collect_kr_news(limit=15):
    """抓取韩联社 RSS 经济+产业通道，输出结构化信号"""
    import urllib.request
    import xml.etree.ElementTree as ET
    sources = [
        ("yna_economy", "https://www.yna.co.kr/rss/economy.xml"),
        ("yna_industry", "https://www.yna.co.kr/rss/industry.xml"),
    ]
    items = []
    for src, url in sources:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
            root = ET.fromstring(raw)
            for item in root.iter("item"):
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                if title:
                    items.append({"source": src, "title": title, "url": link,
                                  "ts": time.strftime("%Y-%m-%d %H:%M")})
        except Exception as e:
            print(f"⚠️ {src} 采集失败: {e}")
    # 按标题去重
    seen, out = set(), []
    for it in items:
        h = hashlib.md5(it["title"][:60].encode()).hexdigest()[:12]
        if h not in seen:
            seen.add(h)
            out.append(it)
        if len(out) >= limit:
            break
    return out

# ── 2. 信度评估：关键词权重 + 来源权重 ──
# 中文关键词（翻译后/中文源）
HIGH_KEYWORDS = ["中韩", "韩中", "出口", "进口", "贸易", "关税", "投资", "FTA", "合作",
                 "半导体", "电池", "化妆品", "医美", "新能源", "芯片", "电商", "消费"]
MED_KEYWORDS = ["增长", "市场", "产业", "政策", "汇率", "物流", "供应链", "品牌"]
# 韩文关键词（韩联社原文标题用）— 수출=出口 수입=进口 무역=贸易 중국=中国 한국=韩国 등
KO_HIGH = ["중국", "한국", "수출", "수입", "무역", "관세", "투자", "반도체", "배터리",
           "화장품", "신에너지", "전기차", "물류", "전자상거래", "FTA", "협력", "경제"]
KO_MED = ["성장", "시장", "산업", "정책", "환율", "공급망", "브랜드", "소비", "생산"]
# 政治/无关排除词
EXCLUDE_KW = ["국회", "의원", "대통령", "정당", "투표", "선거", "국방", "군사", "폭염",
              "양식장", "농식품부", "헤드라인", "날씨", "축산", "수온", "당정",
              "항소심", "실형", "범죄", "화재", "구속", "살인", "폭행", "사고", "재판"]
SRC_WEIGHT = {"yna_economy": 0.9, "yna_industry": 0.9}

def score_signal(item):
    """返回 (score 0-100, 标签) — 信度 = 来源权重×0.5 + 关键词命中×0.3 + 时效×0.2
    中韩双语关键词匹配；政治/无关主题直接排除"""
    src_w = SRC_WEIGHT.get(item.get("source", ""), 0.5)
    title = item.get("title", "")
    # 排除无关主题
    if any(kw in title for kw in EXCLUDE_KW):
        return 5.0, "low"
    high_hits = sum(1 for kw in HIGH_KEYWORDS if kw in title)
    med_hits = sum(1 for kw in MED_KEYWORDS if kw in title)
    ko_high = sum(1 for kw in KO_HIGH if kw in title)
    ko_med = sum(1 for kw in KO_MED if kw in title)
    # 中文关键词权重高（直接命中主题），韩文次之
    kw_score = min(1.0, (high_hits + ko_high) * 0.35 + (med_hits + ko_med) * 0.12)
    recency = 1.0  # RSS 即时
    score = round((src_w * 0.5 + kw_score * 0.3 + recency * 0.2) * 100, 1)
    tag = "high" if score >= 70 else ("medium" if score >= 45 else "low")
    return score, tag

# ── 3. 反哺盖娅 (import ingest_one 直接传, 规避 subprocess/CLI 坑) ──
def translate_ko_zh(title):
    """韩文→中文翻译 (直接调 DeepSeek HTTP API, 纯 ASCII 跳过, 失败回退原文)"""
    if not title or title.encode("ascii", "ignore").decode() == title:
        return title  # 纯 ASCII 无需翻译
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(BACKEND, ".env"))
        import urllib.request
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            return title
        body = json.dumps({
            "model": "deepseek-chat",
            "messages": [{"role": "user",
                          "content": f"把下面韩文新闻标题翻译成简体中文,只输出译文: {title}"}],
            "max_tokens": 120, "temperature": 0.1,
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://api.deepseek.com/chat/completions", data=body,
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {api_key}"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            d = json.loads(resp.read().decode("utf-8"))
        out = d["choices"][0]["message"]["content"].strip()
        return out if out else title
    except Exception:
        return title

def backfeed(items, state, dry_run=False):
    """只反哺 high/medium 且未入库过的信号"""
    try:
        from gaia_backfeed import ingest_one
    except Exception as e:
        print(f"⚠️ 无法导入 ingest_one: {e}")
        return 0, []
    pushed = []
    last_hashes = set(state.get("pushed_hashes", []))
    for it in items:
        score, tag = score_signal(it)
        if tag == "low" or score < 45:
            continue
        h = hashlib.md5(it["title"][:80].encode()).hexdigest()[:16]
        if h in last_hashes:
            continue
        zh = translate_ko_zh(it["title"])
        title = zh[:120]
        content = (f"来源: {it['source']} | {it['url']}\n标题(原文): {it['title']}\n"
                   f"标题(译文): {zh}\n"
                   f"信度评估: {score}/100 ({tag})\n评估依据: 来源权重+关键词命中+时效\n"
                   f"采集时间: {it['ts']}")
        if dry_run:
            pushed.append({"hash": h, "title": title, "score": score})
            last_hashes.add(h)
            continue
        try:
            ts = time.strftime("%Y%m%d_%H%M%S")
            resp = ingest_one(title=f"[中韩机会] {title}",
                              content=content,
                              ktype="intelligence",
                              tags=["中韩", "出海", tag],
                              source_id=f"krcn:{ts}:{h}",
                              source="kr_cn_flywheel")
            ok = resp.get("code") == 200 or (resp.get("data") or {}).get("id")
            if ok:
                pushed.append({"hash": h, "title": title, "score": score})
                last_hashes.add(h)
        except Exception as e:
            print(f"⚠️ 反哺失败 {title[:30]}: {e}")
    state["pushed_hashes"] = list(last_hashes)[-500:]  # 保留最近500
    return len(pushed), pushed

# ── 4. 每日报告 (调用 kr_cn_opportunity_report.py) ──
def daily_report():
    try:
        import subprocess
        r = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "kr_cn_opportunity_report.py"),
             "--top", "12", "--json"],
            capture_output=True, text=True, timeout=300, cwd=BACKEND)
        if r.returncode == 0:
            latest = os.path.join(BACKEND, "data/time_machine_reports/kr_cn_opportunity_latest.json")
            if os.path.exists(latest):
                with open(latest, encoding="utf-8") as f:
                    return json.load(f)
        print(f"⚠️ 报告生成失败 rc={r.returncode}: {r.stderr[-300:]}")
    except Exception as e:
        print(f"⚠️ 每日报告异常: {e}")
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cycle", default="daily", choices=["daily", "hourly"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=15)
    args = ap.parse_args()

    state = load_state()
    items = collect_kr_news(limit=args.limit)
    print(f"📥 采集信号: {len(items)} 条")

    scored = [(it, *score_signal(it)) for it in items]
    n_high = sum(1 for _, _, t in scored if t == "high")
    n_med = sum(1 for _, _, t in scored if t == "medium")
    print(f"📊 信度评估: high={n_high} medium={n_med} low={len(scored)-n_high-n_med}")

    n_push, pushed = backfeed(items, state, dry_run=args.dry_run)
    save_state(state)
    print(f"🧠 反哺盖娅: {n_push} 条新知识")

    report = None
    if args.cycle == "daily":
        report = daily_report()
        if report:
            print(f"📄 中韩双向报告已更新 (Global综合={report.get('kor_global',{}).get('total')})")

    # 输出摘要（供 cron 推送）
    print("")
    print(f"🔄 中韩机会飞轮 [{args.cycle}] {(time.strftime('%Y-%m-%d %H:%M'))}")
    print(f"📥 采集 {len(items)} | 🔎 high {n_high}/med {n_med} | 🧠 新反哺 {n_push}")
    if pushed[:5]:
        print("--- 高信度机会 ---")
        for p in pushed[:5]:
            print(f"• [{p['score']}%] {p['title'][:60]}")

if __name__ == "__main__":
    main()
