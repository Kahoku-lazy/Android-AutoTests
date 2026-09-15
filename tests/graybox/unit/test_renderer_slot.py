"""DRF 渲染器分档契约：`BrowsableAPIRenderer` 只在 DEBUG 下注册（D0）。

注意：pytest-django 会把运行时 `settings.DEBUG` 改成 False（`django_debug_mode` 默认 false），
而渲染器清单是在 `config/settings.py` **导入时**按 DEBUG 计算好的，因此断言必须对齐导入时的档位
（即环境变量 / `.env` 的 `DJANGO_DEBUG`），不能用运行时 `settings.DEBUG`。
两个档位的行为差异（HTML vs JSON）由变更验证阶段的两个独立进程探针覆盖。
"""

from __future__ import annotations

import os

import pytest

from django.conf import settings

pytestmark = [pytest.mark.unit]

BROWSABLE = "rest_framework.renderers.BrowsableAPIRenderer"


def test_browsable_renderer_follows_debug_flag():
    """信封渲染器永远第一；BrowsableAPIRenderer 仅当导入档位为 DEBUG 时注册。"""
    classes = settings.REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"]
    assert classes[0] == "shared.renderers.EnvelopeJSONRenderer"
    import_debug = os.environ.get("DJANGO_DEBUG", "False").lower() in ("true", "1", "yes")
    assert (BROWSABLE in classes) is import_debug


def test_other_renderer_settings_untouched():
    """鉴权 / 权限 / schema / 未认证用户 四项不受本次分档影响。"""
    rest = settings.REST_FRAMEWORK
    assert rest["DEFAULT_AUTHENTICATION_CLASSES"] == ["shared.auth.drf_auth.JWTAuthentication"]
    assert rest["DEFAULT_PERMISSION_CLASSES"] == ["rest_framework.permissions.IsAuthenticated"]
    assert rest["DEFAULT_SCHEMA_CLASS"] == "drf_spectacular.openapi.AutoSchema"
    assert rest["UNAUTHENTICATED_USER"] is None
