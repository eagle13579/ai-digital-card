"""
╔══════════════════════════════════════════════════════════════╗
║                      ⚠️  已 废 弃  ⚠️                         ║
║                                                              ║
║  此文件已废弃，请使用 backend/run.py (端口 8002)              ║
║                                                              ║
║  实际入口: python run.py                                      ║
║  主力入口: backend/run.py → uvicorn 8002                     ║
║                                                              ║
║  本文件仅保留用于向后兼容，新开发请勿引用此文件。             ║
╚══════════════════════════════════════════════════════════════╝
"""
import run  # 实际入口，请使用 python run.py

if __name__ == "__main__":
    print("[DEPRECATED] main.py 已废弃，自动跳转到 run.py (端口8002)")
    import uvicorn
    uvicorn.run(run.app, host="0.0.0.0", port=8002)
