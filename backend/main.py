"""
⚠️ 此文件已废弃，请使用 run.py (端口8002)
实际入口：python run.py
"""
import run  # 实际入口，请使用 python run.py

if __name__ == "__main__":
    print("[WARNING] main.py 已废弃，自动跳转到 run.py (端口8002)")
    import uvicorn
    uvicorn.run(run.app, host="0.0.0.0", port=8002)
