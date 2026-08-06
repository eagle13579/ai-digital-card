#!/usr/bin/env python3
"""gaia_distill.py — 盖娅一键蒸馏管线 v1.0.0

对标「一键蒸馏搭建自己的知识库」，补齐 A8/A9/A10 缺口：
  A8  一键编排: collect → sanitize → score → distill → reflect → report
  A9  安全过滤: 蒸馏前剔除敏感信息（手机号/身份证/银行卡/密钥/私钥/邮箱/URL凭据）
  A10 成本分级: 规则粗筛(0 token) → 便宜LLM精炼(deepseek-chat) → 高价值top20%走premium模型

用法:
  python3 gaia_distill.py --sources all             # 全自动蒸馏入库（默认）
  python3 gaia_distill.py --sources local           # 只蒸馏本地素材
  python3 gaia_distill.py --sources web             # 只蒸馏全网素材
  python3 gaia_distill.py --dry                     # 预览（采集+评分，不调LLM不入库）
  python3 gaia_distill.py --max 10                  # 最多提炼N条
  python3 gaia_distill.py --premium-model <name>    # 指定精炼模型（默认用配置）

依赖: DEEPSEEK_API_KEY (backend/.env) | gaia_reflect.py 反哺
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path("/var/www/ai-digital-card/backend")
SCRIPTS = BACKEND / "scripts"
REFLECT_SCRIPT = SCRIPTS / "gaia_reflect.py"
COLLECT_SCRIPT = SCRIPTS / "gaia_collect_raw.py"
DATA_DIR = BACKEND / "data" / "self_study"

# ── A10 成本分级：模型配置 ──
DEFAULT_LLM_BASE = "https://api.deepseek.com/chat/completions"
DEFAULT_LLM_MODEL = "deepseek-chat"   # 便宜模型：粗提炼/常规精炼
PREMIUM_MODEL = os.environ.get("GAIA_PREMIUM_MODEL", "")  # 高价值素材精炼（默认空=同便宜模型）
PREMIUM_RATIO = 0.2                   # top 20% 高价值素材走 premium

# ── A9 安全过滤：敏感信息模式 ──
SENSITIVE_PATTERNS = [
    ("手机号", re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")),
    ("身份证", re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)")),
    ("银行卡", re.compile(r"(?<!\d)\d{16,19}(?!\d)")),
    ("API密钥", re.compile(r"(sk-[A-Za-z0-9]{16,}|api[_-]?key[\"'\s:=]+[A-Za-z0-9]{16,})", re.I)),
    ("私钥", re.compile(r"(-----BEGIN [A-Z ]*PRIVATE KEY-----|0x[a-fA-F0-9]{40,})")),
    ("邮箱", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("URL凭据", re.compile(r"https?://[^\s:/?#]+:[^\s@/?#]+@")),
]
SENSITIVE_WORDS = ["password", "passwd", "secret", "token", "bearer ", "authorization"]


def _load_api_key() -> str:
    env_file = BACKEND / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("DEEPSEEK_API_KEY="):
                return line.split("=", 1)[1].strip()
    return os.environ.get("DEEPSEEK_API_KEY", "")


# ── A9 安全过滤 ──
def sanitize(content: str) -> tuple[str, list[str]]:
    """脱敏：替换敏感信息为占位符，返回(清洗后文本, 命中列表)"""
    hits = []
    for name, pat in SENSITIVE_PATTERNS:
        m = pat.search(content)
        if m:
            hits.append(name)
            content = pat.sub(f"[已过滤:{name}]", content)
    low = content.lower()
    for w in SENSITIVE_WORDS:
        if w in low:
            hits.append(f"关键词:{w}")
            break
    return content, list(dict.fromkeys(hits))


def is_secretive(item: dict) -> bool:
    """素材整体为敏感/元数据快照 → 不蒸馏"""
    content = item.get("content", "")
    if len(content.strip()) < 100:
        return True
    # 纯 JSON 指标快照（如芯森态总览 全0）无蒸馏价值
    if content.lstrip().startswith("{") and content.count('"') > 20:
        return True
    title = item.get("title", "")
    if "总览快照" in title or "桥接异常" in title:
        return True
    return False


# ── A10 成本分级：规则粗筛（0 token）──
VALUE_KEYWORDS = ["架构", "模式", "优化", "策略", "框架", "流程", "管道", "蒸馏",
                  "引擎", "网关", "模型", "编排", "自动化", "管线", "性能", "安全",
                  "测试", "部署", "方法论", "最佳实践", "SOP", "产品", "商业化"]
SOURCE_WEIGHT = {"github": 8, "arxiv": 9, "local_pool": 7, "palace": 4}


def score_item(item: dict) -> int:
    """0-100 质量评分：来源权重 + 内容长度 + 价值关键词 + 结构完整度"""
    s = 0
    s += SOURCE_WEIGHT.get(item.get("source", ""), 5)
    content = item.get("content", "")
    length = len(content.strip())
    if length >= 1500:
        s += 25
    elif length >= 800:
        s += 18
    elif length >= 300:
        s += 10
    else:
        s += 3
    kws = sum(1 for kw in VALUE_KEYWORDS if kw in content)
    s += min(kws * 3, 30)
    if any(mark in content for mark in ("##", "核心", "洞察", "方案", "步骤", "1.")):
        s += 10
    title = item.get("title", "")
    if len(title) >= 8:
        s += 5
    return min(s, 100)


# ── LLM 蒸馏（A10 精炼阶段）──
def llm_distill(item: dict, api_key: str, model: str) -> dict | None:
    """调用 LLM 把素材提炼为结构化知识条目"""
    content = item.get("content", "")[:2500]
    title = item.get("title", "")[:200]
    prompt = (
        "你是知识蒸馏引擎。将下面素材提炼为1条高质量知识，只输出合法JSON，不要多余文字。\n"
        "JSON格式: {\"title\": \"标题\", \"knowledge_type\": \"pattern|insight|rule|optimization|concept\", "
        "\"content\": \"核心洞察+可复用方案+适用场景（300字以上）\", \"tags\": [\"标签1\",\"标签2\"]}\n"
        "规则: 宁缺毋滥；必须包含可复用价值；content 至少300字；tags 2-4个。\n"
        f"素材标题: {title}\n素材内容: {content}\n"
    )
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4,
        "max_tokens": 1200,
        "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        DEFAULT_LLM_BASE,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = data["choices"][0]["message"]["content"].strip()
        # 提取 JSON（模型可能带 ```json 包裹）
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            return None
        k = json.loads(m.group(0))
        k.setdefault("title", item.get("title", "")[:120])
        k.setdefault("knowledge_type", "insight")
        k.setdefault("tags", [])
        k["content"] = k.get("content", "")[:2000]
        if len(k["content"]) < 100:
            return None
        return k
    except Exception as e:
        print(f"    [WARN] LLM提炼失败 {item.get('title', '')[:40]}: {e}", file=sys.stderr)
        return None


# ── 反哺 ──
def reflect(k: dict, source: str, idx: int = 0) -> bool:
    """调用 gaia_reflect.py 入库（source-id 加毫秒+序号避免唯一索引冲突）"""
    cmd = [
        sys.executable, str(REFLECT_SCRIPT),
        "--title", k["title"][:200],
        "--content", k["content"],
        "--type", k["knowledge_type"],
        "--tags", ",".join(k.get("tags", [])[:4]),
        "--source", source,
        "--source-id", "distill:%s_%02d" % (datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f"), idx),
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return r.returncode == 0 or '"id"' in r.stdout
    except Exception:
        return False


def collect_files(path_str: str) -> list[dict]:
    """采集指定文件/目录（企业素材蒸馏用）"""
    p = Path(path_str)
    files: list[Path] = []
    if p.is_file():
        files = [p]
    elif p.is_dir():
        files = [f for f in p.rglob("*") if f.is_file() and f.suffix.lower() in (".md", ".txt", ".yaml", ".yml", ".json")]
    items = []
    for f in sorted(files):
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            if len(content.strip()) < 100:
                continue
            title = f.stem[:120]
            items.append({
                "source": "enterprise",
                "title": title,
                "content": content[:2000],
                "tags": ["企业蒸馏"],
                "raw": {"path": str(f), "content": content[:2000]},
            })
        except Exception:
            continue
    return items


def main():
    parser = argparse.ArgumentParser(description="盖娅一键蒸馏管线 v1.0.0 (A8一键+A9安全+A10分级)")
    parser.add_argument("--sources", default="all", help="all|web|local")
    parser.add_argument("--file", default="", help="蒸馏指定文件/目录（企业素材）")
    parser.add_argument("--source-tag", default="distill_auto", help="反哺source标记(默认distill_auto)")
    parser.add_argument("--dry", action="store_true", help="预览模式：只采集+评分，不调LLM不入库")
    parser.add_argument("--max", type=int, default=0, help="最多提炼N条(0=全部高价值)")
    parser.add_argument("--premium-model", default="", help="精炼模型(默认同便宜模型)")
    parser.add_argument("--min-score", type=int, default=35, help="粗筛阈值(默认35, local可调高)")
    args = parser.parse_args()

    api_key = _load_api_key()
    premium = args.premium_model or PREMIUM_MODEL or DEFAULT_LLM_MODEL

    print("=" * 56)
    print("🧪 盖娅一键蒸馏管线 v1.0.0")
    print("=" * 56)

    # 1. 采集（--file 优先，否则走标准源）
    print("\n[1/6] 采集素材 ...")
    if args.file:
        items = collect_files(args.file)
        print(f"  企业素材采集 {len(items)} 条 ({args.file})")
    else:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        r = subprocess.run(
            [sys.executable, str(COLLECT_SCRIPT), "--sources", args.sources],
            capture_output=True, text=True, timeout=180,
        )
        try:
            collected = json.loads(r.stdout)
        except Exception:
            print("采集失败:", r.stderr[-400:])
            return
        items = collected.get("items", [])
        print(f"  采集 {len(items)} 条")

    # 2. 清洗 + A9 安全过滤
    print("[2/6] 清洗 + 安全过滤 (A9) ...")
    clean_items = []
    filtered = {"敏感": 0, "低质": 0, "快照": 0}
    for it in items:
        if is_secretive(it):
            filtered["快照"] += 1
            continue
        clean_content, hits = sanitize(it.get("content", ""))
        if hits:
            filtered["敏感"] += 1
            it["content"] = clean_content + "\n[脱敏提示: " + ",".join(hits) + "]"
        if len(it.get("content", "").strip()) < 150:
            filtered["低质"] += 1
            continue
        clean_items.append(it)
    print(f"  通过 {len(clean_items)} 条 | 过滤: {filtered}")

    # 3. A10 成本分级：规则粗筛（0 token）
    print("[3/6] 规则粗筛评分 (A10 第一级, 0 token) ...")
    scored = []
    for it in clean_items:
        s = score_item(it)
        it["score"] = s
        scored.append(it)
    scored.sort(key=lambda x: x["score"], reverse=True)
    pool = [it for it in scored if it["score"] >= args.min_score]
    print(f"  评分完成: 最高 {scored[0]['score'] if scored else 0} 分 | 过阈值 {len(pool)} 条")

    if args.max:
        pool = pool[: args.max]
    if args.dry:
        print("\n[DRY] 预览（不入库）:")
        for it in pool[:10]:
            print(f"  [{it['score']:3d}分][{it['source']}] {it['title'][:60]}")
        print(f"\n预览: {len(pool)} 条待精炼 (评分≥{args.min_score})")
        return

    # 4. 精炼（A10 第二级：LLM）
    print(f"[4/6] LLM精炼 ({DEFAULT_LLM_MODEL} 便宜模型 / top{PREMIUM_RATIO:.0%}走 {premium}) ...")
    n_premium = max(1, int(len(pool) * PREMIUM_RATIO))
    ok, fail = [], 0
    for i, it in enumerate(pool):
        model = premium if i < n_premium else DEFAULT_LLM_MODEL
        k = llm_distill(it, api_key, model)
        if k:
            k["_score"] = it["score"]
            k["_src"] = it["source"]
            ok.append(k)
        else:
            fail += 1
        print(f"    [{i+1}/{len(pool)}] {'✅' if k else '❌'} {it['title'][:44]}")
    print(f"  精炼完成: {len(ok)} 成功 / {fail} 失败")

    # 5. 反哺
    print("[5/6] 反哺盖娅大脑 ...")
    saved = 0
    for i, k in enumerate(ok):
        if reflect(k, source=args.source_tag, idx=i):
            saved += 1
    print(f"  入库 {saved} 条")

    # 6. 简报
    print("[6/6] 简报")
    print("=" * 56)
    print(f"📊 蒸馏简报: 采集{len(items)} → 过滤{len(items)-len(clean_items)} → "
          f"评分{len(scored)} → 精炼{len(ok)} → 入库{saved}")
    for k in ok[:8]:
        print(f"  • [{k['knowledge_type']}] {k['title'][:50]}")
    if len(ok) > 8:
        print(f"  ... 等 {len(ok)} 条")
    print("=" * 56)


if __name__ == "__main__":
    main()
