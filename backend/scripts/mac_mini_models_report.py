#!/usr/bin/env python3
"""Mac mini 模型状态上报脚本 (v2.0 — HTTP 直传版)

用途: 将 Mac mini 上运行的 MLX 推理模型列表上报到服务器
通道: HTTPS POST → https://card.liankebao.top/api/v1/trust/mac-status
       (nginx 反代 → AI数智名片 8201 → data/mac_mini/models_status.json)

v2.0 改进: 不再依赖 git push / 仓库目录 / git 凭据。Mac 只需能访问公网
           （服务器 443 端口），脚本自动完成采集+上报。

运行环境: Mac mini (macOS, Python 3.9+)
运行方式:
  手动:  python3 mac_mini_models_report.py
  定时:  crontab -e 添加:
         */30 * * * * /usr/bin/python3 /path/to/mac_mini_models_report.py >> /tmp/mac_mini_report.log 2>&1

依赖: 无 (纯标准库)
"""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone

# ── 配置 ──────────────────────────────────────────────────────────────────
MLX_API_URL = os.environ.get("MLX_API_URL", "http://127.0.0.1:9091/v1/models")
REPORT_URL = os.environ.get(
    "REPORT_URL", "https://card.liankebao.top/api/v1/trust/mac-status"
)
REPORT_TOKEN = os.environ.get("MAC_REPORT_TOKEN", "mac-mini-report-2026")
TIMEOUT = 10
# ─────────────────────────────────────────────────────────────────────────


def fetch_mlx_models() -> list[dict]:
    """查询 MLX 推理服务 :9091 的模型列表"""
    try:
        req = urllib.request.Request(MLX_API_URL, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
        return data.get("data", data if isinstance(data, list) else [])
    except Exception as exc:
        return [{"error": str(exc), "note": "MLX 服务不可达(可能未启动)"}]


def get_system_info() -> dict:
    """采集 Mac mini 基础信息"""
    info = {"hostname": socket.gethostname()}
    for cmd, key in (
        (["sysctl", "-n", "machdep.cpu.brand_string"], "cpu"),
        (["sysctl", "-n", "hw.memsize"], "memory_raw"),
        (["sw_vers", "-productVersion"], "macos"),
    ):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                val = r.stdout.strip()
                if key == "memory_raw":
                    info["memory_gb"] = round(int(val) / (1024**3), 1)
                else:
                    info[key] = val
        except Exception:
            pass
    return info


def report(payload: dict) -> bool:
    """POST 到服务器接收端点"""
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        REPORT_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Mac-Token": REPORT_TOKEN,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            resp_body = resp.read().decode()
            print(f"✅ 上报成功: HTTP {resp.status} — {resp_body}")
            return True
    except Exception as exc:
        print(f"❌ 上报失败: {exc}")
        return False


def main() -> int:
    models = fetch_mlx_models()
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "device": "Mac mini",
        "system": get_system_info(),
        "mlx_endpoint": MLX_API_URL,
        "model_count": len([m for m in models if not m.get("error")]),
        "models": models,
    }
    ok = report(payload)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
