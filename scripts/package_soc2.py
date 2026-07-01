#!/usr/bin/env python3
"""
SOC 2 Audit Package Builder
═════════════════════════════
Collects all SOC2 compliance documents into a single audit-ready package,
generates a summary letter for the auditor, and produces a ZIP archive.

Usage:
    python scripts/package_soc2.py              # package to ./soc2_audit_package/
    python scripts/package_soc2.py --output ./my_pkg  # custom output directory
    python scripts/package_soc2.py --zip-only          # only produce zip, skip copy

Output:
    soc2_audit_package/    — extracted document folder
    soc2_audit_package.zip — compressed delivery archive
"""

import argparse
import os
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path

# ── Project root (auto-detect: script lives under scripts/) ──────────────
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

# ── Documents to collect ────────────────────────────────────────────────
REQUIRED_DOCS = {
    # Human-readable label          → relative path from project root
    "SOC 2 路线图":                    "docs/compliance/SOC2_ROADMAP.md",
    "SOC 2 审计准备清单":                "docs/compliance/SOC2_CHECKLIST.md",
    "灾难恢复计划 (DRP)":                "docs/compliance/DRP.md",
    "SOC 2 合规就绪检查清单":             "docs/security/soc2_readiness.md",
    "渗透测试报告模板":                   "docs/soc2/penetration-test-template.md",
    "CI 安全指南":                      "docs/ops/CI_SECURITY.md",
}

# ── SUMMARY.md template ─────────────────────────────────────────────────
SUMMARY_TEMPLATE = """# SOC 2 Audit Ready Package — 审计就绪包

> **项目名称**: AI数智名片 (AI Digital Business Card)
> **打包日期**: {date}
> **打包脚本**: `scripts/package_soc2.py`
> **文档版本**: v1.0

---

## 致尊敬的审计师

本包包含了 AI 数智名片项目为 SOC 2 Type I 审计准备的全部合规文档。
项目当前整体就绪率约 **82%**，涵盖安全性 (Security)、可用性 (Availability)、
保密性 (Confidentiality) 及处理完整性 (Processing Integrity) 四项信任准则。

---

## 包内文档清单

| # | 文档名称 | 源文件路径 | 说明 |
|---|---------|-----------|------|
{doc_table}

---

## 已就绪的控制项摘要

| 信任准则 | 控制总数 | ✅ 已完成 | ⚠️ 部分完成 | ❌ 待完成 | 就绪率 |
|----------|---------:|----------:|-------------:|----------:|-------:|
| 安全性 (Security) | 10 | 8 | 1 | 1 | 85% |
| 可用性 (Availability) | 8 | 5 | 2 | 1 | 75% |
| 保密性 (Confidentiality) | 6 | 4 | 1 | 1 | 75% |
| 处理完整性 (Processing Integrity) | 6 | 5 | 1 | 0 | 92% |
| **合计** | **30** | **22** | **5** | **3** | **82%** |

## 待完成的 P0 阻塞项

以下 6 项为启动 Type I 审计前必须完成的阻塞项：

1. **渗透测试 (第三方)** — 需预约第三方安全公司执行，出具正式报告
2. **数据分类标识体系** — 建立 公开/内部/机密/限制 四层分类
3. **灾难恢复计划 (DRP)** — 文档已就绪，需完成首次演练
4. **事件响应计划 (IRP)** — 需编写正式 IRP 文档
5. **变更管理流程文档** — 需编写正式 CAB 审批流程
6. **安全培训（全员）** — 需完成首次培训并记录

## 时间线

- **2026 Q4**: 完成 SOC 2 Type I 审计
- **2027 Q1**: 完成 SOC 2 Type II 审计

---

*由 {script_name} 于 {date} 自动生成*
"""


def find_doc(rel_path: str) -> Path | None:
    """Resolve a relative path under the project root. Returns None if missing."""
    full = (PROJECT_ROOT / rel_path).resolve()
    return full if full.is_file() else None


def gather_docs(output_dir: Path) -> list[tuple[str, Path, Path]]:
    """
    Copy each required document into output_dir.
    Returns list of (label, src_path, dest_path).
    """
    copied: list[tuple[str, Path, Path]] = []
    errors: list[str] = []

    output_dir.mkdir(parents=True, exist_ok=True)

    for label, rel_path in REQUIRED_DOCS.items():
        src = find_doc(rel_path)
        if src is None:
            errors.append(f"  ❌ 缺少: {rel_path}  ({label})")
            continue

        dest = output_dir / src.name
        shutil.copy2(src, dest)
        copied.append((label, src, dest))
        print(f"  ✅ {label:20s} → {dest.name}")

    if errors:
        print("\n⚠️  以下文档未找到，已跳过：")
        for e in errors:
            print(e)

    return copied


def generate_summary(output_dir: Path, copied: list[tuple[str, Path, Path]]):
    """Write SUMMARY.md — the auditor's introduction letter."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    rows = []
    for idx, (label, src, dest) in enumerate(copied, 1):
        rows.append(
            f"| {idx} | {label} | `{dest.name}` | {_describe_doc(label)} |"
        )
    doc_table = "\n".join(rows)

    summary = SUMMARY_TEMPLATE.format(
        date=now,
        doc_table=doc_table,
        script_name=__file__,
    )
    summary_path = output_dir / "SUMMARY.md"
    summary_path.write_text(summary, encoding="utf-8")
    print(f"  ✅ SUMMARY.md               — 审计师介绍信已生成")
    return summary_path


def create_zip(source_dir: Path, output_path: Path):
    """Create a ZIP archive of the entire audit package."""
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for entry in sorted(source_dir.iterdir()):
            zf.write(entry, arcname=entry.name)
    print(f"\n  📦 打包完成: {output_path.resolve()}")


def _describe_doc(label: str) -> str:
    descriptions = {
        "SOC 2 路线图": "SOC 2 认证整体路线图，含甘特图与时间线",
        "SOC 2 审计准备清单": "详细的 SOC 2 审计准备工作分解清单",
        "灾难恢复计划 (DRP)": "正式灾难恢复计划，含 RTO≤4h、RPO≤1h",
        "SOC 2 合规就绪检查清单": "Type I / Type II 就绪检查与差距分析",
        "渗透测试报告模板": "第三方渗透测试报告模板（OWASP Top 10）",
        "CI 安全指南": "CI/CD 安全规范与 SSH 密钥认证指南",
    }
    return descriptions.get(label, "")


def main():
    parser = argparse.ArgumentParser(description="SOC 2 Audit Package Builder")
    parser.add_argument(
        "--output",
        default=None,
        help="Output directory for extracted docs (default: <project>/soc2_audit_package/)",
    )
    parser.add_argument(
        "--zip-only",
        action="store_true",
        help="Skip fresh copy, only create zip from existing output directory",
    )
    args = parser.parse_args()

    output_dir = Path(args.output) if args.output else (PROJECT_ROOT / "soc2_audit_package")
    zip_path = PROJECT_ROOT / "soc2_audit_package.zip"

    print("=" * 60)
    print("  SOC 2 Audit Package Builder")
    print("=" * 60)
    print(f"  项目根目录: {PROJECT_ROOT}")
    print(f"  输出目录:   {output_dir}")
    print(f"  ZIP 路径:   {zip_path}")
    print("=" * 60)

    if not args.zip_only:
        # Clean output directory
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True)

        print("\n📄 收集合规文档...\n")
        copied = gather_docs(output_dir)

        if not copied:
            print("\n❌ 未找到任何合规文档。请确认项目结构正确。")
            sys.exit(1)

        print(f"\n📝 生成 SUMMARY.md...\n")
        generate_summary(output_dir, copied)

    # Always create/update the zip
    if output_dir.exists() and any(output_dir.iterdir()):
        print(f"\n📦 打包 ZIP...")
        create_zip(output_dir, zip_path)
        zip_size = zip_path.stat().st_size
        print(f"  📏 ZIP 大小: {zip_size / 1024:.1f} KB")
    else:
        print(f"\n⚠️  输出目录为空或不存在，跳过 ZIP 打包。")
        print(f"   请先运行: python {__file__} （不带 --zip-only）")

    print("\n✅ 完成。")


if __name__ == "__main__":
    main()
