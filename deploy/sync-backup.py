#!/usr/bin/env python3
"""AI数字名片 备份同步脚本
每天执行：从服务器拉取最新备份到本地
配合 cri 3:30 AM 服务器备份 + cron 4:00 AM 本地拉取
"""
import subprocess, os, sys
from datetime import datetime

REMOTE = "root@47.116.116.87"
REMOTE_PATH = "/var/www/ai-digital-card/backend/data/backups/"
LOCAL_DIR = "D:\\AI数智名片\\backups"

ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log(msg):
    print(f"[{ts}] {msg}")

def main():
    # 确保本地目录存在
    os.makedirs(LOCAL_DIR, exist_ok=True)

    # 通过SSH获取远程备份文件列表，找最新的
    cmd = f"ssh {REMOTE} 'ls -t {REMOTE_PATH}digital_brochure_*.db.gz 2>/dev/null | head -3'"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
    
    if result.returncode != 0 or not result.stdout.strip():
        log("❌ 远程无备份文件或连接失败")
        return False

    files = result.stdout.strip().split("\n")
    log(f"发现 {len(files)} 个远程备份文件")

    for fname in files:
        fname = fname.strip()
        if not fname:
            continue
        local_path = os.path.join(LOCAL_DIR, os.path.basename(fname))
        
        # 如果本地已有同名文件，跳过
        if os.path.exists(local_path):
            log(f"⏭ 已存在: {os.path.basename(fname)}")
            continue
        
        # SCP拉取
        scp_cmd = f"scp {REMOTE}:{fname} \"{local_path}\""
        ret = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True, timeout=60)
        
        if ret.returncode == 0:
            size = os.path.getsize(local_path)
            log(f"✅ 已拉取: {os.path.basename(fname)} ({size/1024:.0f}KB)")
        else:
            log(f"❌ 拉取失败: {fname}")

    # 删除本地30天前的备份
    import time
    now = time.time()
    for f in os.listdir(LOCAL_DIR):
        fpath = os.path.join(LOCAL_DIR, f)
        if os.path.isfile(fpath) and f.endswith('.db.gz'):
            if now - os.path.getmtime(fpath) > 30 * 86400:
                os.remove(fpath)
                log(f"🧹 删除旧备份: {f}")

    log("✅ 同步完成")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
