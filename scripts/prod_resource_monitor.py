#!/usr/bin/env python3
"""AI数字名片 生产资源监控 — 磁盘/内存/CPU/服务"""
import subprocess, json, os, sys
from datetime import datetime

HOST = os.getenv("PROD_HOST", "47.116.116.87")
USER = os.getenv("PROD_USER", "root")

def ssh(cmd):
    try:
        r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
            f"{USER}@{HOST}", cmd], capture_output=True, text=True, timeout=20)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except Exception as e:
        return -1, "", str(e)

issues = []

# 1. 磁盘
rc, out, _ = ssh("df -h / | tail -1")
if rc == 0 and out:
    parts = out.split()
    pct = parts[4].rstrip('%') if len(parts) >= 5 else '0'
    used_gb = parts[2] if len(parts) >= 3 else '?'
    pct_int = int(pct)
    if pct_int >= 85:
        issues.append({"severity": "CRITICAL", "check": "disk", "detail": f"磁盘使用率 {pct}% ({used_gb})"})
    elif pct_int >= 75:
        issues.append({"severity": "WARNING", "check": "disk", "detail": f"磁盘使用率 {pct}% ({used_gb})"})

# 2. 内存
rc, out, _ = ssh("free -m | grep Mem")
if rc == 0 and out:
    parts = out.split()
    total = int(parts[1])
    avail = int(parts[-1])
    used_pct = round((total - avail) / total * 100, 1)
    if used_pct >= 85:
        issues.append({"severity": "CRITICAL", "check": "memory", "detail": f"内存使用率 {used_pct}%"})
    elif used_pct >= 75:
        issues.append({"severity": "WARNING", "check": "memory", "detail": f"内存使用率 {used_pct}%"})

# 3. 8201服务
rc, out, _ = ssh("ss -tlnp | grep 8201")
if rc != 0 or not out:
    issues.append({"severity": "CRITICAL", "check": "service_8201", "detail": "8201端口未监听"})

# 4. 8000服务
rc, out, _ = ssh("ss -tlnp | grep 8000")
if rc != 0 or not out:
    issues.append({"severity": "CRITICAL", "check": "service_8000", "detail": "8000端口未监听"})

# 5. Load average
rc, out, _ = ssh("cat /proc/loadavg | cut -d' ' -f1-3")
if rc == 0 and out:
    loads = out.split()
    if loads and float(loads[0]) > 5:
        issues.append({"severity": "WARNING", "check": "load", "detail": f"负载: {out}"})

report = {
    "timestamp": datetime.utcnow().isoformat(),
    "status": "HEALTHY" if not issues else "ISSUES_FOUND",
    "issues_count": len(issues),
    "issues": issues
}
print(json.dumps(report, indent=2, ensure_ascii=False))

if issues:
    sys.exit(1)
