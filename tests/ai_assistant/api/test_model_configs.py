"""
模块功能：➡️ 模型配置接口：语音合成免地址、聊天空地址拒绝、语音合成再次编辑保存 🏁
Python 调试：➡️ python -m pytest -c tests/pytest.ini tests/ai_assistant/api/test_model_configs.py 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 覆盖 backend/apps/ai_assistant
🏁
"""

from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate

from backend.apps.ai_assistant.models import AIModelConfig
from backend.apps.ai_assistant.views_drf import ModelConfigViewSet

pytestmark = [pytest.mark.django_db, pytest.mark.api]

_PATH = "/api/ai/model-configs/"


@pytest.fixture
def call(db):
    """直调视图：超管身份，绕过网关中间件。"""
    admin = get_user_model().objects.create_user(
        username="model-config-admin", password="pass", is_superuser=True, is_staff=True
    )
    factory = APIRequestFactory()

    def _call(method, data=None, pk=None):
        request = getattr(factory, method)(_PATH, data or {}, format="json")
        request.user_id = str(admin.id)
        force_authenticate(request, user=admin)
        view = ModelConfigViewSet.as_view(
            {"get": "list", "post": "create", "patch": "partial_update", "delete": "destroy"}
        )
        return view(request, pk=pk) if pk else view(request)

    return _call


def _tts_payload(**overrides):
    payload = {
        "provider": "dashscope",
        "api_protocol": "dashscope",
        "model_kind": "tts",
        "api_key_env": "DASHSCOPE_API_KEY",
        "base_url": "",
        "model_name": "qwen3-tts-flash",
        "voice": "Cherry",
    }
    payload.update(overrides)
    return payload


def test_tts_config_allows_blank_base_url(call):
    response = call("post", _tts_payload())

    assert response.status_code == 201
    config = AIModelConfig.objects.get(model_name="qwen3-tts-flash")
    assert config.model_kind == "tts"
    assert config.base_url == ""
    assert response.data["base_url"] == ""


def test_chat_config_still_rejects_blank_base_url(call):
    response = call(
        "post",
        {
            "provider": "deepseek",
            "api_protocol": "deepseek",
            "model_kind": "chat",
            "api_key_env": "DEEPSEEK_API_KEY",
            "base_url": "",
            "model_name": "deepseek-flash",
        },
    )

    assert response.status_code == 400
    assert "API 地址不能为空" in str(response.data)
    assert AIModelConfig.objects.count() == 0


def test_tts_config_can_be_saved_again_without_base_url(call):
    config = AIModelConfig.objects.create(
        provider="dashscope",
        api_key_env="DASHSCOPE_API_KEY",
        model_kind="tts",
        base_url="",
        model_name="qwen3-tts-flash",
        voice="Cherry",
    )

    response = call(
        "patch",
        _tts_payload(model_name="qwen3-tts-flash-2", voice="Serena"),
        pk=config.id,
    )

    assert response.status_code == 200
    config.refresh_from_db()
    assert config.model_name == "qwen3-tts-flash-2"
    assert config.voice == "Serena"
    assert config.base_url == ""
