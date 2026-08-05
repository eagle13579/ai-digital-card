"""AI名片启动包装器 — 修复SQLAlchemy Python 3.14兼容性问题"""
import subprocess
import sys
import os

# 升级 SQLAlchemy 到兼容版本
print("[启动器] 检查 SQLAlchemy 版本...")
try:
    import sqlalchemy
    ver = sqlalchemy.__version__
    print(f"[启动器] 当前 SQLAlchemy: {ver}")
    
    ver_parts = [int(x) for x in ver.split(".")]
    if ver_parts[0] == 2 and ver_parts[1] == 0 and ver_parts[2] <= 35:
        print("[启动器] Python 3.14 兼容性修复: 升级 SQLAlchemy...")
        r = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "sqlalchemy"],
            capture_output=True, text=True, timeout=60
        )
        if r.returncode == 0:
            print(f"[启动器] SQLAlchemy 升级成功")
        else:
            print(f"[启动器] SQLAlchemy 升级失败: {r.stderr[-200:]}")
            # 回退: 使用 importlib 重新加载
except ImportError:
    pass
except Exception as e:
    print(f"[启动器] SQLAlchemy 检查异常: {e}")

# 启动主程序
print("[启动器] 启动 AI名片 main.py...")
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 使用 exec 运行 main.py
with open("main.py", encoding="utf-8") as f:
    code = f.read()
exec(code, {"__name__": "__main__", "__file__": os.path.abspath("main.py")})
