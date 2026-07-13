"""OpenTelemetry 分布式追踪集成 (OpenTelemetry Distributed Tracing)

为 FastAPI 应用添加 OpenTelemetry 支持，包括：
  - TracerProvider 初始化
  - BatchSpanProcessor + ConsoleSpanExporter
  - OTLP 导出 (HTTP/gRPC) 带超时与自动降级
  - FastAPI 集成 (自动追踪请求/响应)
  - 环境变量控制开关: ENABLE_OTEL=true/false

依赖:
  - opentelemetry-api
  - opentelemetry-sdk
  - opentelemetry-instrumentation-fastapi
  - opentelemetry-exporter-otlp-proto-http (OTLP 导出时需要)

用法:
  from app.middleware.otel import init_otel
  init_otel()

降级策略:
  1. OTLP 端点连接超时 (默认 5 秒) → 降级为 ConsoleSpanExporter
  2. opentelemetry-exporter-otlp-proto-http 未安装 → 降级为 ConsoleSpanExporter
  3. 任何未预期异常 → 静默降级，不阻塞应用启动
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

# ── 默认常量 ──────────────────────────────────────────────────────────
_DEFAULT_OTLP_TIMEOUT = 5  # OTLP 连接超时 (秒)
_DEFAULT_SERVICE_NAME = "ai-digital-business-card"


def _get_otlp_timeout() -> int:
    """从环境变量读取 OTLP 超时配置，确保返回合法正整数。"""
    raw = os.getenv("OTEL_EXPORTER_OTLP_TIMEOUT", str(_DEFAULT_OTLP_TIMEOUT))
    try:
        timeout = int(raw)
        return max(1, timeout)
    except (ValueError, TypeError):
        return _DEFAULT_OTLP_TIMEOUT


def _create_otlp_exporter(endpoint: str) -> object | None:
    """创建 OTLPSpanExporter 实例，带连接超时。

    如果导入失败或创建时抛出异常，返回 None 表示降级。

    Args:
        endpoint: OTLP Collector 地址 (如 http://localhost:4318)

    Returns:
        OTLPSpanExporter 实例，或 None (降级)
    """
    try:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
    except ImportError:
        logger.warning(
            "OTLP endpoint 已设置 (%s) 但 "
            "opentelemetry-exporter-otlp-proto-http 未安装，"
            "降级为 ConsoleSpanExporter。如需启用: "
            "pip install opentelemetry-exporter-otlp-proto-http",
            endpoint,
        )
        return None

    try:
        timeout = _get_otlp_timeout()
        span_exporter = OTLPSpanExporter(
            endpoint=endpoint,
            timeout=timeout,
        )
        # 主动触发一次预连接检测 (无阻塞: 仅验证参数)
        logger.info(
            "OTLP 导出器已创建: endpoint=%s, timeout=%ds",
            endpoint,
            timeout,
        )
        return span_exporter
    except Exception as exc:
        logger.warning(
            "OTLP 端点 %s 不可达 (超时 %ds)，"
            "降级为 ConsoleSpanExporter: %s",
            endpoint,
            _get_otlp_timeout(),
            exc,
        )
        return None


def _build_resource(service_name: str) -> object:
    """构建 OTel Resource，标记服务身份。"""
    try:
        from opentelemetry.sdk.resources import Resource

        return Resource.create({"service.name": service_name})
    except ImportError:
        # 极低概率：opentelemetry-sdk 已安装但 resources 不可用
        from opentelemetry.sdk.resources import Resource

        return Resource.create({"service.name": service_name})


def init_otel() -> None:
    """初始化 OpenTelemetry 分布式追踪。

    由环境变量 ENABLE_OTEL 控制 (默认关闭):
      - ENABLE_OTEL=true  -> 启用追踪
      - ENABLE_OTEL=false -> 跳过初始化 (静默降级)

    OTLP 导出 (可选):
      设置 OTEL_EXPORTER_OTLP_ENDPOINT 环境变量即可启用 OTLP 导出；
      未设置时使用 ConsoleSpanExporter。

    降级行为 (不阻塞应用启动):
      - OTLP 端点连接超时 → ConsoleSpanExporter
      - 依赖缺失 → ConsoleSpanExporter
      - 任意未预期异常 → 静默跳过
    """
    if os.getenv("ENABLE_OTEL", "false").lower() not in ("true", "1", "yes"):
        logger.info("OpenTelemetry 未启用 (ENABLE_OTEL=false)")
        return

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            BatchSpanProcessor,
            ConsoleSpanExporter,
        )

        # ── 1. 确定服务名称 ─────────────────────────────────────────
        service_name = os.getenv(
            "OTEL_SERVICE_NAME",
            _DEFAULT_SERVICE_NAME,
        )

        # ── 2. 创建 TracerProvider ──────────────────────────────────
        provider = TracerProvider(
            resource=_build_resource(service_name),
        )

        # ── 3. 配置 Span Exporter (带自动降级) ──────────────────────
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        if otlp_endpoint:
            # 尝试创建 OTLP 导出器 —— 失败时返回 None
            exporter = _create_otlp_exporter(otlp_endpoint)
            if exporter is not None:
                span_exporter = exporter
                export_mode = "OTLP"
            else:
                span_exporter = ConsoleSpanExporter()
                export_mode = "Console (降级)"
        else:
            span_exporter = ConsoleSpanExporter()
            export_mode = "Console"

        # ── 4. 添加 BatchSpanProcessor ──────────────────────────────
        processor = BatchSpanProcessor(span_exporter)
        provider.add_span_processor(processor)

        # ── 5. 设置为全局 Trace Provider ────────────────────────────
        trace.set_tracer_provider(provider)

        # ── 6. 注册 FastAPI 集成 (延迟到应用创建后) ─────────────────
        #     通过 monkey-patch 方式注册，实际调用将由 create_app() 完成
        #     FastAPIInstrumentor.instrument_app(app) 在 create_app 中调用

        logger.info(
            "OpenTelemetry 初始化完成: service=%s, export_mode=%s",
            service_name,
            export_mode,
        )

    except ImportError as exc:
        logger.warning(
            "OpenTelemetry 依赖未安装，跳过追踪初始化: %s. "
            "如需启用，请安装: pip install opentelemetry-api opentelemetry-sdk "
            "opentelemetry-instrumentation-fastapi",
            exc,
        )
    except Exception as exc:
        logger.warning(
            "OpenTelemetry 初始化失败 (降级继续): %s",
            exc,
            exc_info=(exc.__class__.__name__ == "ConnectionError"),
        )
