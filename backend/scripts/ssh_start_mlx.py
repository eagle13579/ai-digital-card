#!/usr/bin/env python3
"""ssh_start_mlx.py — 通过 Windows 跳板 SSH 到 Mac mini 启动 MLX 推理服务 (v1.0)

由 8799 API start_cmd 自举触发 (简单命令: python ssh_start_mlx.py)
流程:
  1. SSH 到 Mac mini (eagle@192.168.1.233)
  2. 检查 MLX 服务 (127.0.0.1:9091) 是否已运行
  3. 未运行则 nohup 启动 mlx_lm.server --port 9091
  4. 等待就绪并验证 /v1/models
  5. 写结果到 mlx_start_result.txt (供 health_check 行为验证)
"""
import subprocess
import sys
import time

MAC_HOST = "eagle@192.168.1.233"
CHECK_CMD = "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:9091/v1/models"
# 启动命令: nohup 后台运行 + 日志落盘
START_CMD = (
    "mkdir -p ~/mlx_serve && cd ~/mlx_serve && "
    "nohup python3 -m mlx_lm.server --model Qwen/Qwen2.5-0.5B-Instruct --port 9091 "
    "> ~/mlx_serve/server.log 2>&1 & echo STARTED_PID=$!"
)
VERIFY_CMD = "curl -s http://127.0.0.1:9091/v1/models | head -c 500"


def ssh(cmd, timeout=60):
    try:
        r = subprocess.run(
            ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
             "-o", "StrictHostKeyChecking=no", MAC_HOST, cmd],
            capture_output=True, text=True, timeout=timeout,
        )
        return r.returncode, (r.stdout or "")[:300], (r.stderr or "")[:200]
    except Exception as e:
        return -1, "", str(e)[:200]


def main():
    lines = []

    def log(msg):
        lines.append(msg)
        print(msg)

    log("=== SSH 启动 MLX 服务脚本 ===")

    # 1. 探测 SSH 连通
    rc, out, err = ssh("echo SSH_OK", timeout=20)
    if rc == 0 and "SSH_OK" in out:
        log("✅ SSH 免密可用: " + MAC_HOST)
    else:
        log(f"❌ SSH 不可用 rc={rc} err={err[:150]}")
        _write(lines, f"SSH_FAIL: {err[:100]}")
        return 1

    # 2. 检查 MLX 是否已在运行
    rc, out, err = ssh(CHECK_CMD, timeout=20)
    if rc == 0 and out.strip().startswith("200"):
        log("✅ MLX 服务已在运行 (9091)")
        rc2, out2, _ = ssh(VERIFY_CMD, timeout=20)
        log("模型列表: " + out2[:200])
        _write(lines, f"ALREADY_RUNNING: {out2[:200]}")
        return 0

    log("MLX 未运行，正在启动...")

    # 3. 启动 MLX 服务 (nohup 后台)
    rc, out, err = ssh(START_CMD, timeout=30)
    log(f"启动命令 rc={rc} 输出={out[:120]}")
    if rc != 0 and "STARTED_PID" not in out:
        log(f"⚠️ 启动可能失败 err={err[:120]}")

    # 4. 等待就绪 (最长 90 秒, 模型加载需要时间)
    for i in range(9):
        time.sleep(10)
        rc, out, err = ssh(CHECK_CMD, timeout=20)
        if rc == 0 and out.strip().startswith("200"):
            rc2, out2, _ = ssh(VERIFY_CMD, timeout=20)
            log(f"🎉 MLX 服务就绪! (等待 {i+1}0s)")
            log("模型: " + out2[:300])
            _write(lines, f"STARTED_OK: {out2[:300]}")
            return 0
        log(f"  等待模型加载... ({i+1}/9)")

    log("⚠️ 超时未就绪，查看日志...")
    rc, out, err = ssh("tail -30 ~/mlx_serve/server.log 2>/dev/null", timeout=20)
    log("服务端日志: " + out[:300])
    _write(lines, f"START_TIMEOUT: {out[:200]}")
    return 1


def _write(lines, msg):
    with open("mlx_start_result.txt", "w") as f:
        f.write(msg + "\n" + "\n".join(lines[-8:]))


if __name__ == "__main__":
    sys.exit(main())
