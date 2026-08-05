"""
task_slicer.py — 任务切片引擎

大任务自动分解为子任务，支持三种切片模式：
  1. TOKEN_BUDGET: 按每片 Token 预算切割
  2. STEP:         按显式步骤/阶段标识切割
  3. SEMANTIC:     按语义段落边界（标题、空行、列表）切割

核心 API:
  - slice_by_token_budget(task, budget, overlap) -> SlicePlan
  - slice_by_steps(task, step_markers)           -> SlicePlan
  - slice_by_semantic(task, min_chunk_size)      -> SlicePlan
  - auto_slice(task, mode, **kwargs)             -> SlicePlan  (统一入口)
"""

from __future__ import annotations
import re
import math
from typing import Any

from app.models.task_slice import TaskSlice, SlicePlan, SliceMode, SliceStatus


# ──────────────────────────────────────────────
# 辅助函数
# ──────────────────────────────────────────────

# 简单 Token 估算: 中文 ~1.5 token/字, 英文 ~1 token/词
_CHINESE_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]")
_EN_WORD_RE = re.compile(r"[a-zA-Z]+")


def estimate_tokens(text: str) -> int:
    """快速估算文本 Token 数（无需调用 LLM）"""
    chinese_chars = len(_CHINESE_RE.findall(text))
    en_words = len(_EN_WORD_RE.findall(text))
    other_chars = len(text) - chinese_chars - sum(len(w) for w in _EN_WORD_RE.findall(text))
    return int(chinese_chars * 1.5 + en_words * 1.3 + other_chars * 0.25)


def _chinese_split_sentences(text: str) -> list[str]:
    """按句号、问号、感叹号、分号拆分句子（保留分隔符）"""
    parts = re.split(r"(?<=[。！？；\n])", text)
    return [p.strip() for p in parts if p.strip()]


def _split_semantic_chunks(text: str) -> list[str]:
    """
    按语义段落拆块。优先按 Markdown 标题级别分割，再按连续空行，
    最后按句子边界保底。
    返回 ["块1", "块2", ...]
    """
    lines = text.splitlines(keepends=True)

    # 策略1: 按 Markdown 标题分割 (# ## ### 等)
    chunks: list[list[str]] = [[]]
    for line in lines:
        if re.match(r"^#{1,6}\s", line):
            # 非空块则新块
            if chunks[-1]:
                chunks.append([])
        chunks[-1].append(line)

    if len(chunks) > 1:
        return ["".join(c).strip() for c in chunks if "".join(c).strip()]

    # 策略2: 按连续空行分割段落
    chunks = [[]]
    blank_count = 0
    for line in lines:
        if line.strip() == "":
            blank_count += 1
            if blank_count >= 2 and chunks[-1]:
                chunks.append([])
                blank_count = 0
        else:
            blank_count = 0
            chunks[-1].append(line)

    if len(chunks) > 1:
        return ["".join(c).strip() for c in chunks if "".join(c).strip()]

    # 策略3: 按句子分割为合理大小的块（至少 3 句一组）
    sentences = _chinese_split_sentences(text)
    if len(sentences) <= 1:
        return [text] if text else []

    chunk_size = max(1, len(sentences) // max(1, (len(sentences) // 5)))
    result = []
    for i in range(0, len(sentences), chunk_size):
        block = "".join(sentences[i:i + chunk_size]).strip()
        if block:
            result.append(block)
    return result if result else [text]


# ──────────────────────────────────────────────
# 切片引擎
# ──────────────────────────────────────────────


class TaskSlicer:
    """
    任务切片引擎。

    用法:
        slicer = TaskSlicer()
        plan = slicer.auto_slice("长任务文本...", mode="token_budget", budget=500)
        slices = plan.slices
    """

    DEFAULT_TOKEN_BUDGET = 500       # 每片默认 Token 预算
    DEFAULT_OVERLAP = 50             # 默认重叠 Tokens
    DEFAULT_MIN_CHUNK_SIZE = 100     # 语义切片最小 Tokens

    # ── 模式 A: Token 预算 ──────────────────

    def slice_by_token_budget(
        self,
        content: str,
        budget: int | None = None,
        overlap: int | None = None,
        task_id: str | None = None,
        metadata: dict | None = None,
    ) -> SlicePlan:
        """
        按 Token 预算切割。
        用滑窗确保每片不超过 budget，片与片之间 overlap 个 Token 重叠。
        """
        budget = budget or self.DEFAULT_TOKEN_BUDGET
        overlap = overlap or self.DEFAULT_OVERLAP
        meta = {"budget": budget, "overlap": overlap, **(metadata or {})}

        plan = SlicePlan(
            original_content=content,
            mode=SliceMode.TOKEN_BUDGET,
            task_id=task_id,
            metadata=meta,
        )

        # 按句子拆分后再组合，避免词中切割
        sentences = _chinese_split_sentences(content)
        if not sentences:
            sentences = [content]

        current_chunk: list[str] = []
        current_tokens = 0

        for sent in sentences:
            sent_tokens = estimate_tokens(sent)
            if current_tokens + sent_tokens <= budget:
                current_chunk.append(sent)
                current_tokens += sent_tokens
            else:
                # 保存当前块
                if current_chunk:
                    chunk_text = "".join(current_chunk)
                    plan.add_slice(TaskSlice(
                        content=chunk_text,
                        token_estimate=estimate_tokens(chunk_text),
                    ))
                # 新块：如果当前句子太长，暴力切割
                if sent_tokens > budget:
                    self._split_long_chunk(plan, sent, budget, meta)
                    current_chunk = []
                    current_tokens = 0
                    if overlap > 0 and plan.slices:
                        # 从上一个切片尾部回退 overlap
                        tail = plan.slices[-1].content
                        tail_sentences = _chinese_split_sentences(tail)
                        overlap_tokens = 0
                        for ts in reversed(tail_sentences):
                            t = estimate_tokens(ts)
                            if overlap_tokens + t <= overlap:
                                current_chunk.insert(0, ts)
                                current_tokens += t
                                overlap_tokens += t
                            else:
                                break
                else:
                    current_chunk = [sent]
                    current_tokens = sent_tokens

        # 尾块
        if current_chunk:
            chunk_text = "".join(current_chunk)
            plan.add_slice(TaskSlice(
                content=chunk_text,
                token_estimate=estimate_tokens(chunk_text),
            ))

        return plan

    def _split_long_chunk(
        self, plan: SlicePlan, text: str, budget: int, meta: dict
    ) -> None:
        """暴力切割超过预算的文本（按字符比例）"""
        total_tokens = estimate_tokens(text)
        if total_tokens <= budget:
            plan.add_slice(TaskSlice(
                content=text,
                token_estimate=total_tokens,
            ))
            return
        ratio = budget / total_tokens
        chunk_size = max(1, int(len(text) * ratio))
        for i in range(0, len(text), chunk_size):
            piece = text[i:i + chunk_size]
            plan.add_slice(TaskSlice(
                content=piece,
                token_estimate=estimate_tokens(piece),
            ))

    # ── 模式 B: 步骤 ────────────────────────

    def slice_by_steps(
        self,
        content: str,
        step_markers: list[str] | None = None,
        task_id: str | None = None,
        metadata: dict | None = None,
    ) -> SlicePlan:
        """
        按显式步骤/阶段标识切割。
        默认步骤标识: 步骤一/二/三..., Step 1/2/3..., 阶段1/2/3...
        """
        markers = step_markers or [
            r"步骤[一二三四五六七八九十]+",
            r"步骤\d+",
            r"Step\s*\d+",
            r"阶段[一二三四五六七八九十]+",
            r"阶段\d+",
            r"第[一二三四五六七八九十]+步",
            r"第\d+步",
            r"\d+\.\s+",        # "1. " 数字列表
        ]
        meta = {"step_markers": step_markers or "auto", **(metadata or {})}

        plan = SlicePlan(
            original_content=content,
            mode=SliceMode.STEP,
            task_id=task_id,
            metadata=meta,
        )

        # 构建统一的匹配 pattern
        pattern = "|".join(f"(?:{m})" for m in markers)
        compiled = re.compile(pattern, re.MULTILINE)

        # 按步骤标识拆段
        lines = content.splitlines(keepends=True)
        current_step: list[str] = []
        current_label = "step_0"

        for line in lines:
            match = compiled.search(line)
            if match:
                if current_step:
                    step_text = "".join(current_step)
                    plan.add_slice(TaskSlice(
                        content=step_text,
                        metadata={"step_label": current_label},
                        token_estimate=estimate_tokens(step_text),
                    ))
                current_step = [line]
                current_label = match.group().strip()
            else:
                current_step.append(line)

        if current_step:
            step_text = "".join(current_step)
            plan.add_slice(TaskSlice(
                content=step_text,
                metadata={"step_label": current_label},
                token_estimate=estimate_tokens(step_text),
            ))

        # 如果没有切到任何步骤，回退到 Token 预算模式
        if plan.slice_count <= 1 and step_markers is None:
            return self.slice_by_token_budget(
                content, budget=self.DEFAULT_TOKEN_BUDGET,
                task_id=task_id, metadata=meta,
            )

        return plan

    # ── 模式 C: 语义 ────────────────────────

    def slice_by_semantic(
        self,
        content: str,
        min_chunk_size: int | None = None,
        task_id: str | None = None,
        metadata: dict | None = None,
    ) -> SlicePlan:
        """
        按语义段落边界切割。自动识别标题、段落、列表。
        """
        min_size = min_chunk_size or self.DEFAULT_MIN_CHUNK_SIZE
        meta = {"min_chunk_size": min_size, **(metadata or {})}

        plan = SlicePlan(
            original_content=content,
            mode=SliceMode.SEMANTIC,
            task_id=task_id,
            metadata=meta,
        )

        chunks = _split_semantic_chunks(content)

        # 合并过小的块
        merged: list[str] = []
        buffer = ""
        for chunk in chunks:
            if not chunk:
                continue
            if estimate_tokens(buffer + chunk) < min_size and merged:
                buffer += "\n" + chunk
            else:
                if buffer:
                    merged.append(buffer)
                buffer = chunk
        if buffer:
            merged.append(buffer)

        # 如果合并后只有一个块且太大了，按 Token 预算再切
        if len(merged) == 1 and estimate_tokens(merged[0]) > min_size * 4:
            return self.slice_by_token_budget(
                content, budget=min_size * 2,
                task_id=task_id, metadata=meta,
            )

        for chunk in merged:
            plan.add_slice(TaskSlice(
                content=chunk,
                token_estimate=estimate_tokens(chunk),
            ))

        return plan

    # ── 统一入口 ────────────────────────────

    def auto_slice(
        self,
        content: str,
        mode: str | SliceMode = "token_budget",
        task_id: str | None = None,
        metadata: dict | None = None,
        **kwargs: Any,
    ) -> SlicePlan:
        """
        统一切片入口。

        Args:
            content: 大任务完整文本
            mode: 切片模式 ("token_budget", "step", "semantic")
            task_id: 可选任务 ID
            metadata: 可选附加元数据
            **kwargs: 传递给具体模式函数的参数
                - token_budget: budget, overlap
                - step: step_markers
                - semantic: min_chunk_size

        Returns:
            SlicePlan: 包含所有子任务切片的计划
        """
        if isinstance(mode, str):
            mode = SliceMode(mode)

        if mode == SliceMode.TOKEN_BUDGET:
            return self.slice_by_token_budget(
                content, task_id=task_id, metadata=metadata, **kwargs,
            )
        elif mode == SliceMode.STEP:
            return self.slice_by_steps(
                content, task_id=task_id, metadata=metadata, **kwargs,
            )
        elif mode == SliceMode.SEMANTIC:
            return self.slice_by_semantic(
                content, task_id=task_id, metadata=metadata, **kwargs,
            )
        else:
            raise ValueError(f"Unknown slice mode: {mode}")
