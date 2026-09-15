"""Central WebSocket URL routing — aggregates all module consumers.

Case-editing WS removed with document-case refactor; no WS production points
remain until a new channel is explicitly approved in dev_docs/03-设计与架构/ARCH-00-平台总体架构.md §1.4（五条通信通道）。
"""

from django.urls import URLPattern

websocket_urlpatterns: list[URLPattern] = []
