"""
compression_router.py — Agent 输出压缩引擎 API (FastAPI)

API:
  POST /api/compression/compress — 压缩 Agent 输出文本
  GET  /api/compression/stats   — 压缩引擎全局统计信息

使用场景:
  - 前端/F10 指挥官调用压缩 Agent 输出以减少 Token 消耗
  - 无损模式用于日志/结构化数据
  - 有损模式用于 Agent 中间结果/长对话摘要
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional

from app.models.compression import (
    CompressionConfig,
    CompressionMode,
)
from app.services.compression_pipeline import (
    CompressionPipeline,
    get_pipeline,
    get_compression_stats,
    compress_text,
)

router = APIRouter(prefix="/api/compression", tags=["F11 压缩流水线"])

# ── 全局引擎实例（默认配置：Lossless, 90% 压缩率） ──
_pipeline: CompressionPipeline = get_pipeline()


# ── 请求/响应模型 ──────────────────────────


class CompressRequest(BaseModel):
    """
    压缩请求。

    支持快速传入 text + mode + ratio，
    也支持完整的 config 对象覆盖所有参数。
    """
    text: str = Field(..., description="待压缩的 Agent 输出原文", min_length=1, max_length=1_000_000)
    mode: CompressionMode = Field(
        default=CompressionMode.LOSSLESS,
        description="压缩模式：lossless（无损）/ lossy（有损）",
    )
    ratio: float = Field(
        default=0.9,
        ge=0.01,
        le=1.0,
        description="目标压缩率（0.01~1.0），0.9 = 压缩到原始体积的 10%",
    )
    min_segment_chars: Optional[int] = Field(
        default=None,
        ge=10,
        description="MECE 拆解最小段落字符数（覆盖默认 80）",
    )
    max_segment_chars: Optional[int] = Field(
        default=None,
        ge=80,
        description="MECE 拆解最大段落字符数（覆盖默认 2000）",
    )
    preserve_keys: Optional[list[str]] = Field(
        default=None,
        description="无损模式下必须保留的关键字段列表",
    )
    enable_dedup: Optional[bool] = Field(
        default=None,
        description="是否启用段落级去重（默认开启）",
    )
    enable_sort: Optional[bool] = Field(
        default=None,
        description="有损模式下是否按重要性排序（默认关闭）",
    )


class CompressResponse(BaseModel):
    """压缩响应"""
    code: int = 0
    message: str = "success"
    data: Optional[dict] = None


class StatsResponse(BaseModel):
    """统计响应"""
    code: int = 0
    message: str = "success"
    data: Optional[dict] = None


# ── POST /api/compression/compress — 压缩文本 ──


@router.post("/compress", response_model=CompressResponse)
async def compress_endpoint(req: CompressRequest):
    """
    压缩 Agent 输出文本。

    使用 MECE 拆解 → 逐段压缩 → 重组的三阶段流水线。
    支持 Lossless（无损）和 Lossy（有损）两种模式。

    请求示例:
        {
            "text": "长篇 Agent 输出...",
            "mode": "lossless",
            "ratio": 0.9
        }

    返回:
        - compressed_text: 压缩后文本
        - original_size: 原始字节数
        - compressed_size: 压缩后字节数
        - compression_ratio: 实际压缩率
        - segments_before: 拆解前段落数
        - segments_after: 压缩后段落数
        - mode: 使用的压缩模式
        - timing_ms: 耗时（毫秒）
    """
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="text 不能为空")

    # 构建配置
    config_kwargs = {"mode": req.mode, "ratio": req.ratio}
    if req.min_segment_chars is not None:
        config_kwargs["min_segment_chars"] = req.min_segment_chars
    if req.max_segment_chars is not None:
        config_kwargs["max_segment_chars"] = req.max_segment_chars
    if req.preserve_keys is not None:
        config_kwargs["preserve_keys"] = req.preserve_keys
    if req.enable_dedup is not None:
        config_kwargs["enable_dedup"] = req.enable_dedup
    if req.enable_sort is not None:
        config_kwargs["enable_sort"] = req.enable_sort

    config = CompressionConfig(**config_kwargs)

    result = _pipeline.compress(req.text, config)

    if result.error:
        return CompressResponse(
            code=1,
            message=f"压缩完成但存在错误: {result.error}",
            data=result.to_dict(),
        )

    return CompressResponse(data={
        **result.to_dict(),
        "compressed_text": result.compressed_text,
    })


# ── GET /api/compression/stats — 全局统计 ──


@router.get("/stats", response_model=StatsResponse)
async def compression_stats():
    """
    获取压缩引擎全局统计信息。

    返回:
        - total_compressions: 总压缩次数
        - total_original_bytes: 总原始字节数
        - total_compressed_bytes: 总压缩后字节数
        - total_saved_bytes: 总节省字节数
        - average_compression_ratio: 平均压缩率
        - average_timing_ms: 平均耗时（毫秒）
        - error_count: 错误次数
        - mode_counts: 各模式使用次数
        - last_timestamp: 最近一次压缩时间戳
    """
    stats = get_compression_stats()
    return StatsResponse(data=stats.to_dict())


# ── POST /api/compression/reset-stats — 重置统计（管理用） ──


@router.post("/reset-stats", response_model=StatsResponse)
async def reset_compression_stats():
    """重置压缩引擎全局统计（管理/调试用）"""
    from app.models.compression import CompressionStats
    import app.services.compression_pipeline as cp
    cp._global_stats = CompressionStats()
    return StatsResponse(message="统计已重置", data=cp._global_stats.to_dict())
