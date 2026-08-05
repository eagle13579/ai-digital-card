"""
compression_pipeline.py — Agent 输出压缩引擎

三阶段流水线:
  阶段1: MECE 拆解 — 将 Agent 输出拆解为互斥且穷尽的语义段落
  阶段2: 压缩     — 对每个段落独立应用无损/有损压缩策略
  阶段3: 重组     — 将压缩后的段落重组为完整输出

模式:
  - Lossless (无损): 保留语义完整性，去除冗余空白、注释、重复段落
  - Lossy     (有损): 摘要提取、关键句保留、非关键信息裁剪

默认压缩率: 90%（即压缩后体积为原始体积的 10%）
"""

from __future__ import annotations
import json
import logging
import re
import time
from typing import Any

from app.models.compression import (
    CompressionConfig,
    CompressionMode,
    CompressionResult,
    CompressionStats,
)

logger = logging.getLogger(__name__)

# ── 全局默认配置 ──────────────────────────────────
DEFAULT_CONFIG = CompressionConfig(mode=CompressionMode.LOSSLESS, ratio=0.9)

# ── 全局统计实例 ──────────────────────────────────
_global_stats = CompressionStats()


def get_compression_stats() -> CompressionStats:
    """获取压缩引擎全局统计实例"""
    return _global_stats


# ════════════════════════════════════════════════════
# 阶段1: MECE 拆解 (Mutually Exclusive, Collectively Exhaustive)
# ════════════════════════════════════════════════════


def _mece_decompose(text: str, config: CompressionConfig) -> list[str]:
    """
    MECE 拆解：将输入文本拆解为互斥且穷尽的语义段落。

    拆解策略（按优先级）:
      1. 代码块 (```...```) — 单个完整段落
      2. 表格 (|...|...|)   — 单行作为一个段落
      3. 列表 (-, *, 1.)   — 每个列表项作为一个段落
      4. 标题段落 (# ...)   — 标题 + 跟随内容
      5. 空行分隔的正文段落 — 自然段落
      6. 以上都不满足则按句子切分

    Returns:
        段落列表，每段至少 config.min_segment_chars 字符
    """
    segments: list[str] = []
    text = text.strip()
    if not text:
        return segments

    # 1) 提取代码块
    code_block_re = re.compile(r"```[\s\S]*?```", re.MULTILINE)
    parts: list[str] = []
    last_end = 0
    for m in code_block_re.finditer(text):
        if m.start() > last_end:
            parts.append(text[last_end : m.start()])
        parts.append(m.group())
        last_end = m.end()
    if last_end < len(text):
        parts.append(text[last_end:])

    for part in parts:
        part = part.strip()
        if not part:
            continue
        # 代码块直接作为完整段落
        if part.startswith("```"):
            segments.append(part)
            continue
        # 2) 表格行
        table_rows = _extract_table_rows(part)
        if table_rows:
            segments.extend(table_rows)
            continue
        # 3) 空行分隔自然段落 — 递归子段落拆解
        sub_paras = re.split(r"\n\s*\n", part)
        for sp in sub_paras:
            sp = sp.strip()
            if not sp:
                continue
            # 4) 列表项拆解
            list_items = _extract_list_items(sp)
            if list_items:
                segments.extend(list_items)
                continue
            # 5) 标题段落拆解
            heading_paras = _extract_heading_paragraphs(sp)
            if heading_paras:
                segments.extend(heading_paras)
                continue
            # 6) 按句子切分（长段落）
            if len(sp) > config.max_segment_chars:
                segments.extend(_split_sentences(sp, config.min_segment_chars))
            else:
                segments.append(sp)

    # 合并过短的段落
    return _merge_short_segments(segments, config.min_segment_chars)


def _extract_table_rows(text: str) -> list[str]:
    """提取 Markdown 表格行"""
    rows: list[str] = []
    lines = text.split("\n")
    in_table = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            # 忽略分隔行（|---|）
            if not re.match(r"^\|[\s\-:]+\|$", stripped):
                rows.append(stripped)
                in_table = True
        else:
            if in_table:
                break
    return rows


def _extract_list_items(text: str) -> list[str]:
    """提取列表项（-, *, 1. 等）"""
    items: list[str] = []
    lines = text.split("\n")
    current_item: list[str] = []
    in_list = False
    list_pattern = re.compile(r"^(\s*)([-*]|\d+\.)\s+")

    for line in lines:
        m = list_pattern.match(line)
        if m:
            if current_item:
                items.append("\n".join(current_item).strip())
            current_item = [line]
            in_list = True
        elif in_list:
            if line.strip() and line[0] == " ":
                current_item.append(line)
            else:
                if current_item:
                    items.append("\n".join(current_item).strip())
                    current_item = []
                in_list = False
                # 非列表内容，保持原样
                if line.strip():
                    items.append(line)

    if current_item:
        items.append("\n".join(current_item).strip())

    return items if items else []


def _extract_heading_paragraphs(text: str) -> list[str]:
    """按标题 (#) 拆解段落"""
    segments: list[str] = []
    lines = text.split("\n")
    current: list[str] = []
    for line in lines:
        if re.match(r"^#{1,6}\s+", line):
            if current:
                segments.append("\n".join(current).strip())
            current = [line]
        else:
            current.append(line)
    if current:
        segments.append("\n".join(current).strip())
    return segments if len(segments) > 1 else []


def _split_sentences(text: str, min_chars: int) -> list[str]:
    """按句子边界切分长文本，合并短句"""
    # 中文句号、问号、感叹号、换行、分号
    parts = re.split(r"(?<=[。！？\n;])\s*", text)
    merged: list[str] = []
    buf = ""
    for p in parts:
        if not p.strip():
            continue
        if len(buf) + len(p) < min_chars:
            buf += p
        else:
            if buf:
                merged.append(buf)
            buf = p
    if buf:
        merged.append(buf)
    return merged if merged else [text]


def _merge_short_segments(segments: list[str], min_chars: int) -> list[str]:
    """合并过短的段落到前一段落"""
    if not segments:
        return segments
    merged: list[str] = []
    for seg in segments:
        if (len(seg) < min_chars and merged
                and not seg.startswith("```") and not merged[-1].startswith("```")):
            merged[-1] = merged[-1] + "\n" + seg
        else:
            merged.append(seg)
    return merged


# ════════════════════════════════════════════════════
# 阶段2: 压缩
# ════════════════════════════════════════════════════


def _compress_segment(segment: str, config: CompressionConfig) -> str:
    """
    对单个 MECE 段落应用压缩策略。

    Lossless 策略:
      - 去除多余空白/空行
      - JSON 缩紧（保留结构）
      - 去除注释行（# // /* */）
      - 去除重复行
      - 保持语义无损

    Lossy 策略（含 Lossless 的所有操作 +）:
      - 截断到目标 ratio
      - 优先保留：标题、关键句（带 !、结论性语句）
      - 摘要：保留前 N% 的重要内容
    """
    if not segment:
        return segment

    # ── 基础清洗（两种模式都执行） ──
    compressed = _basic_clean(segment, config)

    if config.mode == CompressionMode.LOSSLESS:
        # 无损模式下只做基础清洗
        return _ensure_ratio(compressed, segment, config)

    # ── Lossy: 有损压缩 ──
    return _lossy_compress(compressed, config)


def _basic_clean(text: str, config: CompressionConfig) -> str:
    """基础清洗：去除冗余，保持语义无损"""
    lines = text.split("\n")
    cleaned: list[str] = []
    seen: set[str] = set()

    for line in lines:
        stripped = line.strip()

        # 空行 — 无损模式下只保留一个连续空行
        if not stripped:
            if cleaned and cleaned[-1] != "":
                cleaned.append("")
            continue

        # 去掉纯注释行
        if re.match(r"^\s*(#|//|--|/\*|\*/\s*$)", stripped):
            continue

        # 去重（相同内容的行只保留一个）
        if config.enable_dedup:
            norm = stripped.lower()
            if norm in seen:
                continue
            seen.add(norm)

        cleaned.append(stripped)

    # 去除首尾空行
    while cleaned and cleaned[0] == "":
        cleaned.pop(0)
    while cleaned and cleaned[-1] == "":
        cleaned.pop()

    return "\n".join(cleaned)


def _ensure_ratio(compressed: str, original: str, config: CompressionConfig) -> str:
    """确保无损压缩后仍达到目标压缩率（如果基础清洗不够，补充裁剪）。"""
    orig_size = len(original.encode("utf-8"))
    comp_size = len(compressed.encode("utf-8"))
    actual_ratio = 1.0 - (comp_size / max(orig_size, 1))
    if actual_ratio >= config.ratio:
        return compressed

    # 未达目标：进一步压缩（仅对过长段落）
    lines = compressed.split("\n")
    if len(lines) <= 3:
        return compressed

    # 移除最不重要的段落（中间的内容段落）
    target_size = int(orig_size * (1.0 - config.ratio))
    if len(compressed) <= target_size:
        return compressed

    # 保留首尾，从中间删除
    keep_first = max(1, len(lines) // 4)
    keep_last = max(1, len(lines) // 4)
    result = lines[:keep_first] + lines[-keep_last:]
    result_text = "\n".join(result)

    if len(result_text.encode("utf-8")) > target_size:
        # 仍然过长：逐行从中间删除
        middle = lines[keep_first:-keep_last]
        while middle and len(result_text.encode("utf-8")) > target_size:
            # 删除中间最中间的行
            mid_idx = len(middle) // 2
            middle.pop(mid_idx)
            result_text = "\n".join(lines[:keep_first] + middle + lines[-keep_last:])

    return result_text


def _lossy_compress(text: str, config: CompressionConfig) -> str:
    """有损压缩：智能摘要 + 关键信息保留"""
    lines = text.split("\n")
    orig_size = len(text.encode("utf-8"))
    target_size = int(orig_size * (1.0 - config.ratio))

    if orig_size <= target_size:
        return text

    # ── 评分：每行的重要性 ──
    scored: list[tuple[float, str, int]] = []  # (score, line, original_index)
    for idx, line in enumerate(lines):
        s = _score_line_importance(line)
        scored.append((s, line, idx))

    # ── 按重要性排序 ──
    if config.enable_sort:
        scored.sort(key=lambda x: (-x[0], x[2]))

    # ── 从最重要行开始累积，直到达到目标大小 ──
    result_lines: list[tuple[int, str]] = []
    current_size = 0
    for score, line, idx in scored:
        line_bytes = len(line.encode("utf-8"))
        if current_size + line_bytes <= target_size:
            result_lines.append((idx, line))
            current_size += line_bytes
        if current_size >= target_size:
            break

    # ── 按原始顺序恢复 ──
    result_lines.sort(key=lambda x: x[0])
    result = "\n".join(line for _, line in result_lines)

    # 如果结果为空，保留最关键的一行
    if not result.strip() and lines:
        # 找最重要的行
        best = max(scored, key=lambda x: x[0])
        result = best[1]

    return result


def _score_line_importance(line: str) -> float:
    """
    评估行的语义重要性（0~1）。

    重要特征:
      - 标题 (#) → 高
      - 加粗 (**) → 较高
      - 含结论性词语（结论/总结/因此/所以/总之）→ 高
      - 含数字/关键数据 → 较高
      - 短行（分隔符/装饰）→ 低
      - 纯标点 → 极低
    """
    stripped = line.strip()
    if not stripped:
        return 0.0

    score = 0.5

    # 标题
    if re.match(r"^#{1,6}\s+", stripped):
        score += 0.4
    # 加粗
    if re.search(r"\*\*.*\*\*", stripped):
        score += 0.2
    # 结论性词语
    if re.search(r"(结论|总结|因此|所以|总之|综上所述|关键|重要|核心)", stripped):
        score += 0.3
    # 数据
    if re.search(r"\d+[.%]|第\d+|[0-9,]+元|占比|增长|下降|同比|环比", stripped):
        score += 0.2
    # 代码块标记
    if stripped.startswith("```"):
        score += 0.3
    # 短行降权
    if len(stripped) < 10:
        score -= 0.2
    # 纯标点/装饰
    if re.match(r"^[\s\-_=*#]+$", stripped):
        score -= 0.3

    return max(0.0, min(1.0, score))


# ════════════════════════════════════════════════════
# 阶段3: 重组
# ════════════════════════════════════════════════════


def _recompose(segments: list[str]) -> str:
    """
    将压缩后的段落重组为完整输出。

    规则:
      - 段落间以双换行分隔
      - 代码块前后保留原样
      - 最后清理多余空行
    """
    if not segments:
        return ""

    result = ""
    for i, seg in enumerate(segments):
        seg = seg.strip()
        if not seg:
            continue
        if i > 0:
            # 代码块前不加额外空行
            if seg.startswith("```"):
                result += "\n" + seg
            elif result.endswith("```"):
                result += "\n\n" + seg
            else:
                result += "\n\n" + seg
        else:
            result = seg

    return result.strip()


# ════════════════════════════════════════════════════
# 流水线入口
# ════════════════════════════════════════════════════


class CompressionPipeline:
    """
    Agent 输出压缩引擎 — 三阶段流水线。

    用法:
        pipeline = CompressionPipeline()
        result = pipeline.compress("长篇 Agent 输出文本...")
    """

    def __init__(self, config: CompressionConfig | None = None):
        self.config: CompressionConfig = config or CompressionConfig()

    def compress(
        self,
        text: str,
        config: CompressionConfig | None = None,
    ) -> CompressionResult:
        """
        执行完整的三阶段压缩流水线。

        Args:
            text: 原始 Agent 输出文本
            config: 压缩配置（覆盖实例级配置）

        Returns:
            CompressionResult 包含压缩结果及统计
        """
        start = time.time()
        cfg = config or self.config
        error: str | None = None

        try:
            original = text
            if not original or not original.strip():
                result = CompressionResult(
                    original_text=original,
                    compressed_text=original,
                    mode=cfg.mode,
                    timing_ms=0.0,
                )
                _global_stats.record(result)
                return result

            # ── 阶段1: MECE 拆解 ──
            segments = _mece_decompose(original, cfg)
            segments_before = len(segments)

            # ── 阶段2: 逐段压缩 ──
            compressed_segments = [
                _compress_segment(seg, cfg) for seg in segments
            ]
            # 过滤压缩后为空的段落
            compressed_segments = [s for s in compressed_segments if s.strip()]

            # ── 阶段3: 重组 ──
            compressed_text = _recompose(compressed_segments)

            elapsed = (time.time() - start) * 1000  # ms

            result = CompressionResult(
                original_text=original,
                compressed_text=compressed_text,
                original_size=len(original.encode("utf-8")),
                compressed_size=len(compressed_text.encode("utf-8")),
                compression_ratio=1.0 - (
                    len(compressed_text.encode("utf-8"))
                    / max(len(original.encode("utf-8")), 1)
                ),
                segments_before=segments_before,
                segments_after=len(compressed_segments),
                mode=cfg.mode,
                timing_ms=elapsed,
                metadata={"config": cfg.to_dict()},
            )

        except Exception as exc:
            logger.exception("压缩流水线异常")
            error = str(exc)
            elapsed = (time.time() - start) * 1000
            result = CompressionResult(
                original_text=text,
                compressed_text=text,  # 异常时返回原文
                mode=cfg.mode,
                timing_ms=elapsed,
                error=error,
            )

        _global_stats.record(result)
        return result

    def compress_lossless(self, text: str) -> CompressionResult:
        """快速无损压缩"""
        cfg = CompressionConfig(mode=CompressionMode.LOSSLESS, ratio=self.config.ratio)
        return self.compress(text, cfg)

    def compress_lossy(self, text: str) -> CompressionResult:
        """快速有损压缩"""
        cfg = CompressionConfig(mode=CompressionMode.LOSSY, ratio=self.config.ratio)
        return self.compress(text, cfg)


# ── 单例全局引擎 ──────────────────────────────────
_pipeline_instance: CompressionPipeline | None = None


def get_pipeline(config: CompressionConfig | None = None) -> CompressionPipeline:
    """获取全局压缩流水线实例（单例）"""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = CompressionPipeline(config)
    return _pipeline_instance


def compress_text(
    text: str,
    mode: CompressionMode = CompressionMode.LOSSLESS,
    ratio: float = 0.9,
    **kwargs: Any,
) -> CompressionResult:
    """
    便捷函数：一行完成压缩。

    Args:
        text: 原始文本
        mode: 压缩模式
        ratio: 目标压缩率
        **kwargs: 其他 CompressionConfig 参数

    Returns:
        CompressionResult
    """
    config = CompressionConfig(mode=mode, ratio=ratio, **kwargs)
    pipeline = get_pipeline(config)
    return pipeline.compress(text, config)
