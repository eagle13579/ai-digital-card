#!/usr/bin/env python3
"""Mac mini 状态接收器 (服务器侧 v1.0)

从 GitHub 远端拉取 Mac mini 上报的模型状态文件，校验后写入本地接收目录。
配合 Mac 侧 mac_mini_models_report.py 使用（Mac 推送 → 本脚本拉取）。

cron: */30 * * * * (no_agent, 静默正常=无更新)
"""
import json
import os
import subprocess
import sys

REPO_DIR = "/var/www/ai-digital-card"
MAC_REL = "backend/data/mac_mini/models_status.json"
LOCAL_OUT = os.path.join(REPO_DIR, "backend/data/mac_mini/models_status.json")


def git_pull() -> str:
    """拉取远端（优先 main，回退 dev/develop）"""
    for branch in ("main", "dev", "develop"):
        r = subprocess.run(
            ["git", "-C", REPO_DIR, "fetch", "origin", branch],
            capture_output=True, text=True, timeout=60,
        )
        if r.returncode == 0:
            subprocess.run(
                ["git", "-C", REPO_DIR, "checkout", branch],
                capture_output=True, text=True, timeout=30,
            )
            subprocess.run(
                ["git", "-C", REPO_DIR, "pull", "origin", branch, "--ff-only"],
                capture_output=True, text=True, timeout=60,
            )
            return branch
    return ""


def main() -> int:
    if not os.path.exists(LOCAL_OUT):
        branch = git_pull()
        if branch:
            print(f"✅ 已拉取 {branch}, 检查 Mac mini 状态...")
        else:
            print("⚠️ 无法拉取远端")
            return 1
    if not os.path.exists(LOCAL_OUT):
        # 无上报文件 = 正常（Mac 侧尚未配置），静默
        return 0
    try:
        data = json.load(open(LOCAL_OUT))
        count = data.get("model_count", 0)
        generated = data.get("generated_at", "?")
        host = data.get("system", {}).get("hostname", "?")
        if data.get("device") != "Mac mini":
            return 0  # 非预期文件，忽略
        # 有内容才输出（no_agent 静默模式）
        models = [m.get("id", "?") for m in data.get("models", []) if not m.get("error")]
        print(f"✅ Mac mini 模型状态: {count} 个模型 | 生成于 {generated} | {host}")
        if models:
            print("   模型: " + ", ".join(models[:15]))
        else:
            errs = [m.get("error", "?") for m in data.get("models", []) if m.get("error")]
            if errs:
                print(f"   ⚠️ MLX 服务未就绪: {errs[0][:80]}")
    except Exception as exc:
        print(f"⚠️ Mac mini 状态文件解析失败: {exc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
