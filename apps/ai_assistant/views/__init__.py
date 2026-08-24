"""ai-assistant views package — 仅剩豁免端点的函数视图。

Batch 1-3 已迁移到 DRF（../views_drf.py、../views_toolbox_drf.py、
../views_knowledge_drf.py、../views_upload_drf.py）；
此处仅保留 SSE（chat_stream）——工具网关在 views/tool_gateway.py 单独导入。
"""

from .chat_views import chat_stream

__all__ = [
    "chat_stream",
]
