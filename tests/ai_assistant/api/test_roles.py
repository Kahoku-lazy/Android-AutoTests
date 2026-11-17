"""角色注册表接口契约：五个方法的状态码、信封、字段集合与错误码。"""

from __future__ import annotations

import re

import pytest

from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.urls import Resolver404, resolve
from rest_framework.test import APIRequestFactory, force_authenticate

from backend.apps.ai_assistant.models import AIModelConfig, AIRole
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


def _config():
    return AIModelConfig.objects.create(
        provider="deepseek",
        api_key_env="DEEPSEEK_API_KEY",
        api_protocol="deepseek",
        model_name="deepseek-flash",
        base_url="https://api.deepseek.com",
    )


def _agent_call(user, method, path, data=None, action="list", **url_kwargs):
    factory = APIRequestFactory()
    request = getattr(factory, method)(path, data or {}, format="json")
    request.user_id = str(user.id)
    force_authenticate(request, user=user)
    view = AgentViewSet.as_view({"get": action, "post": action})
    return view(request, **url_kwargs)


def test_agent_routes_resolve():
    assert resolve("/api/ai/agents/").func.cls is AgentViewSet
    assert resolve("/api/ai/agents/create/").func.cls is AgentViewSet
    assert resolve("/api/ai/agents/7/").func.cls is AgentViewSet
    assert resolve("/api/ai/agents/7/update/").func.cls is AgentViewSet
    assert resolve("/api/ai/agents/7/delete/").func.cls is AgentViewSet


def test_create_agent_requires_operator(user):
    """普通用户不能创建。"""
    response = _agent_call(
        user, "post", "/api/ai/agents/create/", {"name": "新助手"}, action="create_agent"
    )
    assert response.status_code == 403
    assert AIAgent.objects.count() == 0


def test_create_agent_persists_for_operator(db):
    """运营可创建，且不把创建者写成归属人。"""
    from django.contrib.auth.models import Group

    from backend.apps.ai_assistant.models import AIModelConfig
    from backend.shared.users import OPERATOR_GROUP

    operator = get_user_model().objects.create_user(username="agent-ops", password="pass")
    operator.groups.add(Group.objects.get_or_create(name=OPERATOR_GROUP)[0])
    AIModelConfig.objects.create(
        provider="govee", api_key_env="GOVEE_API_KEY", model_name="deepseek-flash"
    )
    response = _agent_call(
        operator,
        "post",
        "/api/ai/agents/create/",
        {"name": "新助手", "api_key_env": "GOVEE_API_KEY", "model_name": "deepseek-flash"},
        action="create_agent",
    )
    assert response.status_code == 201
    agent = AIAgent.objects.get(id=response.data["id"])
    assert agent.owner_id is None
    assert agent.api_key_env == "GOVEE_API_KEY"
    assert agent.model_name == "deepseek-flash"


def test_create_agent_persists_for_superuser(db):
    from backend.apps.ai_assistant.models import AIModelConfig

    admin = get_user_model().objects.create_user(
        username="agent-admin", password="pass", is_superuser=True, is_staff=True
    )
    AIModelConfig.objects.create(
        provider="govee", api_key_env="GOVEE_API_KEY", model_name="deepseek-flash"
    )
    response = _agent_call(
        admin,
        "post",
        "/api/ai/agents/create/",
        {"name": "新助手", "api_key_env": "GOVEE_API_KEY", "model_name": "deepseek-flash"},
        action="create_agent",
    )
    assert response.status_code == 201
    agent = AIAgent.objects.get(id=response.data["id"])
    assert agent.owner_id is None
    assert agent.name == "新助手"
    assert agent.model_name == "deepseek-flash"


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
            "provider": "govee",
            "api_protocol": "openai",
            "api_key_env": "GOVEE_API_KEY",
            "model_name": "deepseek-flash",
            "base_url": "https://example.test/v1",
        },
    )
    second = call(
        "post",
        "/api/ai/model-configs/",
        {
            "provider": "govee",
            "api_protocol": "openai",
            "api_key_env": "GOVEE_API_KEY",
            "base_url": "https://example.test/v1",
            "model_name": "grok-4.7",
        },
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert AIModelConfig.objects.filter(api_key_env="GOVEE_API_KEY").count() == 2
    listed = call("get", "/api/ai/model-configs/")
    assert {row["model_name"] for row in listed.data["configs"]} == {"deepseek-flash", "grok-4.7"}


def test_create_agent_rejects_blank_name(db):
    admin = get_user_model().objects.create_user(
        username="agent-admin2", password="pass", is_superuser=True, is_staff=True
    )
    response = _agent_call(
        admin, "post", "/api/ai/agents/create/", {"name": "   "}, action="create_agent"
    )
    assert response.status_code == 400
    assert AIAgent.objects.count() == 0


def test_agent_list_detail_update_delete(db):
    from backend.apps.ai_assistant.models import AIModelConfig

    admin = get_user_model().objects.create_user(
        username="agent-admin3", password="pass", is_superuser=True, is_staff=True
    )
    AIModelConfig.objects.create(
        provider="govee", api_key_env="GOVEE_API_KEY", model_name="deepseek-flash"
    )
    created = _agent_call(
        admin,
        "post",
        "/api/ai/agents/create/",
        {"name": "助手甲", "api_key_env": "GOVEE_API_KEY", "model_name": "deepseek-flash"},
        action="create_agent",
    )
    agent_id = created.data["id"]

    listed = _agent_call(admin, "get", "/api/ai/agents/")
    assert listed.status_code == 200
    assert agent_id in [row["id"] for row in listed.data["agents"]]

    detail = _agent_call(
        admin, "get", f"/api/ai/agents/{agent_id}/", action="retrieve", pk=agent_id
    )
    assert detail.status_code == 200
    assert detail.data["agent"]["name"] == "助手甲"
    assert "api_key" not in detail.data["agent"]

    updated = _agent_call(
        admin,
        "post",
        f"/api/ai/agents/{agent_id}/update/",
        {"name": "助手甲改", "api_key_env": "GOVEE_API_KEY", "model_name": "deepseek-flash"},
        action="update_agent",
        pk=agent_id,
    )
    assert updated.status_code == 200
    assert AIAgent.objects.get(id=agent_id).name == "助手甲改"

    deleted = _agent_call(
        admin, "post", f"/api/ai/agents/{agent_id}/delete/", action="delete_agent", pk=agent_id
    )
    assert deleted.status_code == 200
    assert not AIAgent.objects.filter(id=agent_id).exists()


def test_agent_write_forbidden_for_normal_user(user):
    agent = AIAgent.objects.create(name="别人的助手", owner=user)
    response = _agent_call(
        user,
        "post",
        f"/api/ai/agents/{agent.id}/update/",
        {"name": "改名"},
        action="update_agent",
        pk=agent.id,
    )
    assert response.status_code == 403
    assert AIAgent.objects.get(id=agent.id).name == "别人的助手"


def test_operator_can_update_any_agent(db, user):
    """运营可以改别人名下的智能体，不按归属人限制。"""
    from django.contrib.auth.models import Group

    from backend.shared.users import OPERATOR_GROUP

    operator = get_user_model().objects.create_user(username="agent-ops2", password="pass")
    from backend.apps.ai_assistant.models import AIModelConfig

    operator.groups.add(Group.objects.get_or_create(name=OPERATOR_GROUP)[0])
    AIModelConfig.objects.create(
        provider="govee", api_key_env="GOVEE_API_KEY", model_name="deepseek-flash"
    )
    agent = AIAgent.objects.create(name="别人的助手", owner=user)
    response = _agent_call(
        operator,
        "post",
        f"/api/ai/agents/{agent.id}/update/",
        {"name": "运营改的", "api_key_env": "GOVEE_API_KEY", "model_name": "deepseek-flash"},
        action="update_agent",
        pk=agent.id,
    )
    assert response.status_code == 200
    assert AIAgent.objects.get(id=agent.id).name == "运营改的"


def test_normal_user_sees_all_agents(user):
    """登录用户看到全部智能体，包括挂在别人名下的。"""
    owner = get_user_model().objects.create_user(username="other-owner", password="pass")
    hidden = AIAgent.objects.create(name="别人的", owner=owner)
    listed = _agent_call(user, "get", "/api/ai/agents/")
    assert listed.status_code == 200
    assert hidden.id in [row["id"] for row in listed.data["agents"]]


def test_missing_agent_detail_is_404(user):
    """记录不存在是 404，不用 403 表示不存在。"""
    response = _agent_call(user, "get", "/api/ai/agents/999999/", action="retrieve", pk=999999)
    assert response.status_code == 404


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
