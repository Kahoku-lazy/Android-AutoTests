"""引擎侧自研中间件：只放 AgentScope 内置实现覆盖不到的能力，以及统一装配入口。

本模块的业务功能如下：
1. ModelRetryMiddleware: 模型调用的退避重试、备用模型回退与流式不重放。
2. RagContextMiddleware: 复用本地索引，把检索片段追加到系统提示词。
3. build_agent_middlewares: 按固定顺序装配追踪 / 预算 / RAG / 语音 / 记忆入口 / 重试。
"""

from .assembly import build_agent_middlewares
from .budget import build_budget_middleware
from .memory import build_memory_middleware
from .model_retry import (
    ModelRetryMiddleware,
    RetrySettings,
    build_model_retry_middleware,
    is_transient_model_error,
    load_retry_settings,
)
from .rag_context import RagContextMiddleware, build_rag_middleware
from .tracing import build_tracing_middleware, setup_tracing
from .tts import build_tts_middleware

__all__ = [
    "ModelRetryMiddleware",
    "RagContextMiddleware",
    "RetrySettings",
    "build_agent_middlewares",
    "build_budget_middleware",
    "build_memory_middleware",
    "build_model_retry_middleware",
    "build_rag_middleware",
    "build_tracing_middleware",
    "build_tts_middleware",
    "is_transient_model_error",
    "load_retry_settings",
    "setup_tracing",
]
