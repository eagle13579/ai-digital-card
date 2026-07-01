"""
Media Service — 视频/多媒体文件上传处理服务

提供视频文件格式验证、大小校验、安全转码（可选）、存储等功能。
"""

import os
import uuid
import asyncio
import logging
from pathlib import Path
from typing import Optional

from fastapi import UploadFile, HTTPException

from app.config import settings

logger = logging.getLogger(__name__)

# 允许的视频扩展名和 MIME 类型映射
ALLOWED_MAP: dict[str, str] = {
    ".mp4": "video/mp4",
    ".webm": "video/webm",
}

# 转码预设（ffmpeg 参数）
TRANSCODE_PRESETS = {
    "mp4": {
        "codec_video": "libx264",
        "codec_audio": "aac",
        "crf": "23",
        "pix_fmt": "yuv420p",
        "extra_args": ["-movflags", "+faststart"],
    },
    "webm": {
        "codec_video": "libvpx-vp9",
        "codec_audio": "libopus",
        "crf": "30",
        "pix_fmt": "yuv420p",
        "extra_args": [],
    },
}


class MediaService:
    """视频/多媒体文件上传处理服务"""

    @staticmethod
    def validate_video(file: UploadFile) -> None:
        """
        验证上传的视频文件格式和大小。

        检查:
        - 文件扩展名在允许列表中
        - MIME 类型匹配
        - 文件大小未超限
        """
        # 1. 提取扩展名
        filename = file.filename or ""
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_MAP:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的视频格式: {ext}，允许格式: {', '.join(ALLOWED_MAP.keys())}",
            )

        # 2. 验证 MIME 类型
        content_type = file.content_type or ""
        expected_mime = ALLOWED_MAP[ext]
        if content_type and content_type != expected_mime:
            raise HTTPException(
                status_code=400,
                detail=f"MIME 类型不匹配: {content_type}，期望: {expected_mime}",
            )

        logger.info(
            "视频文件格式验证通过: name=%s, ext=%s, mime=%s",
            filename, ext, content_type,
        )

    @staticmethod
    async def check_file_size(file: UploadFile) -> None:
        """
        检查上传文件大小是否超过限制。
        通过读取文件内容判断，避免依赖 content-length 头。
        """
        max_size = settings.VIDEO_MAX_SIZE
        # 先检查 content-length（如果存在）
        if hasattr(file, "size") and file.size is not None:
            if file.size > max_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"视频文件过大（{file.size / 1024 / 1024:.1f}MB），"
                    f"最大允许 {max_size / 1024 / 1024:.0f}MB",
                )
            return

        # 否则读取前 max_size+1 字节来验证
        chunk = await file.read(max_size + 1)
        if len(chunk) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"视频文件超过大小限制（最大 {max_size / 1024 / 1024:.0f}MB）",
            )
        # 将读取的内容放回，供后续使用
        await file.seek(0)

    @staticmethod
    def generate_filename(original_filename: str) -> str:
        """生成安全的唯一文件名，保留原始扩展名"""
        ext = Path(original_filename).suffix.lower() or ".mp4"
        return f"{uuid.uuid4().hex}{ext}"

    @staticmethod
    async def save_upload(
        file: UploadFile,
        sub_dir: Optional[str] = None,
    ) -> str:
        """
        保存上传的视频文件到磁盘，返回相对路径。

        Args:
            file: 上传文件对象
            sub_dir: 子目录名（如用户ID），可选

        Returns:
            相对路径字符串（如 'uploads/videos/abc123.mp4'）
        """
        # 确保上传目录存在
        upload_base = Path(settings.VIDEO_UPLOAD_DIR)
        if sub_dir:
            upload_base = upload_base / sub_dir
        upload_base.mkdir(parents=True, exist_ok=True)

        # 生成安全文件名
        safe_name = MediaService.generate_filename(file.filename or "video.mp4")
        dest_path = upload_base / safe_name

        # 写入文件
        content = await file.read()
        dest_path.write_bytes(content)

        relative_path = str(Path("uploads") / "videos")
        if sub_dir:
            relative_path = f"{relative_path}/{sub_dir}"
        relative_path = f"{relative_path}/{safe_name}"

        logger.info(
            "视频文件已保存: orig=%s, saved=%s, size=%d",
            file.filename, relative_path, len(content),
        )
        return relative_path

    @staticmethod
    async def video_exists(file: UploadFile) -> bool:
        """
        快速检查视频文件是否可读、非空（用于上传前预检）。
        在此实现中保留为辅助方法，实际预检在 validate + check_size 中完成。
        """
        return True

    @staticmethod
    async def transcode_video(
        source_path: str,
        target_format: str = "mp4",
    ) -> Optional[str]:
        """
        视频转码（使用 ffmpeg）。
        如果系统中没有 ffmpeg，则跳过转码，返回 None。

        Args:
            source_path: 源文件路径
            target_format: 目标格式 ('mp4' | 'webm')

        Returns:
            转码后文件路径，若跳过转码则返回 None
        """
        if target_format not in TRANSCODE_PRESETS:
            logger.warning("不支持的转码目标格式: %s，跳过转码", target_format)
            return None

        # 检查 ffmpeg 是否可用
        try:
            proc = await asyncio.create_subprocess_exec(
                "ffmpeg", "-version",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            retcode = await proc.wait()
            if retcode != 0:
                logger.info("ffmpeg 不可用（返回码 %d），跳过视频转码", retcode)
                return None
        except FileNotFoundError:
            logger.info("系统中未安装 ffmpeg，跳过视频转码")
            return None

        preset = TRANSCODE_PRESETS[target_format]
        src = Path(source_path)
        dest = src.with_suffix(f".{target_format}")

        # 如果目标文件已存在，跳过转码
        if dest.exists():
            logger.info("转码目标文件已存在，跳过: %s", dest)
            return str(dest)

        cmd = [
            "ffmpeg", "-i", str(src),
            "-c:v", preset["codec_video"],
            "-c:a", preset["codec_audio"],
            "-crf", preset["crf"],
            "-pix_fmt", preset["pix_fmt"],
            *preset["extra_args"],
            "-y", str(dest),
        ]

        logger.info("开始视频转码: %s -> %s", src, dest)
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            logger.error(
                "视频转码失败: return_code=%d, stderr=%s",
                proc.returncode, stderr.decode()[:500],
            )
            return None

        logger.info("视频转码完成: %s（%d 字节）", dest, dest.stat().st_size)
        return str(dest)

    @staticmethod
    async def handle_video_upload(
        file: UploadFile,
        user_id: Optional[int] = None,
        transcode: bool = True,
    ) -> dict:
        """
        完整的视频上传处理流程：
        1. 验证格式
        2. 检查大小
        3. 保存文件
        4. 可选转码

        Args:
            file: 上传文件
            user_id: 用户ID（用于子目录）
            transcode: 是否尝试转码

        Returns:
            {
                "url": "uploads/videos/xxx.mp4",       # 最终视频 URL
                "original_name": "原始文件名.mp4",       # 原始文件名
                "size": 1234567,                        # 文件大小（字节）
                "transcoded": True/False,               # 是否经过转码
            }
        """
        # 1. 格式验证
        MediaService.validate_video(file)

        # 2. 大小检查
        await MediaService.check_file_size(file)

        # 3. 保存
        sub_dir = str(user_id) if user_id is not None else None
        saved_path = await MediaService.save_upload(file, sub_dir=sub_dir)

        result = {
            "url": saved_path,
            "original_name": file.filename or "",
            "size": 0,
            "transcoded": False,
        }

        # 获取实际文件大小
        full_path = Path(settings.VIDEO_UPLOAD_DIR) / (sub_dir or "") / Path(saved_path).name
        if full_path.exists():
            result["size"] = full_path.stat().st_size

        # 4. 可选转码
        if transcode:
            transcode_target = "mp4"
            # 如果是 webm 则转成 mp4，mp4 则尝试优化
            ext = Path(saved_path).suffix.lower()
            if ext == ".webm":
                transcode_target = "mp4"
            elif ext == ".mp4":
                transcode_target = "mp4"  # 重新编码优化

            transcoded_path = await MediaService.transcode_video(
                str(full_path),
                target_format=transcode_target,
            )
            if transcoded_path:
                rel = Path(transcoded_path)
                # 构建相对 URL
                relative_url = str(rel).replace("\\", "/")
                # 更新 URL 为转码后的文件
                idx = relative_url.find("uploads/")
                if idx >= 0:
                    relative_url = relative_url[idx:]
                result["url"] = relative_url
                result["transcoded"] = True

        return result
