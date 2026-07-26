r"""
SSE 流式引擎服务 — 用于AI数智名片对话功能

注入来源: ds2api_toolkit/sse_stream_engine.py
原架构: Go internal/stream/engine.go + internal/sse/parser.go 翻译

核心能力:
  - SSEParser: DeepSeek 私有 SSE 格式解析 ({"v", "p", "o"})
  - SSEStreamEngine: 异步流式消费引擎 (consume / consume_stream)
  - SSEDeduplicator: 去重窗口
  - SseEngineService: 面向名片对话场景的高层接口

独立导入:
    from services.sse_engine import SseEngineService, SSEStreamEngine, SSEParser
"""

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncGenerator, Callable, Optional

logger = logging.getLogger(__name__)


# ==============================================================================
# 数据类型
# ==============================================================================

class StopReason(str, Enum):
    """流停止原因"""
    NONE = ""
    CONTEXT_CANCELLED = "context_cancelled"
    NO_CONTENT_TIMEOUT = "no_content_timeout"
    IDLE_TIMEOUT = "idle_timeout"
    UPSTREAM_COMPLETED = "upstream_completed"
    HANDLER_REQUESTED = "handler_requested"


@dataclass
class ContentPart:
    """SSE 内容片段"""
    text: str
    type: str = "text"  # text | thinking


@dataclass
class ParsedDecision:
    """解析决策"""
    stop: bool = False
    stop_reason: StopReason = StopReason.NONE
    content_seen: bool = False


@dataclass
class ConsumeConfig:
    """消费配置"""
    thinking_enabled: bool = True
    initial_type: str = ""  # "text" | "thinking"
    keep_alive_interval: float = 0.0
    idle_timeout: float = 0.0
    max_keep_alive_no_input: int = 0


@dataclass
class ConsumeHooks:
    """消费钩子"""
    on_parsed: Optional[Callable] = None
    on_keep_alive: Optional[Callable] = None
    on_finalize: Optional[Callable] = None
    on_context_done: Optional[Callable] = None


@dataclass
class LineResult:
    """SSE 行解析结果"""
    data: dict[str, Any] | None = None
    is_done: bool = False
    is_valid: bool = False
    path: str = ""


# ==============================================================================
# SSE 解析器
# ==============================================================================

class SSEParser:
    """
    DeepSeek SSE 解析器

    DeepSeek 使用私有 SSE 格式: {"v": value, "p": path, "o": operation}
    """

    DONE_MARKER = "[DONE]"

    @staticmethod
    def parse_line(raw: str) -> tuple[Optional[dict], bool, bool]:
        """
        解析单行 SSE 数据

        返回: (chunk_data, is_done, is_valid)
        """
        line = raw.strip()
        if not line or not line.startswith("data:"):
            return None, False, False

        data_str = line[5:].strip()
        if data_str == SSEParser.DONE_MARKER:
            return None, True, True

        try:
            chunk = json.loads(data_str)
            return chunk, False, True
        except json.JSONDecodeError:
            return None, False, False

    @staticmethod
    def extract_content(chunk: dict[str, Any],
                        thinking_enabled: bool = True) -> list[ContentPart]:
        """
        从 SSE chunk 中提取内容部分
        """
        parts = []
        v = chunk.get("v")
        path = chunk.get("p", "")

        if v is None:
            return parts

        if SSEParser._should_skip_path(path):
            return parts

        if path.endswith("/status") and isinstance(v, str):
            if v.strip().upper() == "FINISHED":
                return parts

        if isinstance(v, str) and v.strip():
            if "thinking" in path:
                if thinking_enabled:
                    parts.append(ContentPart(text=v, type="thinking"))
            else:
                parts.append(ContentPart(text=v, type="text"))
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    text = item.get("v", "") if "v" in item else item.get("text", "")
                    if text:
                        parts.append(ContentPart(text=str(text)))

        return parts

    @staticmethod
    def _should_skip_path(path: str) -> bool:
        """判断路径是否应该跳过"""
        skip_patterns = [
            "response/fragments/-/status",
            "response/status",
        ]
        for p in skip_patterns:
            if path == p or path.startswith(p):
                return True
        if re.match(r'^response/fragments/-\d+/status$', path):
            return True
        return False

    @staticmethod
    def to_openai_format(parts: list[ContentPart]) -> str:
        """将 ContentPart 列表转成 OpenAI 兼容的 SSE 块 (用于流式HTTP响应)"""
        text_parts = [p.text for p in parts if p.type == "text"]
        thinking_parts = [p.text for p in parts if p.type == "thinking"]

        result = ""
        if thinking_parts:
            result += "".join(thinking_parts) + "\n"
        if text_parts:
            result += "".join(text_parts)
        return result

    @staticmethod
    def merge_with_thinking(parts: list[ContentPart]) -> dict:
        """将 ContentPart 列表合并为 {content, reasoning_content} 格式"""
        text = "".join(p.text for p in parts if p.type == "text")
        thinking = "".join(p.text for p in parts if p.type == "thinking")
        result = {"content": text}
        if thinking:
            result["reasoning_content"] = thinking
        return result


# ==============================================================================
# SSE 流式引擎
# ==============================================================================

class SSEStreamEngine:
    """
    SSE 流式引擎 — select loop 驱动消费

    基于 DS2API internal/stream/engine.go
    """

    def __init__(self):
        self._running = False

    async def consume(self,
                      reader: asyncio.StreamReader,
                      config: ConsumeConfig | None = None,
                      hooks: ConsumeHooks | None = None) -> list[ContentPart]:
        """
        消费 SSE 流, 收集所有内容

        返回: 所有收集到的 ContentPart
        """
        config = config or ConsumeConfig()
        hooks = hooks or ConsumeHooks()
        all_parts: list[ContentPart] = []
        self._running = True

        has_content = False
        last_content_time = time.time()
        keepalive_count = 0

        try:
            while self._running and not reader.at_eof():
                line = await asyncio.wait_for(
                    reader.readline(), timeout=30.0
                )

                if not line:
                    break

                raw = line.decode("utf-8", errors="replace").strip()

                chunk, is_done, is_valid = SSEParser.parse_line(raw)

                if not is_valid:
                    continue

                if is_done:
                    if hooks.on_finalize:
                        hooks.on_finalize(
                            StopReason.UPSTREAM_COMPLETED, None
                        )
                    break

                if chunk:
                    parts = SSEParser.extract_content(
                        chunk, config.thinking_enabled
                    )
                    all_parts.extend(parts)

                    if parts:
                        has_content = True
                        last_content_time = time.time()

                    if hooks.on_parsed:
                        decision = hooks.on_parsed(chunk)
                        if decision and decision.stop:
                            break

                if config.keep_alive_interval > 0:
                    if not has_content:
                        keepalive_count += 1
                        if (config.max_keep_alive_no_input > 0 and
                                keepalive_count >= config.max_keep_alive_no_input):
                            if hooks.on_finalize:
                                hooks.on_finalize(
                                    StopReason.NO_CONTENT_TIMEOUT, None
                                )
                            break

                if config.idle_timeout > 0:
                    elapsed = time.time() - last_content_time
                    if has_content and elapsed > config.idle_timeout:
                        if hooks.on_finalize:
                            hooks.on_finalize(
                                StopReason.IDLE_TIMEOUT, None
                            )
                        break

        except asyncio.TimeoutError:
            if hooks.on_finalize:
                hooks.on_finalize(StopReason.IDLE_TIMEOUT, None)
        except Exception as e:
            logger.error(f"SSE consume error: {e}")
            if hooks.on_finalize:
                hooks.on_finalize(StopReason.HANDLER_REQUESTED, e)
        finally:
            self._running = False

        return all_parts

    async def consume_stream(self,
                             reader: asyncio.StreamReader,
                             config: ConsumeConfig | None = None
                             ) -> AsyncGenerator[ContentPart, None]:
        """
        流式消费 SSE, 逐片段 yield

        类似 Go 的 stream.ConsumeSSE + channel 模式
        """
        config = config or ConsumeConfig()
        self._running = True

        try:
            while self._running and not reader.at_eof():
                line = await asyncio.wait_for(
                    reader.readline(), timeout=30.0
                )
                if not line:
                    break

                raw = line.decode("utf-8", errors="replace").strip()
                chunk, is_done, is_valid = SSEParser.parse_line(raw)

                if not is_valid:
                    continue
                if is_done:
                    break

                if chunk:
                    parts = SSEParser.extract_content(
                        chunk, config.thinking_enabled
                    )
                    for part in parts:
                        yield part

        except asyncio.TimeoutError:
            pass
        finally:
            self._running = False

    def stop(self):
        """停止引擎"""
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running


# ==============================================================================
# 去重工具
# ==============================================================================

class SSEDeduplicator:
    """
    SSE 去重引擎

    防止重复片段被多次处理
    """

    def __init__(self, window_size: int = 100):
        self._seen: set[int] = set()
        self._window: list[int] = []
        self._window_size = window_size

    def is_duplicate(self, chunk: dict) -> bool:
        """检查 chunk 是否重复"""
        chunk_id = hash(json.dumps(chunk, sort_keys=True))
        if chunk_id in self._seen:
            return True
        self._seen.add(chunk_id)
        self._window.append(chunk_id)
        if len(self._window) > self._window_size:
            old = self._window.pop(0)
            self._seen.discard(old)
        return False

    def clear(self):
        self._seen.clear()
        self._window.clear()


def trim_continuation_overlap(prev_text: str, new_text: str, min_overlap: int = 5) -> str:
    """
    修剪续写片段的重叠部分

    当 SSE 分片边界切割了词语, 需要去除重叠
    """
    if not prev_text or not new_text:
        return new_text

    max_overlap = min(len(prev_text), len(new_text), 50)
    for i in range(max_overlap, min_overlap - 1, -1):
        if prev_text[-i:] == new_text[:i]:
            return new_text[i:]
    return new_text


# ==============================================================================
# 高层服务接口 — 面向名片对话场景
# ==============================================================================

class SseEngineService:
    """
    SSE 流式引擎服务 — AI数智名片 对话功能专用

    提供:
      - process_stream: 从 HTTP 流式响应中消费 SSE
      - process_response: 一次性处理并返回完整结果
      - merge_parts: 合并 ContentPart 为文本/思考内容
    """

    def __init__(self):
        self._engine = SSEStreamEngine()
        self._deduplicator = SSEDeduplicator()

    @property
    def engine(self) -> SSEStreamEngine:
        return self._engine

    @property
    def deduplicator(self) -> SSEDeduplicator:
        return self._deduplicator

    async def process_stream(self,
                             reader: asyncio.StreamReader,
                             thinking_enabled: bool = True,
                             on_part: Optional[Callable[[ContentPart], None]] = None,
                             idle_timeout: float = 0.0) -> list[ContentPart]:
        """
        处理 SSE 流并逐片段回调

        Args:
            reader: asyncio 流读取器
            thinking_enabled: 是否启用思考内容解析
            on_part: 每个片段到达时的回调 (用于流式输出)
            idle_timeout: 空闲超时秒数, 0=不启用

        Returns:
            所有收集到的 ContentPart 列表
        """
        config = ConsumeConfig(
            thinking_enabled=thinking_enabled,
            idle_timeout=idle_timeout,
        )

        # 如果提供了 on_part 回调, 拦截 parse 事件
        if on_part:
            original_hooks = ConsumeHooks()
            parts_acc: list[ContentPart] = []

            async def _wrapped_consume():
                nonlocal parts_acc
                self._engine._running = True
                try:
                    while self._engine._running and not reader.at_eof():
                        line = await asyncio.wait_for(reader.readline(), timeout=30.0)
                        if not line:
                            break
                        raw = line.decode("utf-8", errors="replace").strip()
                        chunk, is_done, is_valid = SSEParser.parse_line(raw)
                        if not is_valid:
                            continue
                        if is_done:
                            break
                        if chunk:
                            parts = SSEParser.extract_content(chunk, config.thinking_enabled)
                            for part in parts:
                                parts_acc.append(part)
                                if on_part:
                                    on_part(part)
                except asyncio.TimeoutError:
                    pass
                except Exception as e:
                    logger.error(f"SSE stream error: {e}")
                finally:
                    self._engine._running = False
                return parts_acc

            return await _wrapped_consume()

        # 无回调: 使用标准 consume
        return await self._engine.consume(reader, config=config)

    def merge_parts(self, parts: list[ContentPart]) -> dict:
        """
        合并 ContentPart 为统一格式

        Returns:
            {"content": "...", "reasoning_content": "..."}
        """
        return SSEParser.merge_with_thinking(parts)

    def to_text(self, parts: list[ContentPart]) -> str:
        """将所有部分合并为纯文本"""
        return "".join(p.text for p in parts)

    def to_openai_chunks(self, parts: list[ContentPart]) -> list[dict]:
        """
        将 ContentPart 转为 OpenAI 流式 chunk 格式

        用于兼容 OpenAI 流式 API 的响应格式
        """
        chunks = []
        for i, part in enumerate(parts):
            if part.type == "thinking":
                chunks.append({
                    "choices": [{
                        "delta": {
                            "content": "",
                            "reasoning_content": part.text,
                        },
                        "index": 0,
                    }]
                })
            else:
                chunks.append({
                    "choices": [{
                        "delta": {
                            "content": part.text,
                        },
                        "index": 0,
                    }]
                })
        return chunks

    def reset(self):
        """重置引擎和去重器状态"""
        self._engine.stop()
        self._deduplicator.clear()


# ===== 全局单例 =====
sse_engine_service = SseEngineService()


# ===== 简易测试 =====
if __name__ == "__main__":
    print("SSE Engine Service loaded successfully.")
    print(f"  SSEParser: {SSEParser.parse_line('data: {\"v\":\"hello\",\"p\":\"text\"}')}")
    print(f"  SseEngineService ready: {sse_engine_service is not None}")
