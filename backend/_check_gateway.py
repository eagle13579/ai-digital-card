#!/usr/bin/env python3
"""Check websockets version and verify we can start the gateway."""
import subprocess, os, sys

venv_python = r"C:\Users\56867\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe"

# 1. Check websockets version
r = subprocess.run(
    [venv_python, "-c", "import websockets; print('websockets:', websockets.__version__)"],
    capture_output=True, text=True, timeout=10
)
print(r.stdout.strip())
if r.stderr:
    print(f"STDERR: {r.stderr[:200]}")

# 2. Check lark_oapi version
r = subprocess.run(
    [venv_python, "-c", "import lark_oapi; print('lark_oapi:', lark_oapi.__version__)"],
    capture_output=True, text=True, timeout=10
)
print(r.stdout.strip())

# 3. Check if .env has GATEWAY_ALLOW_ALL_USERS
env_file = r"D:\向海容的知识库\wiki\wiki\记忆宫殿\profiles\automation\.env"
if os.path.isfile(env_file):
    with open(env_file, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    for kw in ['GATEWAY_ALLOW_ALL_USERS', 'FEISHU_APP_ID', 'FEISHU_APP_SECRET', 'FEISHU_DOMAIN']:
        found = kw in content
        print(f"  {kw}: {'✅' if found else '❌'}")

# 4. Check for existing gateway lock
lock_file = r"D:\向海容的知识库\wiki\wiki\记忆宫殿\profiles\automation\.gateway.lock"
if os.path.isfile(lock_file):
    with open(lock_file, 'r') as f:
        print(f"  🔒 Gateway lock exists: {f.read().strip()}")
else:
    print("  ✅ No gateway lock file")

# 5. Check config.yaml feishu section
config_file = r"D:\向海容的知识库\wiki\wiki\记忆宫殿\profiles\automation\config.yaml"
if os.path.isfile(config_file):
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
    # Find feishu section
    in_feishu = False
    for line in content.split('\n'):
        if 'feishu' in line.lower() and ':' in line and not line.startswith(' '):
            in_feishu = True
        elif in_feishu and not line.startswith(' ' * 2) and line.strip():
            # Check if platforms section
            if 'platforms' in line.lower() or '#' in line[:4]:
                continue
            in_feishu = False
        if in_feishu:
            s = line.strip()
            if s:
                print(f"  config: {s}")
