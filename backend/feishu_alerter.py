#!/usr/bin/env python3
"""
Server-side 飞书 alerting agent for health_monitor.py failures.

Reads the health_alerts.log and sends 飞书 bot notifications for CRITICAL alerts.
Configure via ENV: FEISHU_WEBHOOK_URL (or file /etc/ai-digital-card/feishu_webhook.txt)
"""

import json
import os
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone

LOG_FILE = "/var/log/ai-digital-card/health_alerts.log"
WEBHOOK_FILE = "/etc/ai-digital-card/feishu_webhook.txt"


def _load_webhook() -> str | None:
    """Load 飞书 webhook URL from env var or config file."""
    url = os.environ.get("FEISHU_WEBHOOK_URL")
    if url:
        return url.strip()
    if os.path.isfile(WEBHOOK_FILE):
        with open(WEBHOOK_FILE) as f:
            return f.read().strip()
    return None


def _send_feishu_alert(title: str, content: str) -> bool:
    """Send a 飞书 message via webhook."""
    webhook = _load_webhook()
    if not webhook:
        print("⚠️  No 飞书 webhook configured — alert not sent", flush=True)
        return False

    payload = json.dumps({
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": title,
                    "content": [[{"tag": "text", "text": content}]]
                }
            }
        }
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            webhook,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode()
            print(f"✅  飞书 alert sent: {resp.status}", flush=True)
            return True
    except Exception as exc:
        print(f"❌  Failed to send 飞书 alert: {exc}", flush=True)
        return False


def check_and_alert() -> str:
    """Read recent health_alerts.log and send alerts for CRITICAL failures."""
    if not os.path.isfile(LOG_FILE):
        return "ℹ️  No health alert log found"

    # Read the last 50 lines
    with open(LOG_FILE) as f:
        lines = f.readlines()

    # Find CRITICAL alerts (not just WARNING)
    critical = []
    for line in lines:
        if "CRITICAL" in line:
            critical.append(line.strip())

    if not critical:
        # Check for any recent WARNING (within last 60 minutes might be interesting)
        now = datetime.now(timezone.utc)
        recent_warnings = []
        for line in lines:
            if "WARNING" in line:
                recent_warnings.append(line.strip())
        if recent_warnings:
            recent = recent_warnings[-5:]  # last 5 warnings
            msg = f"⚠️  No CRITICAL alerts found. Last {len(recent)} warnings:\n" + "\n".join(recent)
        else:
            msg = "✅  健康检查全部正常"
        _send_feishu_alert("✅ 服务健康检查", msg)
        return msg

    # Send alerts for critical failures
    msg = f"🚨 发现 {len(critical)} 条严重告警:\n" + "\n".join(critical[-10:])
    title = f"🚨 {len(critical)}条严重告警"
    _send_feishu_alert(title, msg)
    return msg


def main():
    result = check_and_alert()
    print(result, flush=True)


if __name__ == "__main__":
    main()
