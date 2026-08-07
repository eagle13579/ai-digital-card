#!/usr/bin/env python3
"""disk_watchdog.py — 磁盘空间监控（P2-4 工程健壮性）

每 5 分钟检查磁盘使用率，超过阈值时推送飞书告警（带清理建议）。
幂等：同一告警级别在冷却期内不重复发送（防止刷屏）。

用法:
    python3 disk_watchdog.py            # 单次检查（cron 每5分钟）
"""
from __future__ import annotations

import json
import os
import shutil
import time
import urllib.request
from pathlib import Path

# ── 配置 ──────────────────────────────────────────────────────
THRESHOLD_WARN = 80   # 警告阈值 %
THRESHOLD_CRIT = 90   # 严重阈值 %
COOLDOWN = 3600       # 同级别告警冷却（秒）
STATE_FILE = Path("/var/www/ai-digital-card/backend/data/disk_watchdog_state.json")
MOUNT = "/"

# 飞书 Webhook（从 .env 读取，未配置则尝试 App API 模式）
ENV_FILE = Path("/var/www/ai-digital-card/backend/.env")
# 飞书 App 凭据（API 模式，从环境变量读取；生产环境由 systemd EnvironmentFile 提供）
FEISHU_APP_ID = os.environ.get("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")
FEISHU_CHAT_ID = os.environ.get("FEISHU_HOME_CHANNEL", "")


def load_env() -> dict:
    env: dict[str, str] = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k] = v.strip().strip('"').strip("'")
    # 补充飞书 App 凭据（无默认值，从环境或 .env 读取）
    for k in ("FEISHU_APP_ID", "FEISHU_APP_SECRET", "FEISHU_HOME_CHANNEL"):
        if k in os.environ:
            env[k] = os.environ[k]
    return env


def get_feishu_webhook(env: dict) -> str:
    # 优先从 .env 读 FEISHU_WEBHOOK，其次尝试 bot 配置
    return env.get("FEISHU_WEBHOOK", "") or env.get("LEGION_FEISHU_WEBHOOK", "")


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state), encoding="utf-8")


def get_top_dirs(limit: int = 8) -> str:
    """找磁盘占用大头（供告警附上清理建议）。"""
    dirs = [
        "/var/www", "/opt/hermes-remote/home", "/root/.cache", "/tmp",
        "/root", "/var/log", "/var/cache",
    ]
    results: list[tuple[int, str]] = []
    for d in dirs:
        try:
            if os.path.exists(d):
                size = sum(
                    f.stat().st_size
                    for f in Path(d).rglob("*")
                    if f.is_file() and not os.path.islink(f)
                )
                results.append((size, d))
        except Exception:
            continue
    results.sort(reverse=True)
    lines = [f"  {s / 1024 / 1024:.0f}MB  {p}" for s, p in results[:limit]]
    return "\n".join(lines)


def send_feishu(msg: str, webhook: str) -> bool:
    """发送飞书消息：优先 webhook，其次 App API（tenant_access_token）。"""
    if webhook:
        return _send_via_webhook(msg, webhook)
    return _send_via_api(msg)


def _send_via_webhook(msg: str, webhook: str) -> bool:
    """飞书 webhook 发送。"""
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": "🛡️ 磁盘空间告警"},
                "template": "red",
            },
            "elements": [
                {"tag": "markdown", "content": msg},
            ],
        },
    }
    try:
        req = urllib.request.Request(
            webhook,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            ok = "success" in body or '"code":0' in body
            print(f"[disk_watchdog] 飞书 webhook 推送: {'✅' if ok else '⚠️ ' + body[:200]}")
            return ok
    except Exception as exc:  # noqa: BLE001
        print(f"[disk_watchdog] 飞书 webhook 推送失败: {exc}")
        return False


def _get_tenant_token(env: dict | None = None) -> str | None:
    """用 App 凭据换 tenant_access_token。"""
    env = env or {}
    app_id = env.get("FEISHU_APP_ID") or FEISHU_APP_ID
    app_secret = env.get("FEISHU_APP_SECRET") or FEISHU_APP_SECRET
    if not app_id or not app_secret:
        return None
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = json.dumps({
        "app_id": app_id,
        "app_secret": app_secret,
    }).encode("utf-8")
    try:
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("code") == 0:
            return data.get("tenant_access_token")
        print(f"[disk_watchdog] 获取 token 失败: {data.get('msg')}")
        return None
    except Exception as exc:  # noqa: BLE001
        print(f"[disk_watchdog] 获取 token 异常: {exc}")
        return None


def _send_via_api(msg: str, env: dict | None = None) -> bool:
    """飞书 App API 发送消息到 home_channel。"""
    env = env or {}
    chat_id = env.get("FEISHU_HOME_CHANNEL") or FEISHU_CHAT_ID
    token = _get_tenant_token(env)
    if not token or not chat_id:
        print(f"[disk_watchdog] 告警仅日志（无发送通道）:\n{msg}")
        return False
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
    payload = json.dumps({
        "receive_id": chat_id,
        "msg_type": "interactive",
        "content": json.dumps({
            "header": {
                "title": {"tag": "plain_text", "content": "🛡️ 磁盘空间告警"},
                "template": "red",
            },
            "elements": [
                {"tag": "markdown", "content": msg},
            ],
        }),
    }).encode("utf-8")
    try:
        req = urllib.request.Request(
            url, data=payload,
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Authorization": f"Bearer {token}",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        ok = data.get("code") == 0
        print(f"[disk_watchdog] 飞书 API 推送: {'✅' if ok else '⚠️ ' + str(data.get('msg'))}")
        return ok
    except Exception as exc:  # noqa: BLE001
        print(f"[disk_watchdog] 飞书 API 推送失败: {exc}")
        return False


def main() -> int:
    usage = shutil.disk_usage(MOUNT)
    percent = usage.used / usage.total * 100
    free_gb = usage.free / 1024 / 1024 / 1024

    env = load_env()
    webhook = get_feishu_webhook(env)
    state = load_state()

    level = None
    if percent >= THRESHOLD_CRIT:
        level = "CRIT"
    elif percent >= THRESHOLD_WARN:
        level = "WARN"

    if level is None:
        # 正常状态静默（no_agent cron: 空输出=不推送，避免每5分钟刷屏）
        return 0

    # 冷却期检查
    last = state.get(f"last_{level}", 0)
    now = time.time()
    if now - last < COOLDOWN:
        print(f"[disk_watchdog] {level} 冷却中（{COOLDOWN - (now - last):.0f}s 后再次告警）")
        return 0

    msg = (
        f"**磁盘使用率 {percent:.1f}%**（剩余 {free_gb:.1f}G）\n"
        f"阈值: WARN≥{THRESHOLD_WARN}% / CRIT≥{THRESHOLD_CRIT}%\n\n"
        f"**占用大户：**\n{get_top_dirs()}\n\n"
        f"**建议：**\n"
        f"  1. 清理构建缓存: `rm -rf /root/.cache/* /var/cache/apt/archives/*`\n"
        f"  2. 清理旧日志: `journalctl --vacuum-size=100M`\n"
        f"  3. 检查 /tmp 大文件"
    )

    sent = send_feishu(msg, webhook)
    if sent or not webhook:
        state[f"last_{level}"] = now
        save_state(state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
