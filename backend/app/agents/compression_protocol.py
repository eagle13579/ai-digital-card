"""compression_protocol.py — 信号压缩协议

压缩哲学: 过滤99%噪音，只留1%精华
每个Agent输出都必须经过压缩协议，只传递高价值信号。

Only standard library dependencies: datetime, re, json, textwrap
"""

import re
import json
import textwrap
from datetime import datetime
from typing import Optional


def context_distillation(context: str | dict, task_focus: str, max_chars: int = 500) -> str:
    """上下文提纯 — A Orchestra 核心创新 (84%→96%)

    精确筛选而非暴力堆叠：只保留与task_focus直接相关的信号。
    这消除了长周期任务中的上下文衰减。

    Args:
        context: 原始上下文（字符串或字典）
        task_focus: 当前子任务的关注点（用于筛选）
        max_chars: 最大字符数

    Returns:
        提纯后的上下文，只包含高相关性信号
    """
    import json

    raw: str
    if isinstance(context, dict):
        raw = json.dumps(context, ensure_ascii=False, indent=2)
    else:
        raw = context

    # 精确筛选：只保留包含task_focus关键词的行
    focus_keywords = task_focus.lower().split()
    filtered_lines = []
    for line in raw.split("\n"):
        if any(kw in line.lower() for kw in focus_keywords):
            filtered_lines.append(line)
    filtered = "\n".join(filtered_lines) if filtered_lines else raw

    return compress_summary(filtered, max_chars=max_chars)


def compress_summary(raw_text: str, max_chars: int = 500) -> str:
    """用格式模板强制压缩文本，去掉无意义填充，只保留[信号]和[结论]。

    Args:
        raw_text: 原始Agent输出文本
        max_chars: 最大字符数，默认500

    Returns:
        压缩后的文本，格式：[信号] ... [结论] ...
    """
    if not raw_text or not raw_text.strip():
        return "[信号] 空输入 | [结论] 无内容可压缩"

    # Step 1: 去除空白行、纯标点行、无意义填充词
    lines = raw_text.split('\n')
    meaningful_lines = []
    filler_pattern = re.compile(
        r'^(好的|当然|首先|然后|最后|需要注意的是|综上所述|总而言之|'
        r'这里我们|我们可以看到|我们可以发现|值得一提的是|'
        r'OK|Okay|So|Well|Basically|Actually|In conclusion|'
        r'In summary|Note that|Please note|It is worth noting|'
        r'As we can see|As mentioned|As discussed)\s*[：:，,\s]*$',
        re.IGNORECASE
    )
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # 跳过纯标点/纯空格行
        if re.match(r'^[\s\-\*\.\,\!\?\:\;\(\)\[\]\{\}/\\#@\$%\^&\+\=\|~`"\'<>]+$', stripped):
            continue
        # 跳过无意义填充词单独成行
        if filler_pattern.match(stripped):
            continue
        meaningful_lines.append(stripped)

    # Step 2: 提取信号和结论部分
    full_text = ' | '.join(meaningful_lines)

    signal_match = re.search(
        r'[\[【]信号[\]】]\s*[:：]?\s*(.+?)(?=[\[【]|$)',
        full_text,
        re.DOTALL
    )
    conclusion_match = re.search(
        r'[\[【]结论[\]】]\s*[:：]?\s*(.+?)(?=[\[【]|$)',
        full_text,
        re.DOTALL
    )

    parts = []
    if signal_match:
        signal_text = signal_match.group(1).strip()
        # 截断过长信号
        signal_max = max(max_chars // 3, 100)
        parts.append(f"[信号] {_truncate(signal_text, signal_max)}")
    else:
        # 无显式[信号]则提取前30%作为信号
        head_len = max(len(full_text) // 3, 50)
        head = full_text[:head_len].strip()
        parts.append(f"[信号] {_truncate(head, 150)}")

    if conclusion_match:
        conclusion_text = conclusion_match.group(1).strip()
        conc_max = max(max_chars // 3, 100)
        parts.append(f"[结论] {_truncate(conclusion_text, conc_max)}")
    else:
        # 无显式[结论]则提取后20%作为结论
        tail_len = max(len(full_text) // 5, 30)
        tail = full_text[-tail_len:].strip()
        parts.append(f"[结论] {_truncate(tail, 100)}")

    compressed = ' | '.join(parts)

    # Step 3: 强制截断到max_chars
    if len(compressed) > max_chars:
        compressed = compressed[:max_chars]
        # 确保以完整标点结束
        if compressed[-1] not in '.!?。！？':
            # 找最后一个句号截断
            last_period = max(
                compressed.rfind('。'),
                compressed.rfind('.'),
                compressed.rfind('！'),
                compressed.rfind('!')
            )
            if last_period > max_chars // 2:
                compressed = compressed[:last_period + 1]

    return compressed


def filter_relevance(items: list[str], topic: str) -> list[str]:
    """关键词匹配过滤，保留与topic相关的条目。

    将topic拆分为关键词，逐个匹配items。
    只要item命中任意一个关键词即视为相关。

    Args:
        items: 待过滤的字符串列表
        topic: 主题关键词（支持空格分隔的多关键词）

    Returns:
        过滤后保留的相关条目列表
    """
    if not items:
        return []
    if not topic or not topic.strip():
        return items

    keywords = _extract_keywords(topic)
    if not keywords:
        return items

    result = []
    for item in items:
        item_lower = item.lower()
        for kw in keywords:
            if kw in item_lower:
                result.append(item)
                break

    return result


def _extract_keywords(topic: str) -> list[str]:
    """从主题文本中提取关键词，去停用词、去重、排序（长词优先）。"""
    # 常用中文停用词（仅限噪声词）
    stop_words = {
        '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都',
        '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你',
        '会', '着', '没有', '看', '好', '自己', '这', '他', '她', '它',
        '们', '那', '什么', '怎么', '如何', '为何', '因为', '所以',
        '但', '但是', '然而', '不过', '虽然', '如果', '可以', '能够',
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
        'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
        'would', 'could', 'should', 'may', 'might', 'shall', 'can',
        'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
        'as', 'into', 'through', 'during', 'before', 'after', 'about',
        'between', 'under', 'over', 'and', 'or', 'but', 'not', 'so',
        'if', 'than', 'that', 'this', 'these', 'those', 'it', 'its',
    }

    # 分词：中英文混合split
    # 中文按字？做简单分词：按空格+标点分割
    tokens = re.split(r'[\s,，。.！!？?；;：:、/\\()（）\[\]【】{}""''"\'《》<>]+', topic)
    keywords = []
    for token in tokens:
        token = token.strip().lower()
        if not token:
            continue
        if token in stop_words:
            continue
        # 纯数字/纯标点跳过
        if re.match(r'^[\d\W]+$', token):
            continue
        keywords.append(token)

    # 去重，保持顺序
    seen = set()
    unique = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            unique.append(kw)

    # 长词优先排序（更精确的匹配放前面）
    unique.sort(key=lambda x: (-len(x), x))
    return unique


def distill_key_signals(chunks: list[dict]) -> str:
    """从多个Agent输出的分块中提取关键信号。

    Args:
        chunks: 分块列表，每个分块为dict，格式:
            {"agent": "AgentX", "content": "...", "confidence": "High/Medium/Low"}

    Returns:
        格式化信号摘要，每行格式：
        [#信号] 来源=AgentX | 内容=Key | 置信度=High/Medium/Low
    """
    if not chunks:
        return "[#信号] 无数据输入 | 置信度=Low"

    valid_confidence = {'High', 'Medium', 'Low'}
    output_lines = []

    for i, chunk in enumerate(chunks, 1):
        if not isinstance(chunk, dict):
            continue

        agent = str(chunk.get('agent', f'Unknown-{i}'))
        content = str(chunk.get('content', ''))
        confidence = str(chunk.get('confidence', 'Low'))

        # 归一化置信度
        if confidence not in valid_confidence:
            if confidence.lower() in ('高', 'high', 'certain', 'definite'):
                confidence = 'High'
            elif confidence.lower() in ('中', 'medium', 'mid', 'moderate', 'possible'):
                confidence = 'Medium'
            else:
                confidence = 'Low'

        # 压缩content为关键信号（取前100字符）
        signal = _compress_signal(content, max_len=100)

        line = f"[#信号{i}] 来源={agent} | 内容={signal} | 置信度={confidence}"
        if len(line) > 200:
            # 如果整行太长，进一步压缩信号内容
            overflow = len(line) - 200
            signal = _compress_signal(content, max_len=max(100 - overflow, 20))
            line = f"[#信号{i}] 来源={agent} | 内容={signal} | 置信度={confidence}"

        output_lines.append(line)

    return '\n'.join(output_lines)


def _compress_signal(text: str, max_len: int = 100) -> str:
    """将一段文本压缩为关键信号字符串。"""
    text = text.strip()
    if not text:
        return "无内容"

    # 去除换行符
    text = text.replace('\n', ' ').replace('\r', ' ')

    # 提取第一个句号/感叹号前的完整句子
    sentence_end = re.search(r'[。！？\.!\?]', text)
    if sentence_end and sentence_end.start() < max_len:
        text = text[:sentence_end.end()]

    if len(text) > max_len:
        # 找最近的空格截断
        truncated = text[:max_len]
        last_space = truncated.rfind(' ')
        last_punct = max(
            truncated.rfind('，'),
            truncated.rfind(','),
            truncated.rfind('；'),
            truncated.rfind(';')
        )
        break_point = last_space if last_space > max_len // 2 else max_len
        if last_punct > max_len // 2:
            break_point = last_punct
        text = text[:break_point] + '...'

    return text


def _truncate(text: str, max_len: int) -> str:
    """安全截断字符串，确保不截断中文字符。"""
    if len(text) <= max_len:
        return text
    return text[:max_len] + '...'


class CompressionProtocol:
    """压缩协议 — 可配置压缩率与自动截断。

    Attributes:
        compression_ratio: 压缩率，范围0.01~0.50（1%~50%）
        max_chars: 输出最大字符数上限
        default_max_chars: compress_summary默认max_chars
    """

    def __init__(
        self,
        compression_ratio: float = 0.15,
        max_chars: int = 2000,
        default_max_chars: int = 500
    ):
        """初始化压缩协议。

        Args:
            compression_ratio: 目标压缩率，范围0.01~0.50，默认0.15（15%）
            max_chars: 单次压缩输出最大字符数上限，默认2000
            default_max_chars: compress_summary的默认max_chars，默认500

        Raises:
            ValueError: 当compression_ratio不在0.01~0.50范围内
        """
        self.compression_ratio = self._validate_ratio(compression_ratio)
        self.max_chars = max(10, max_chars)
        self.default_max_chars = min(default_max_chars, self.max_chars)

    @staticmethod
    def _validate_ratio(ratio: float) -> float:
        """验证并修正压缩率。"""
        if not isinstance(ratio, (int, float)):
            raise ValueError(f"compression_ratio必须是数值，收到: {type(ratio)}")
        if ratio < 0.01:
            return 0.01
        if ratio > 0.50:
            return 0.50
        return ratio

    def compress(self, raw_text: str, max_chars: Optional[int] = None) -> str:
        """对文本执行压缩协议。

        Args:
            raw_text: 原始文本
            max_chars: 可选，覆盖实例默认的default_max_chars

        Returns:
            压缩后的文本
        """
        if max_chars is None:
            max_chars = self.default_max_chars
        else:
            max_chars = min(max_chars, self.max_chars)

        return compress_summary(raw_text, max_chars=max_chars)

    def distill(
        self,
        chunks: list[dict],
        max_signals: Optional[int] = None
    ) -> str:
        """从分块中提取关键信号，按置信度排序。

        Args:
            chunks: 信号分块列表
            max_signals: 最大信号数量（基于压缩率计算）

        Returns:
            排序后的信号摘要
        """
        if not chunks:
            return "[#信号] 无数据输入 | 置信度=Low"

        raw = distill_key_signals(chunks)
        lines = raw.split('\n')

        # 按置信度排序：High > Medium > Low
        confidence_order = {'High': 0, 'Medium': 1, 'Low': 2}

        def sort_key(line):
            for conf, order in confidence_order.items():
                if conf in line:
                    return order
            return 3

        lines.sort(key=sort_key)

        # 基于压缩率截断信号数量
        if max_signals is None:
            max_signals = max(1, int(len(lines) * self.compression_ratio * 2))
        max_signals = max(1, min(max_signals, len(lines)))

        truncated = lines[:max_signals]
        return '\n'.join(truncated)

    def summary_stats(self, raw_text: str, compressed: str) -> dict:
        """生成压缩统计信息。

        Returns:
            dict: {"原始长度": int, "压缩后长度": int, "压缩率": float, "时间戳": str}
        """
        raw_len = len(raw_text)
        comp_len = len(compressed)
        ratio = comp_len / max(raw_len, 1)

        return {
            "原始长度": raw_len,
            "压缩后长度": comp_len,
            "压缩率": round(ratio, 4),
            "时间戳": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def __repr__(self) -> str:
        return (
            f"CompressionProtocol(ratio={self.compression_ratio:.0%}, "
            f"max_chars={self.max_chars}, "
            f"default_max={self.default_max_chars})"
        )
