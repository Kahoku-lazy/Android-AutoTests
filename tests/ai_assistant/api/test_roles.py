"""
模块功能：➡️ 角色注册表接口契约：五个方法的状态码、信封、字段集合与错误码 🏁
Python 调试：➡️ python -m pytest -c tests/pytest.ini tests/ai_assistant/api/test_roles.py 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 覆盖 backend/apps/ai_assistant、backend/gateway/middleware.py
🏁
"""

from __future__ import annotations

import re

import pytest

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import RequestFactory
from django.urls import Resolver404, resolve
from rest_framework.test import APIRequestFactory, force_authenticate

from backend.apps.ai_assistant.models import AIRole, ModelUseGrant
from backend.apps.ai_assistant.views_drf import RoleViewSet
from backend.gateway.middleware import JWTAuthenticationMiddleware
from backend.shared.users import OPERATOR_GROUP

pytestmark = [pytest.mark.django_db, pytest.mark.api]

_ROLE_ID = re.compile(r"^\d{8}[0-9a-z]{3}$")
_FIELDS = {
    "role_id",
    "name",
    "model_config_id",
    "provider",
    "api_key_env",
    "model_name",
    "base_url",
    "api_protocol",
    "system_prompt",
    "kinds",
    "created_at",
    "updated_at",
}


@pytest.fixture
def user(db):
    """运营账号：角色写操作要求 is_operator（超管天然算运营）。"""
    user = get_user_model().objects.create_user(username="role-user", password="pass")
    user.groups.add(Group.objects.get_or_create(name=OPERATOR_GROUP)[0])
    return user


def _config(user) -> int:
    """建一份模型配置并把使用名单授权给该用户（空名单对任何模型都为 False）。"""
    from backend.apps.ai_assistant.models import AIModelConfig

    config = AIModelConfig.objects.create(
        provider="deepseek",
        api_key_env="DEEPSEEK_API_KEY",
        api_protocol="deepseek",
        model_name="deepseek-flash",
        base_url="https://api.deepseek.com",
    )
    ModelUseGrant.objects.create(user_id=user.id, model_config=config)
    return config.id


def call(user, method, path, data=None, **url_kwargs):
    """直调视图：DRF 鉴权放行，绕过网关中间件（401 另有中间件用例覆盖）。"""
    factory = APIRequestFactory()
    request = getattr(factory, method)(path, data or {}, format="json")
    request.user_id = str(user.id)
    force_authenticate(request, user=user)
    return (
        RoleViewSet.as_view({"get": "list", "post": "create"})(request)
        if not url_kwargs
        else (
            RoleViewSet.as_view(
                {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
            )(request, **url_kwargs)
        )
    )


def test_model_config_round_trip(db):
    """模型配置能创建、列出，同一个密钥可以有两个模型。"""
    from backend.apps.ai_assistant.models import AIModelConfig
    from backend.apps.ai_assistant.views_drf import ModelConfigViewSet

    admin = get_user_model().objects.create_user(
        username="model-admin", password="pass", is_superuser=True, is_staff=True
    )
    factory = APIRequestFactory()

    def call(method, path, data=None, pk=None):
        request = getattr(factory, method)(path, data or {}, format="json")
        request.user_id = str(admin.id)
        force_authenticate(request, user=admin)
        view = ModelConfigViewSet.as_view({"get": "list", "post": "create", "delete": "destroy"})
        return view(request, pk=pk) if pk else view(request)

    first = call(
        "post",
        "/api/ai/model-configs/",
        {
            "provider": "openai",
            "api_protocol": "openai",
            "api_key_env": "OPENAI_API_KEY",
            "model_name": "deepseek-flash",
            "base_url": "https://example.test/v1",
        },
    )
    second = call(
        "post",
        "/api/ai/model-configs/",
        {
            "provider": "openai",
            "api_protocol": "openai",
            "api_key_env": "OPENAI_API_KEY",
            "base_url": "https://example.test/v1",
            "model_name": "grok-4.7",
        },
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert AIModelConfig.objects.filter(api_key_env="OPENAI_API_KEY").count() == 2
    listed = call("get", "/api/ai/model-configs/")
    assert {row["model_name"] for row in listed.data["configs"]} == {"deepseek-flash", "grok-4.7"}


def test_routes_resolve():
    assert resolve("/api/ai/roles/").func.cls.__name__ == "RoleViewSet"
    match = resolve("/api/ai/roles/20261115a3f/")
    assert match.func.cls.__name__ == "RoleViewSet"
    assert match.kwargs["role_id"] == "20261115a3f"
    with pytest.raises(Resolver404):
        resolve("/api/ai/roles")


def test_anonymous_request_is_rejected_by_middleware():
    request = RequestFactory().get("/api/ai/roles/")
    response = JWTAuthenticationMiddleware(lambda _request: None)(request)
    assert response.status_code == 401


def test_create_returns_201_and_full_record(user):
    response = call(
        user,
        "post",
        "/api/ai/roles/",
        {
            "name": "页面执行",
            "model_config_id": _config(user),
            "system_prompt": "你是执行者",
            "kinds": ["executor"],
        },
    )
    assert response.status_code == 201
    body = {"status": True, "data": response.data}
    assert body["status"] is True
    assert set(body["data"]) == _FIELDS
    assert _ROLE_ID.match(body["data"]["role_id"])
    assert body["data"]["name"] == "页面执行"
    assert "T" in body["data"]["created_at"]


def test_list_orders_newest_first(user):
    config_id = _config(user)
    for index in range(3):
        AIRole.objects.create(
            role_id=f"20261115a0{index}", name=f"角色{index}", model_config_id=config_id
        )
    response = call(user, "get", "/api/ai/roles/")
    assert response.status_code == 200
    names = [row["name"] for row in response.data]
    assert names == ["角色2", "角色1", "角色0"]


def test_partial_update_changes_only_submitted_field(user):
    config_id = _config(user)
    created = call(
        user,
        "post",
        "/api/ai/roles/",
        {
            "name": "页面执行",
            "model_config_id": config_id,
            "system_prompt": "原文",
            "kinds": ["executor"],
        },
    ).data
    response = call(
        user,
        "patch",
        f"/api/ai/roles/{created['role_id']}/",
        {"system_prompt": "新文"},
        role_id=created["role_id"],
    )
    assert response.status_code == 200
    data = response.data
    assert data["system_prompt"] == "新文"
    assert data["name"] == "页面执行"
    assert data["model_config_id"] == config_id
    assert data["role_id"] == created["role_id"]


def test_delete_then_detail_is_404(user):
    created = call(
        user,
        "post",
        "/api/ai/roles/",
        {"name": "待删", "model_config_id": _config(user), "kinds": ["executor"]},
    ).data
    deleted = call(
        user, "delete", f"/api/ai/roles/{created['role_id']}/", role_id=created["role_id"]
    )
    assert deleted.status_code == 200
    assert deleted.data == {"role_id": created["role_id"]}
    missing = call(user, "get", f"/api/ai/roles/{created['role_id']}/", role_id=created["role_id"])
    assert missing.status_code == 404


def test_unknown_role_id_is_404(user):
    response = call(user, "get", "/api/ai/roles/20261115zzz/", role_id="20261115zzz")
    assert response.status_code == 404


def test_duplicate_name_is_409(user):
    payload = {"name": "页面执行", "model_config_id": _config(user), "kinds": ["executor"]}
    assert call(user, "post", "/api/ai/roles/", payload).status_code == 201
    duplicate = call(user, "post", "/api/ai/roles/", payload)
    assert duplicate.status_code == 409
    assert AIRole.objects.count() == 1


def test_blank_fields_are_400(user):
    response = call(user, "post", "/api/ai/roles/", {"name": "   "})
    assert response.status_code == 400
    assert AIRole.objects.count() == 0


def test_model_outside_grant_is_403(user):
    """未进入本人使用名单的模型不能拿来建角色（名单为空即全部为 False）。"""
    from backend.apps.ai_assistant.models import AIModelConfig

    config = AIModelConfig.objects.create(
        provider="deepseek",
        api_key_env="DEEPSEEK_API_KEY",
        model_name="未授权模型",
    )
    response = call(
        user,
        "post",
        "/api/ai/roles/",
        {"name": "随便", "model_config_id": config.id, "kinds": ["executor"]},
    )
    assert response.status_code == 403
    assert AIRole.objects.count() == 0
