#!/usr/bin/env python3
"""AI数字名片 生产健康检查 — 供cronjob调度
检查: 8201端口 + 关键API + 系统日志
"""
import subprocess, json, sys, os
from datetime import datetime

PROD_HOST = os.getenv("PROD_HOST", "47.116.116.87")
PROD_USER = os.getenv("PROD_USER", "root")
SSH_KEY = os.getenv("SSH_KEY_PATH", "/root/.ssh/id_rsa")

issues = []

def ssh(cmd):
    try:
        r = subprocess.run(
            ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
             "-i", SSH_KEY, f"{PROD_USER}@{PROD_HOST}", cmd],
            capture_output=True, text=True, timeout=20
        )
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except Exception as e:
        return -1, "", str(e)

def check_http(url):
    try:
        r = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--max-time", "10", url],
            capture_output=True, text=True, timeout=15
        )
        return r.stdout.strip()
    except:
        return "000"

# 1. Check service status
rc, out, err = ssh("systemctl is-active ai-digital-card")
if rc == 0:
    status = out.strip()
    if status != "active":
        issues.append({"severity": "CRITICAL", "check": "systemctl status", "detail": f"Service is {status}, not active"})
else:
    issues.append({"severity": "CRITICAL", "check": "SSH", "detail": f"SSH failed: {err[:100]}"})

# 2. Check port 8201
rc, out, err = ssh("ss -tlnp | grep 8201")
if rc != 0 or not out:
    issues.append({"severity": "CRITICAL", "check": "port_8201", "detail": "Port 8201 not listening"})

# 3. Check via public domain
code = check_http("https://card.liankebao.top/api/health")
if code not in ("200", "401"):
    issues.append({"severity": "WARNING", "check": "public_API_health", "detail": f"card.liankebao.top/api/health returned {code}"})

# 4. Check JWT endpoint
code = check_http("https://liankebao.top/api/auth/health")
if code not in ("200", "401", "404"):
    issues.append({"severity": "WARNING", "check": "public_auth", "detail": f"auth health returned {code}"})

# Output
report = {
    "timestamp": datetime.utcnow().isoformat(),
    "status": "HEALTHY" if not issues else "ISSUES_FOUND",
    "issues_count": len(issues),
    "issues": issues
}
print(json.dumps(report, indent=2, ensure_ascii=False))

if issues:
    sys.exit(1)
