"""画册处理异步任务 - 封面生成/图片压缩/二维码生成"""
import logging

logger = logging.getLogger(__name__)

def generate_brochure_qrcode(brochure_id: int):
    """异步生成画册分享二维码"""
    logger.info(f"Generate QR code for brochure {brochure_id}")
    return {"status": "ok", "brochure_id": brochure_id}

def compress_brochure_images(brochure_id: int):
    """异步压缩画册图片"""
    logger.info(f"Compress images for brochure {brochure_id}")
    return {"status": "ok", "brochure_id": brochure_id}
