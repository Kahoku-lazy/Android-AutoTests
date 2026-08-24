"""尾斜杠规范化中间件单测（真机发现 #1）。"""

import pytest

from django.test import RequestFactory

from gateway.normalize_slash import NormalizeTrailingSlashMiddleware

pytestmark = [pytest.mark.unit, pytest.mark.device_pool]


def _apply(path):
    request = RequestFactory().get(path)
    middleware = NormalizeTrailingSlashMiddleware(lambda req: None)
    middleware(request)
    return request.path_info


class TestNormalizeTrailingSlash:
    def test_devices_slashless_gets_slash(self):
        assert _apply("/api/devices") == "/api/devices/"

    def test_runner_tasks_slashless_unchanged(self):
        # runner 路由原生无尾斜杠 → 不得补
        assert _apply("/api/runner/tasks") == "/api/runner/tasks"

    def test_non_api_unchanged(self):
        assert _apply("/admin") == "/admin"

    def test_unknown_path_unchanged(self):
        assert _apply("/api/no-such-path-xyz") == "/api/no-such-path-xyz"

    def test_trailing_slash_unchanged(self):
        assert _apply("/api/devices/") == "/api/devices/"
