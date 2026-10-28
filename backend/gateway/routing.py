"""Central WebSocket URL routing — aggregates all module consumers.

知识库助手实时语音是本平台当前唯一的 WebSocket 生产点：
`/ws/knowledge-assistant/?token=<access_token>`。

该通道只承载知识库助手的音频、转写、打断与播放进度；任务进度与列表
仍走 HTTP 轮询（见 PRD 非功能约束的唯一例外）。
"""

from django.urls import URLPattern, path

from backend.apps.knowledge_assistant.consumer import KnowledgeAssistantConsumer

websocket_urlpatterns: list[URLPattern] = [
    path("ws/knowledge-assistant/", KnowledgeAssistantConsumer.as_asgi()),
]
