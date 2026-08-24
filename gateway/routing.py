"""Central WebSocket URL routing — aggregates all module consumers."""

from collections.abc import Callable
from typing import cast

from django.http import HttpResponseBase
from django.urls import URLPattern, re_path

from apps.case_manager.consumers import CaseEditingConsumer
from apps.test_runner.consumers import TestRunConsumer

# django-stubs types re_path for HTTP views; Channels as_asgi() is ASGI-only.
_HttpView = Callable[..., HttpResponseBase]

websocket_urlpatterns: list[URLPattern] = [
    re_path(r"^ws/test-run/(?P<run_id>[^/]+)$", cast(_HttpView, TestRunConsumer.as_asgi())),
    re_path(
        r"^ws/case-editing/(?P<case_id>[^/]+)$", cast(_HttpView, CaseEditingConsumer.as_asgi())
    ),
]
