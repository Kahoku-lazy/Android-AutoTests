"""Central WebSocket URL routing — aggregates all module consumers.

Case-editing WS removed with document-case refactor; no WS production points
remain until a new communication channel is explicitly approved.
"""

from django.urls import URLPattern

websocket_urlpatterns: list[URLPattern] = []
