"""Central WebSocket URL routing — aggregates all module consumers.

Case-editing WS removed with document-case refactor; no WS production points
remain until a new channel is explicitly approved in architecture.md.
"""

from django.urls import URLPattern

websocket_urlpatterns: list[URLPattern] = []
