#!/usr/bin/env python3
"""本地Windows执行: SSH探测Mac + 部署上报代理 (v1.0)

由 8799 API start_cmd 触发 (简单命令: python ssh_probe_deploy.py)
作用:
  1. 探测本地能否 ssh 到 Mac mini (eagle@192.168.1.233)
  2. 若能: 下载上报脚本到 Mac + 注册 crontab + 立即跑一次
  3. 写结果到 probe_result.txt (供 health_check 探测)
"""
import subprocess
import sys
import time

MAC_HOST = "eagle@192.168.1.233"
AGENT_DIR = "/Users/eagle/mac-report-agent"
SCRIPT_URL = "https://raw.githubusercontent.com/eagle13579/ai-digital-card/feature/trust-engine-merge/backend/scripts/mac_mini_models_report.py"

lines = []


def log(msg):
    lines.append(msg)
    print(msg)


def run(cmd, timeout=60):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or "")[:200], (r.stderr or "")[:200]
    except Exception as e:
        return -1, "", str(e)[:200]


def main():
    log("=== SSH 探测部署脚本启动 ===")

    # 1. 探测 ssh 连通性 (BatchMode=无交互, 失败立即返回)
    rc, out, err = run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8",
         "-o", "StrictHostKeyChecking=no", MAC_HOST, "echo SSH_OK"], timeout=20)
    if rc == 0 and "SSH_OK" in out:
        log(f"✅ SSH 免密可用: {MAC_HOST}")
    else:
        log(f"❌ SSH 不可用 rc={rc}")
        log(f"   stderr: {err[:150]}")
        _write_result("SSH_FAIL: " + err[:100])
        return 1

    # 2. 部署脚本到 Mac
    rc, out, err = run(
        ["ssh", MAC_HOST, f"mkdir -p {AGENT_DIR} && curl -fsSL '{SCRIPT_URL}' -o {AGENT_DIR}/mac_mini_models_report.py && chmod +x {AGENT_DIR}/mac_mini_models_report.py && echo DEPLOY_OK"], timeout=60)
    if "DEPLOY_OK" in out:
        log("✅ 脚本已部署到 Mac")
    else:
        log(f"❌ 脚本部署失败 rc={rc} err={err[:150]}")
        _write_result("DEPLOY_FAIL: " + err[:100])
        return 1

    # 3. 注册 crontab (每30分钟)
    cron_cmd = (
        f"(crontab -l 2>/dev/null | grep -v mac_mini_models_report; "
        f"echo '*/30 * * * * /usr/bin/python3 {AGENT_DIR}/mac_mini_models_report.py >> /Users/eagle/mac_mini_report.log 2>&1') | crontab -"
    )
    rc, out, err = run(["ssh", MAC_HOST, cron_cmd], timeout=30)
    rc2, out2, err2 = run(["ssh", MAC_HOST, "crontab -l | grep mac_mini_models_report"], timeout=15)
    if rc2 == 0 and "mac_mini_models_report" in out2:
        log("✅ crontab 已注册 (每30分钟)")
    else:
        log(f"⚠️ crontab 注册可能失败: {out2[:100]} {err2[:100]}")

    # 4. 立即手动跑一次
    rc, out, err = run(
        ["ssh", MAC_HOST, f"/usr/bin/python3 {AGENT_DIR}/mac_mini_models_report.py"], timeout=60)
    log(f"✅ 立即执行: rc={rc} 输出={out[:120]}")

    _write_result("SUCCESS: agent deployed + crontab registered + first run done")
    return 0


def _write_result(msg):
    with open("probe_result.txt", "w") as f:
        f.write(msg + "\n" + "\n".join(lines[-5:]))


if __name__ == "__main__":
    sys.exit(main())
