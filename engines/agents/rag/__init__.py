"""
文件名: ➡️ __init__.py 🏁
路径: ➡️ engines/agents/rag/__init__.py 🏁
模块功能：➡️ AgentScope RAG 引擎：本地资料索引、检索与 LLM 上下文格式化 🏁
Python 调试：➡️ python -m engines.agents.rag 🏁
时间：➡️ 2026-10-30 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-10-30 🏁
类型: ➡️ Harness 配置模块 🏁
简介说明：➡️
1. （模块无公开类/函数，见源码）
🏁
关联模块：➡️
1. 暂无本地 engines/utils 依赖
🏁
测试：➡️
1. 暂无专门单测
🏁
"""

from .config import RagConfig, load_rag_config
from .service import RagHit, RagService, format_context
from .store import SQLiteVectorStore
from .tool import build_rag_tool

__all__ = [
    "RagConfig",
    "RagHit",
    "RagService",
    "SQLiteVectorStore",
    "build_rag_tool",
    "format_context",
    "load_rag_config",
]
