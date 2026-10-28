"""
python -m 调试路径: backend.apps.knowledge_assistant.views

本模块的业务功能如下：
1. KnowledgeAssistantStatusAPIView: 返回知识库助手的就绪状态。

视图只分发；引擎配置在 engines.agents.realtime_vocie，日志路径在 runtime.py。
"""

from __future__ import annotations

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from .runtime import build_status_payload


class KnowledgeAssistantStatusAPIView(APIView):
    """GET /api/knowledge-assistant/status/ — 知识库助手就绪状态（登录可读）。"""

    @extend_schema(
        responses=OpenApiTypes.OBJECT,
        tags=["knowledge-assistant"],
        description="返回知识库助手是否启用、是否就绪、不可用原因、模型/音色与日志路径。",
    )
    def get(self, request):
        """返回不含密钥的就绪信息。"""
        return Response(build_status_payload())
