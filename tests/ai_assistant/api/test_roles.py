"""角色注册表接口契约：五个方法的状态码、信封、字段集合与错误码。

旧 AIAgent / AgentViewSet 用例已删除（2026-11-19）：模型与视图已演进为
AIAssistant / AssistantViewSet（路由 /api/ai/assistants/），旧用例引用已退役
名字，执行必 NameError；经需求方确认按失效用例删除，不改写。
"""

from __future__ import annotations

import re

import pytest

from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.urls import Resolver404, resolve
from rest_framework.test import APIRequestFactory, force_authenticate

from backend.apps.ai_assistant.models import AIRole
from backend.apps.ai_assistant.views_drf import RoleViewSet
from backend.gateway.middleware import JWTAuthenticationMiddleware

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
    "created_at",
    "updated_at",
}


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(username="role-user", password="pass")


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
        {"name": "页面执行", "model_name": "deepseek-flash", "system_prompt": "你是执行者"},
    )
    assert response.status_code == 201
    body = {"status": True, "data": response.data}
    assert body["status"] is True
    assert set(body["data"]) == _FIELDS
    assert _ROLE_ID.match(body["data"]["role_id"])
    assert body["data"]["name"] == "页面执行"
    assert "T" in body["data"]["created_at"]


def test_list_orders_newest_first(user):
    for index in range(3):
        AIRole.objects.create(role_id=f"20261115a0{index}", name=f"角色{index}", model_name="m")
    response = call(user, "get", "/api/ai/roles/")
    assert response.status_code == 200
    names = [row["name"] for row in response.data]
    assert names == ["角色2", "角色1", "角色0"]


def test_partial_update_changes_only_submitted_field(user):
    created = call(
        user,
        "post",
        "/api/ai/roles/",
        {"name": "页面执行", "model_name": "m1", "system_prompt": "原文"},
    ).data
    response = call(
        user,
        "patch",
        f"/api/ai/roles/{created['role_id']}/",
        {"model_name": "m2"},
        role_id=created["role_id"],
    )
    assert response.status_code == 200
    data = response.data
    assert data["model_name"] == "m2"
    assert data["name"] == "页面执行"
    assert data["system_prompt"] == "原文"
    assert data["role_id"] == created["role_id"]


def test_delete_then_detail_is_404(user):
    created = call(user, "post", "/api/ai/roles/", {"name": "待删", "model_name": "m"}).data
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
    payload = {"name": "页面执行", "model_name": "m"}
    assert call(user, "post", "/api/ai/roles/", payload).status_code == 201
    duplicate = call(user, "post", "/api/ai/roles/", payload)
    assert duplicate.status_code == 409
    assert AIRole.objects.count() == 1


def test_blank_fields_are_400(user):
    response = call(user, "post", "/api/ai/roles/", {"name": "   ", "model_name": ""})
    assert response.status_code == 400
    assert AIRole.objects.count() == 0


def test_arbitrary_model_name_is_accepted(user):
    response = call(user, "post", "/api/ai/roles/", {"name": "随便", "model_name": "不存在的模型"})
    assert response.status_code == 201
    assert response.data["model_name"] == "不存在的模型"
