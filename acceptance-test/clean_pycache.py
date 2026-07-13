"""Clean all __pycache__ directories in backend"""
import shutil, os, glob
backend = r"D:\AI数智名片\backend"
count = 0
for p in glob.glob(backend + "/**/__pycache__", recursive=True):
    if os.path.isdir(p):
        shutil.rmtree(p)
        count += 1
print(f"CLEANED {count} __pycache__ dirs")
