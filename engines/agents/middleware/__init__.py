"""
文件名: ➡️ __init__.py 🏁
路径: ➡️ engines/agents/middleware/__init__.py 🏁
模块功能：➡️ 引擎侧自研中间件：只放 AgentScope 内置实现覆盖不到的能力，以及统一装配入口 🏁
Python 调试：➡️ python -m engines.agents.middleware 🏁
时间：➡️ 2026-10-28 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-10-30 🏁
类型: ➡️ Harness 配置模块 🏁
简介说明：➡️
1. ModelRetryMiddleware: 模型调用的退避重试、备用模型回退与流式不重放。
2. RagContextMiddleware: 复用本地索引，把检索片段追加到系统提示词。
3. build_agent_middlewares: 按固定顺序装配追踪 / 预算 / RAG / 语音 / 记忆入口 / 重试。
🏁
关联模块：➡️
1. 暂无本地 engines/utils 依赖
🏁
测试：➡️
1. tests/graybox/unit/test_agent_middleware_assembly.py: 中间件装配：默认集合、顺序、各能力开关与单项失败隔离
2. tests/graybox/unit/test_model_retry_middleware.py: 模型重试与回退中间件：分类判定、退避序列、回退、流式首块、环境变量解析
🏁
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
