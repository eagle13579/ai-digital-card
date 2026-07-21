#!/usr/bin/env python3
"""
auto_training_pipeline.py — 用户增长驱动模型自动训练管道 (Python版)

原是 auto_training_pipeline.sh，为消除 Windows 上 bash.exe 弹窗而转为 .py.
每15分钟运行一次（由 Hermes cron 调度），自动完成:
  Step 1: 用户数据增强（更新match_records匹配对）
  Step 2: 准备训练数据（构建V2特征集 → v2_training_data.json）
  Step 3: 训练V2三塔匹配模型（防过拟合版）
  Step 4: 输出训练报告摘要

Usage:
    python scripts/auto_training_pipeline.py

Exit code: 0 = success, 1 = any step failed
"""

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ── Windows CP936 Emoji 兼容 ──
if sys.platform == "win32" and sys.stdout.encoding and "utf" not in sys.stdout.encoding.lower():
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


BACKEND_DIR = Path(__file__).resolve().parent.parent
REPORT_PATH = BACKEND_DIR / "models" / "training_report_v2.json"
PYTHON = sys.executable  # 用当前 Python，避免跨版本


def _run_script(script_rel: str, timeout: int | None = None) -> str:
    """运行 scripts/ 下的 Python 脚本，返回 stdout。失败时抛异常。"""
    script_path = BACKEND_DIR / "scripts" / script_rel
    if not script_path.is_file():
        raise FileNotFoundError(f"脚本不存在: {script_path}")

    cmd = [PYTHON, str(script_path)]
    kwargs: dict = {
        "capture_output": True,
        "text": True,
        "cwd": str(BACKEND_DIR),
    }
    if sys.platform == "win32":
        kwargs["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
    if timeout is not None:
        kwargs["timeout"] = timeout

    result = subprocess.run(cmd, **kwargs)
    if result.returncode != 0:
        err_lines = (result.stderr or "").strip().splitlines()[-20:]
        out_lines = (result.stdout or "").strip().splitlines()[-5:]
        msg = f"{script_rel} 退出码 {result.returncode}"
        if err_lines:
            msg += "\n  stderr:\n    " + "\n    ".join(err_lines)
        if out_lines:
            msg += "\n  stdout (tail):\n    " + "\n    ".join(out_lines)
        raise RuntimeError(msg)

    return result.stdout or ""


def main() -> int:
    start_time = time.time()

    print("")
    print("=" * 42)
    print("  🔄 自动训练管道开始")
    print(f"  时间: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print("=" * 42)

    # ── Step 1: 用户数据增强 ─────────────────────────────
    print("")
    print("━━━ [Step 1/4] 用户数据增强（更新匹配对） ━━━")
    try:
        out1 = _run_script("enhance_user_data.py")
    except Exception as e:
        print(f"❌ 用户数据增强失败: {e}")
        print("")
        print("⚠️  管道暂停，等待下次触发")
        print("=" * 42)
        return 1

    print(out1)

    # 提取新增匹配对数用于报告
    new_pairs = ""
    total_pairs = ""
    for line in out1.splitlines():
        m = re.search(r"新生成匹配对.*?(\d+)", line)
        if m:
            new_pairs = m.group(1)
        m = re.search(r"全量用户对.*?(\d+)", line)
        if m:
            total_pairs = m.group(1)

    print(f"✅ Step 1 完成: 新增 {new_pairs or '?'} 匹配对")

    # ── Step 2: 准备训练数据 ────────────────────────────
    print("")
    print("━━━ [Step 2/4] 准备训练数据（V2特征集） ━━━")
    try:
        out2 = _run_script("prepare_v2_training_data.py")
    except Exception as e:
        print(f"❌ 训练数据准备失败: {e}")
        print("")
        print("⚠️  管道暂停，等待下次触发")
        print("=" * 42)
        return 1

    print(out2)

    total_samples = ""
    for line in out2.splitlines():
        m = re.search(r"总样本数.*?(\d+)", line)
        if m:
            total_samples = m.group(1)

    print(f"✅ Step 2 完成: {total_samples or '?'} 训练样本")

    # ── Step 3: 训练匹配模型 ────────────────────────────
    print("")
    print("━━━ [Step 3/4] 训练V2三塔匹配模型 ━━━")
    TIMEOUT_SEC = 55
    print(f"  ⏱️  训练超时保护: {TIMEOUT_SEC}秒")
    try:
        out3 = _run_script("train_matching_model_v2.py", timeout=TIMEOUT_SEC)
    except subprocess.TimeoutExpired:
        print("❌ 模型训练超时 (>55s)，管道暂停")
        print("=" * 42)
        return 1
    except Exception as e:
        print(f"❌ 模型训练失败: {e}")
        print("")
        print("⚠️  管道暂停，等待下次触发")
        print("=" * 42)
        return 1

    print(out3)
    print("✅ Step 3 完成: 模型已保存")

    # ── Step 4: 训练报告 ────────────────────────────────
    print("")
    print("━━━ [Step 4/4] 训练报告摘要 ━━━")

    duration = time.time() - start_time
    duration_min = duration / 60.0

    if REPORT_PATH.is_file():
        print(f"📊 训练报告有效: {REPORT_PATH}")
        try:
            with open(REPORT_PATH, "r", encoding="utf-8") as f:
                r = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"⚠️  报告解析失败: {e}")
            r = {}

        train_m = r.get("metrics", {}).get("train", {})
        val_m = r.get("metrics", {}).get("val", {})
        hist = r.get("training_history", {})

        def _fmt(v, default="N/A"):
            if v is None or v == "N/A":
                return default
            if isinstance(v, (int, float)):
                return f"{v:>10.4f}"
            return f"{str(v):>10s}"

        print(f"  ┌─ 训练集 {'─' * 30}┐")
        print(f"  │  准确率 (Accuracy):  {_fmt(train_m.get('accuracy'))}          │")
        print(f"  │  AUC:               {_fmt(train_m.get('auc'))}          │")
        print(f"  └{'─' * 42}┘")
        print(f"  ┌─ 验证集 {'─' * 30}┐")
        print(f"  │  准确率 (Accuracy):  {_fmt(val_m.get('accuracy'))}          │")
        print(f"  │  AUC:               {_fmt(val_m.get('auc'))}          │")
        print(f"  └{'─' * 42}┘")
        print(f"  训练轮数: {hist.get('epochs_trained', 'N/A')}")
        print(f"  样本总数: {r.get('data_summary', {}).get('total_samples', 'N/A')}")
        print(f"  总耗时:   {duration_min:.1f} 分钟")
    else:
        print("⚠️  训练报告未找到（首次运行或训练失败）")
        print(f"  路径: {REPORT_PATH}")

    print("")
    print("=" * 42)
    print("  ✅ 自动训练管道完成")
    print(f"  时间: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"  总耗时: {duration_min:.1f} 分钟")
    print(f"  新增匹配对: {new_pairs or 'N/A'}")
    print(f"  训练样本: {total_samples or 'N/A'}")
    print("=" * 42)

    return 0


if __name__ == "__main__":
    sys.exit(main())
