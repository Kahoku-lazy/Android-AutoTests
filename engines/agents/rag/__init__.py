"""
文件名: ➡️ __init__.py 🏁
路径: ➡️ engines/agents/rag/__init__.py 🏁
模块功能：➡️ 本地知识库：按库索引、检索和命令行探针 🏁
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

from .catalog import KnowledgeBaseSpec, load_knowledge_catalog
from .config import RagConfig, load_rag_config
from .service import KnowledgeBaseService, KnowledgeHit, RagService
from .store import SQLiteVectorStore

__all__ = [
    "KnowledgeBaseService",
    "KnowledgeBaseSpec",
    "KnowledgeHit",
    "RagConfig",
    "RagService",
    "SQLiteVectorStore",
    "load_knowledge_catalog",
    "load_rag_config",
]
