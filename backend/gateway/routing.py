"""Central WebSocket URL routing — aggregates all module consumers.

当前**没有** WebSocket 生产点：知识助手（实时语音 + 文字问答）已整体下线
（变更 retire-engines-agents），平台不再有语音通道。任务进度与列表走 HTTP 轮询。

保留本模块与空清单，是为了让 `backend/config/asgi.py` 的装配保持稳定：
将来真出现 WebSocket 需求时，在这里登记 consumer 即可，不改 ASGI 入口。
"""

from django.urls import URLPattern

websocket_urlpatterns: list[URLPattern] = []
