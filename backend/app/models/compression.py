"""
compression.py — Agent 输出压缩引擎数据模型

定义 CompressionMode（压缩模式枚举）、CompressionConfig（压缩配置）、
CompressionResult（压缩结果）、CompressionStats（全局统计）。
"""

from __future__ import annotations
import time
from enum import Enum
from typing import Any


class CompressionMode(str, Enum):
    """压缩模式枚举"""
    LOSSLESS = "lossless"  # 无损压缩：保持语义完整性，仅去除冗余
    LOSSY = "lossy"        # 有损压缩：允许语义精简/摘要，大幅降低体积


class CompressionConfig:
    """
    Agent 输出压缩引擎配置。

    Attributes:
        mode: 压缩模式（lossless / lossy）
        ratio: 目标压缩率，范围 0.0~1.0（默认 0.9 = 压缩到原始体积的 10%）
        min_segment_chars: MECE 拆解最小段落字符数
        max_segment_chars: MECE 拆解最大段落字符数
        preserve_keys: 无损模式下必须保留的关键字段列表
        max_summary_sentences: 有损模式下摘要最大句子数
        enable_dedup: 是否启用段落级去重（无损模式下默认开启）
        enable_sort: 是否启用段落按重要性排序（有损模式下默认开启）
    """

    def __init__(
        self,
        mode: CompressionMode = CompressionMode.LOSSLESS,
        ratio: float = 0.9,
        min_segment_chars: int = 80,
        max_segment_chars: int = 2000,
        preserve_keys: list[str] | None = None,
        max_summary_sentences: int = 5,
        enable_dedup: bool = True,
        enable_sort: bool = False,
    ):
        if not 0.0 < ratio <= 1.0:
            raise ValueError("ratio 必须在 (0.0, 1.0] 范围内")
        if min_segment_chars < 10:
            raise ValueError("min_segment_chars 必须 >= 10")
        if max_segment_chars < min_segment_chars:
            raise ValueError("max_segment_chars 必须 >= min_segment_chars")

        self.mode: CompressionMode = mode
        self.ratio: float = ratio
        self.min_segment_chars: int = min_segment_chars
        self.max_segment_chars: int = max_segment_chars
        self.preserve_keys: list[str] = preserve_keys or []
        self.max_summary_sentences: int = max_summary_sentences
        self.enable_dedup: bool = enable_dedup
        self.enable_sort: bool = enable_sort

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value,
            "ratio": self.ratio,
            "min_segment_chars": self.min_segment_chars,
            "max_segment_chars": self.max_segment_chars,
            "preserve_keys": self.preserve_keys,
            "max_summary_sentences": self.max_summary_sentences,
            "enable_dedup": self.enable_dedup,
            "enable_sort": self.enable_sort,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> CompressionConfig:
        return CompressionConfig(
            mode=CompressionMode(data.get("mode", "lossless")),
            ratio=data.get("ratio", 0.9),
            min_segment_chars=data.get("min_segment_chars", 80),
            max_segment_chars=data.get("max_segment_chars", 2000),
            preserve_keys=data.get("preserve_keys", []),
            max_summary_sentences=data.get("max_summary_sentences", 5),
            enable_dedup=data.get("enable_dedup", True),
            enable_sort=data.get("enable_sort", False),
        )

    def __repr__(self) -> str:
        return (
            f"<CompressionConfig mode={self.mode.value} "
            f"ratio={self.ratio}>"
        )


class CompressionResult:
    """
    单次压缩结果。

    Attributes:
        original_text: 原始文本
        compressed_text: 压缩后文本
        original_size: 原始字节数
        compressed_size: 压缩后字节数
        compression_ratio: 实际压缩率
        segments_before: 拆解前段落数
        segments_after: 压缩后段落数
        mode: 使用的压缩模式
        timing_ms: 耗时（毫秒）
        error: 压缩过程中的错误信息（如有）
        metadata: 附加元数据
    """

    def __init__(
        self,
        original_text: str,
        compressed_text: str,
        original_size: int = 0,
        compressed_size: int = 0,
        compression_ratio: float = 0.0,
        segments_before: int = 0,
        segments_after: int = 0,
        mode: CompressionMode = CompressionMode.LOSSLESS,
        timing_ms: float = 0.0,
        error: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        self.original_text: str = original_text
        self.compressed_text: str = compressed_text
        self.original_size: int = original_size or len(original_text.encode("utf-8"))
        self.compressed_size: int = compressed_size or len(compressed_text.encode("utf-8"))
        self.compression_ratio: float = compression_ratio or (
            1.0 - (self.compressed_size / max(self.original_size, 1))
        )
        self.segments_before: int = segments_before
        self.segments_after: int = segments_after
        self.mode: CompressionMode = mode
        self.timing_ms: float = timing_ms
        self.error: str | None = error
        self.metadata: dict[str, Any] = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "original_size": self.original_size,
            "compressed_size": self.compressed_size,
            "compression_ratio": round(self.compression_ratio, 4),
            "segments_before": self.segments_before,
            "segments_after": self.segments_after,
            "mode": self.mode.value,
            "timing_ms": round(self.timing_ms, 2),
            "error": self.error,
            "metadata": self.metadata,
        }

    def __repr__(self) -> str:
        return (
            f"<CompressionResult {self.original_size}→{self.compressed_size} "
            f"({self.compression_ratio:.1%}) "
            f"mode={self.mode.value}>"
        )


class CompressionStats:
    """
    压缩引擎全局统计。

    Attributes:
        total_compressions: 总压缩次数
        total_original_bytes: 总原始字节数
        total_compressed_bytes: 总压缩后字节数
        total_timing_ms: 总耗时（毫秒）
        error_count: 错误次数
        mode_counts: 各模式使用次数
        last_timestamp: 最近一次压缩时间戳
    """

    def __init__(self):
        self.total_compressions: int = 0
        self.total_original_bytes: int = 0
        self.total_compressed_bytes: int = 0
        self.total_timing_ms: float = 0.0
        self.error_count: int = 0
        self.mode_counts: dict[str, int] = {}
        self.last_timestamp: float | None = None

    def record(self, result: CompressionResult) -> None:
        """记录一次压缩结果到统计"""
        self.total_compressions += 1
        self.total_original_bytes += result.original_size
        self.total_compressed_bytes += result.compressed_size
        self.total_timing_ms += result.timing_ms
        if result.error:
            self.error_count += 1
        mode_key = result.mode.value
        self.mode_counts[mode_key] = self.mode_counts.get(mode_key, 0) + 1
        self.last_timestamp = time.time()

    def to_dict(self) -> dict[str, Any]:
        avg_ratio = 0.0
        avg_timing = 0.0
        if self.total_compressions > 0:
            saved = self.total_original_bytes - self.total_compressed_bytes
            avg_ratio = saved / max(self.total_original_bytes, 1)
            avg_timing = self.total_timing_ms / self.total_compressions

        return {
            "total_compressions": self.total_compressions,
            "total_original_bytes": self.total_original_bytes,
            "total_compressed_bytes": self.total_compressed_bytes,
            "total_saved_bytes": self.total_original_bytes - self.total_compressed_bytes,
            "average_compression_ratio": round(avg_ratio, 4),
            "average_timing_ms": round(avg_timing, 2),
            "error_count": self.error_count,
            "mode_counts": self.mode_counts,
            "last_timestamp": self.last_timestamp,
        }

    def __repr__(self) -> str:
        return (
            f"<CompressionStats total={self.total_compressions} "
            f"errors={self.error_count}>"
        )
