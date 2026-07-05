"""Central WebSocket URL routing — aggregates all module consumers."""
from django.urls import re_path
from apps.element_locator.consumers import ScreenshotConsumer
from apps.test_runner.consumers import TestRunConsumer

websocket_urlpatterns = [
    re_path(r'^ws/screenshot$', ScreenshotConsumer.as_asgi()),
    re_path(r'^ws/test-run/(?P<run_id>[^/]+)$', TestRunConsumer.as_asgi()),
]
