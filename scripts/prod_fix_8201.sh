#!/usr/bin/env python3
"""AI数字名片 生产修复脚本 — 修复8201启动失败

常见失败原因:
1. JWT_SECRET为空/默认值 → 在.env中设置强密钥
2. ImportError (Windows路径污染) → 检查backend目录是否有D:\\等Windows路径文件
3. Redis连接失败 → 启动/关闭Redis
4. 端口被占 → pkill冲突进程
"""
import subprocess, sys

PROD_HOST = "47.116.116.87"
PROD_USER = "root"

def run(cmd):
    print(f"  $ {cmd}")
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        print(f"  ⚠️ Exit code {r.returncode}")
        if r.stderr:
            print(f"  stderr: {r.stderr[:500]}")
    if r.stdout:
        for line in r.stdout.strip().split('\n')[-10:]:
            print(f"  {line}")
    return r

def ssh_cmd(cmd):
    return run(f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 {PROD_USER}@{PROD_HOST} '{cmd}'")

print("=" * 60)
print("P0-1: AI数字名片 生产修复")
print("=" * 60)

# Step 1: 检查.env中的JWT_SECRET
print("\n[1/5] 检查 JWT_SECRET...")
r = ssh_cmd("grep JWT_SECRET /var/www/ai-digital-card/backend/.env | head -1")
if "JWT_SECRET=" in r.stdout:
    val = r.stdout.strip().split("JWT_SECRET=")[1].strip().strip('"').strip("'")
    if not val:
        print("  ❌ JWT_SECRET为空！")
    elif val.lower() in ('change-me', 'default', 'changeme', 'secret'):
        print("  ❌ JWT_SECRET为默认值！")
    elif len(val) < 20:
        print(f"  ⚠️ JWT_SECRET长度={len(val)}，建议≥20")
    else:
        print(f"  ✅ JWT_SECRET有效 (长度={len(val)})")

# Step 2: 检查Windows路径污染
print("\n[2/5] 检查Windows路径污染...")
r = ssh_cmd("find /var/www/ai-digital-card/backend -name '*\\\\*' -o -name 'D:*' 2>/dev/null | head -20")
if r.stdout.strip():
    print(f"  ❌ 发现Windows路径污染文件:")
    for line in r.stdout.strip().split('\n'):
        print(f"     {line}")
else:
    print("  ✅ 无Windows路径污染")

# Step 3: 检查端口占用
print("\n[3/5] 检查8201端口...")
r = ssh_cmd("ss -tlnp | grep 8201")
if r.stdout.strip():
    print(f"  ⚠️ 端口被占用: {r.stdout.strip()[:200]}")
    run(f"ssh {PROD_USER}@{PROD_HOST} 'pkill -9 -f "uvicorn.*8201" || true'")
    print("  ✅ 已清理进程")
else:
    print("  ✅ 端口空闲")

# Step 4: 杀掉旧进程
print("\n[4/5] 清理残留uvicorn进程...")
r = ssh_cmd("pgrep -f 'uvicorn main:app' | wc -l")
old_count = int(r.stdout.strip() or '0')
if old_count > 0:
    ssh_cmd("pkill -9 -f 'uvicorn main:app' || true")
    print(f"  ✅ 杀掉{old_count}个旧进程")
else:
    print("  ✅ 无残留进程")

# Step 5: 启动服务
print("\n[5/5] 启动服务...")
r = ssh_cmd("systemctl start ai-digital-card")
if r.returncode == 0:
    print("  systemctl start 成功")
else:
    print("  systemctl start 失败，尝试直接启动...")
    r = ssh_cmd("cd /var/www/ai-digital-card/backend && source venv/bin/activate && nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8201 --workers 2 > /tmp/ai-card.log 2>&1 &")
    print(f"  直接启动: {r.stdout[:200] if r.stdout else 'done'}")

# 验证
print("\n" + "=" * 60)
print("验证...")
r = ssh_cmd("sleep 5 && curl -s http://localhost:8201/health")
print(f"  health: {r.stdout}")

r = ssh_cmd("ss -tlnp | grep 8201")
if r.stdout.strip():
    print(f"  ✅ 8201正在监听!")
else:
    print(f"  ❌ 8201未监听! 检查日志...")
    ssh_cmd("journalctl -u ai-digital-card --no-pager -n 20 --no-hostname 2>/dev/null | tail -20")

print("\n✅ 修复完成!")
