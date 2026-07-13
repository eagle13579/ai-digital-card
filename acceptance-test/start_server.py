"""Start server with port retry"""
import time, subprocess, sys, os

for attempt in range(5):
    p = subprocess.Popen(
        [sys.executable, '-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '8201'],
        cwd=r'D:\AI数智名片\backend',
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE
    )
    time.sleep(3)
    # Check if it's listening
    import socket
    s = socket.socket()
    r = s.connect_ex(('localhost', 8201))
    s.close()
    if r == 0:
        print(f"SERVER STARTED OK (attempt {attempt+1})")
        sys.exit(0)
    # Check stderr
    stderr = p.stderr.read().decode('utf-8', errors='replace')
    if 'address already in use' in stderr.lower():
        print(f"Port busy, waiting... (attempt {attempt+1})")
        p.kill()
        time.sleep(5)
    else:
        print(f"UNKNOWN ERROR: {stderr[:200]}")
        p.kill()
        break

print("FAILED TO START")
sys.exit(1)
