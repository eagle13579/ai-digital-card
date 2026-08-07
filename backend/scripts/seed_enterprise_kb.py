#!/usr/bin/env python3
"""seed_enterprise_kb.py — 批量灌入企业文档到 enterprise_kb/raw（P1-3 扩充知识源）

把两个项目的核心文档（README/架构/手册/说明）整理成企业知识素材，
供 gaia_distill.py 蒸馏入库 → 军团差异化学习使用。

用法:
    python3 seed_enterprise_kb.py           # 灌入并触发蒸馏
    python3 seed_enterprise_kb.py --dry     # 只预览要灌哪些
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path("/var/www/ai-digital-card/backend")
RAW_DIR = BACKEND / "data" / "enterprise_kb" / "raw"
DISTILL_SCRIPT = BACKEND / "scripts" / "gaia_distill.py"
VENV_PY = BACKEND / "venv" / "bin" / "python3"

# ── 企业文档清单：项目 → 文档路径 → 知识标题 ──
# 格式: (源文件绝对路径, 素材标题, 租户标签)
SOURCES: list[tuple[Path, str, str]] = [
    # AI数智名片 核心文档
    (Path("/var/www/ai-digital-card/README.md"), "AI数智名片产品README", "aicard"),
    (Path("/var/www/ai-digital-card/ARCHITECTURE.md"), "AI数智名片系统架构", "aicard"),
    (Path("/var/www/ai-digital-card/DESIGN.md"), "AI数智名片设计文档", "aicard"),
    (Path("/var/www/ai-digital-card/AGENTS.md"), "AI数智名片智能体约定", "aicard"),
    (Path("/var/www/ai-digital-card/BASELINE.md"), "AI数智名片基线规范", "aicard"),
    (Path("/var/www/ai-digital-card/data/enterprise_kb/raw/20260806_002549_default_AI数智名片企业销售手册.md"), "AI数智名片企业销售手册", "aicard"),
    # 链客宝
    (Path("/var/www/liankebao/README.md"), "链客宝产品README", "liankebao"),
    (Path("/var/www/liankebao/README-小程序.md"), "链客宝小程序说明", "liankebao"),
]


def sanitize_title(title: str) -> str:
    return re.sub(r"[^\w\u4e00-\u9fff_-]", "_", title)[:50]


def read_doc(path: Path) -> str:
    """读取文档，限制单篇长度（取头部最有价值部分）。"""
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""
    # 去掉敏感信息（密码/密钥/邮箱）防止蒸馏入知识库
    content = re.sub(r"(?i)(password|secret|token|api[_-]?key|jwt)[\"'=\s:]+[A-Za-z0-9_\-\.@]{6,}", "[REDACTED]", content)
    content = re.sub(r"(?<![\w.+-])[\w.+-]+@[\w-]+\.[\w.]+", "[EMAIL]", content)
    # 取前 8000 字符（核心价值通常在头部）
    return content[:8000]


def build_material(title: str, content: str, tenant: str) -> str:
    """组装成蒸馏素材格式（与 distill_router 一致）。"""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe = sanitize_title(title)
    body = f"# {title}\n\n{content}\n\n---\n[tenant: {tenant}]\n"
    fname = f"{ts}_{tenant}_{safe}.md"
    return fname, body


def main() -> int:
    ap = argparse.ArgumentParser(description="批量灌入企业文档到 enterprise_kb")
    ap.add_argument("--dry", action="store_true", help="只预览")
    ap.add_argument("--distill", action="store_true", default=True, help="灌入后触发蒸馏")
    args = ap.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    written = []

    for src_path, title, tenant in SOURCES:
        if not src_path.exists():
            print(f"  ⚠️ 跳过（不存在）: {src_path}")
            continue
        content = read_doc(src_path)
        if len(content) < 200:
            print(f"  ⚠️ 跳过（内容过短 {len(content)}B）: {src_path}")
            continue
        fname, body = build_material(title, content, tenant)
        fpath = RAW_DIR / fname
        if args.dry:
            print(f"  📄 预览: {fname} ({len(body)}B)")
            continue
        fpath.write_text(body, encoding="utf-8")
        written.append(fname)
        print(f"  ✅ 写入: {fname} ({len(body)}B)")

    if args.dry:
        print(f"\n预览完成：共 {len(written)} 篇（dry-run 未写入）")
        return 0

    print(f"\n灌入完成：{len(written)} 篇文档 → {RAW_DIR}")
    print(f"raw 目录现有: {len(list(RAW_DIR.glob('*.md')))} 篇")

    if args.distill and written:
        print("\n🚀 触发盖娅蒸馏入库...")
        proc = subprocess.run(
            [str(VENV_PY), str(DISTILL_SCRIPT), "--file", str(RAW_DIR),
             "--source-tag", "distill_enterprise", "--max", "20"],
            capture_output=True, text=True, timeout=430,
        )
        tail = (proc.stdout or "")[-2000:]
        print(tail)
        if proc.returncode != 0:
            print("⚠️ 蒸馏返回码:", proc.returncode)
            print((proc.stderr or "")[-1000:])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
