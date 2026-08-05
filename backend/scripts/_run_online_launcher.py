"""临时启动器 — 修复 sys.path 冲突后执行在线学习"""
import sys
import os
import site

# 手动加载 site-packages（因为 -S 禁用了自动加载）
venv_base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".venv")
venv_site = os.path.join(venv_base, "Lib", "site-packages")
if os.path.isdir(venv_site) and venv_site not in sys.path:
    sys.path.insert(0, venv_site)

# 确保 backend 根目录在 path 上
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.chdir(backend_dir)

# 直接调用原始脚本
script_path = os.path.join(backend_dir, "scripts", "run_online_learning.py")
exec(compile(open(script_path).read(), script_path, 'exec'))
