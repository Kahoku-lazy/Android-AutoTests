"""
python -m 调试路径: engines.agents.middleware.tracing

本模块的业务功能如下：
1. setup_tracing: 进程内注册一次 TracerProvider 与 OTLP/HTTP 导出器。
2. build_tracing_middleware: 配了端点才装配框架的 TracingMiddleware。
"""

from __future__ import annotations

import os

from agentscope.middleware import TracingMiddleware

from utils.logs import agent_event_log

ENDPOINT_ENV = "AGENT_TRACING_OTLP_ENDPOINT"
"""OTLP/HTTP 收集端地址，例如 http://localhost:4318/v1/traces。"""

SERVICE_NAME_ENV = "AGENT_TRACING_SERVICE_NAME"
"""写入 span resource 的服务名。"""

DEFAULT_SERVICE_NAME = "android-autotests"

_configured = False


def setup_tracing(endpoint: str, service_name: str = DEFAULT_SERVICE_NAME) -> bool:
    """注册 TracerProvider 与 OTLP/HTTP 导出器；同一进程只注册一次。

    Args:
        endpoint: OTLP/HTTP 收集端地址。
        service_name: 写入 resource 的服务名。

    Returns:
        本次真正完成注册返回 True；已注册或缺少依赖返回 False。

    Raises:
        RuntimeError: 端点为空白。
    """
    global _configured
    endpoint = (endpoint or "").strip()
    if not endpoint:
        raise RuntimeError("OTLP 端点为空白")
    if _configured:
        return False
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import SERVICE_NAME, Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError as exc:
        agent_event_log.warning("缺少 OpenTelemetry 依赖，追踪未启用：%s", exc)
        return False
    provider = TracerProvider(resource=Resource.create({SERVICE_NAME: service_name}))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
    trace.set_tracer_provider(provider)
    _configured = True
    return True


def build_tracing_middleware() -> TracingMiddleware | None:
    """配置了 OTLP 端点时装配追踪中间件。

    Returns:
        追踪中间件；没配端点或依赖缺失时返回 None。

    Raises:
        RuntimeError: 端点配置为空白（空格）时由 `setup_tracing` 抛出。
    """
    endpoint = os.environ.get(ENDPOINT_ENV, "").strip()
    if not endpoint:
        return None
    service_name = os.environ.get(SERVICE_NAME_ENV, "").strip() or DEFAULT_SERVICE_NAME
    if not _configured and not setup_tracing(endpoint, service_name):
        return None
    return TracingMiddleware()
