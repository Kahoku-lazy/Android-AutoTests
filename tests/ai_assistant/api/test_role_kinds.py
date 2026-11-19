"""Agent 配置类型标签的接口契约：建 / 改 / 清空 / 级联 / 列表下发。"""

from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate

from backend.apps.ai_assistant.models import AIModelConfig, AIRole, AIRoleKind
from backend.apps.ai_assistant.views_drf import RoleViewSet

pytestmark = [pytest.mark.django_db, pytest.mark.api]


@pytest.fixture
def operator(db):
    return get_user_model().objects.create_user(
        username="kind-operator", password="pass", is_superuser=True, is_staff=True
    )


def _config():
    return AIModelConfig.objects.create(
        provider="deepseek",
        api_key_env="DEEPSEEK_API_KEY",
        api_protocol="deepseek",
        model_name="deepseek-flash",
        base_url="https://api.deepseek.com",
    )


def _request(user, method, path, payload=None):
    request = getattr(APIRequestFactory(), method)(path, payload or {}, format="json")
    request.user_id = str(user.id)
    force_authenticate(request, user=user)
    return request


def _post(user, payload):
    request = _request(user, "post", "/api/ai/roles/", payload)
    return RoleViewSet.as_view({"post": "create"})(request)


def _list(user):
    return RoleViewSet.as_view({"get": "list"})(_request(user, "get", "/api/ai/roles/"))


def _patch(user, role_id, payload):
    request = _request(user, "patch", f"/api/ai/roles/{role_id}/", payload)
    return RoleViewSet.as_view({"patch": "partial_update"})(request, role_id=role_id)


def _delete(user, role_id):
    request = _request(user, "delete", f"/api/ai/roles/{role_id}/")
    return RoleViewSet.as_view({"delete": "destroy"})(request, role_id=role_id)


def _create(user, name="页面执行", kinds=("executor",), prompt="你是执行者"):
    config = _config()
    response = _post(
        user,
        {
            "name": name,
            "model_config_id": config.id,
            "system_prompt": prompt,
            "kinds": list(kinds),
        },
    )
    assert response.status_code == 201, response.data
    return response.data


def test_create_persists_single_kind(operator):
    data = _create(operator, kinds=["verifier"])
    assert data["kinds"] == ["verifier"]
    assert AIRoleKind.objects.filter(role__role_id=data["role_id"]).count() == 1


@pytest.mark.parametrize("kinds", [None, []])
def test_create_without_kind_is_400(operator, kinds):
    config = _config()
    payload = {"name": "缺类型", "model_config_id": config.id}
    if kinds is not None:
        payload["kinds"] = kinds
    response = _post(operator, payload)
    assert response.status_code == 400
    assert AIRole.objects.count() == 0


def test_create_with_two_kinds_is_400(operator):
    config = _config()
    response = _post(
        operator,
        {"name": "两类型", "model_config_id": config.id, "kinds": ["executor", "verifier"]},
    )
    assert response.status_code == 400
    assert AIRole.objects.count() == 0


def test_create_with_unknown_kind_is_400(operator):
    config = _config()
    response = _post(
        operator, {"name": "错类型", "model_config_id": config.id, "kinds": ["reviewer"]}
    )
    assert response.status_code == 400
    assert AIRole.objects.count() == 0


def test_create_with_duplicate_kind_is_400(operator):
    config = _config()
    response = _post(
        operator,
        {"name": "重复类型", "model_config_id": config.id, "kinds": ["executor", "executor"]},
    )
    assert response.status_code == 400
    assert AIRole.objects.count() == 0


def test_patch_replaces_kind_and_keeps_other_fields(operator):
    created = _create(operator, kinds=["executor"])
    response = _patch(operator, created["role_id"], {"kinds": ["verifier"]})
    assert response.status_code == 200
    assert response.data["kinds"] == ["verifier"]
    assert response.data["role_id"] == created["role_id"]
    assert response.data["name"] == created["name"]
    assert response.data["system_prompt"] == created["system_prompt"]
    assert AIRoleKind.objects.filter(role__role_id=created["role_id"]).count() == 1


def test_patch_without_kinds_keeps_current_kind(operator):
    created = _create(operator, kinds=["planner"])
    response = _patch(operator, created["role_id"], {"system_prompt": "改提示词"})
    assert response.status_code == 200
    assert response.data["kinds"] == ["planner"]


def test_patch_with_empty_kinds_clears_to_unclassified(operator):
    created = _create(operator, kinds=["executor"])
    response = _patch(operator, created["role_id"], {"kinds": []})
    assert response.status_code == 200
    assert response.data["kinds"] == []
    assert AIRoleKind.objects.filter(role__role_id=created["role_id"]).count() == 0


def test_list_carries_kinds_and_legacy_empty_array(operator):
    config = _config()
    created = _post(
        operator, {"name": "有类型", "model_config_id": config.id, "kinds": ["verifier"]}
    )
    assert created.status_code == 201, created.data
    legacy = AIRole.objects.create(
        role_id="20261115zzz", name="存量无类型", model_config=config, system_prompt=""
    )
    response = _list(operator)
    assert response.status_code == 200
    by_name = {row["name"]: row["kinds"] for row in response.data}
    assert by_name["有类型"] == ["verifier"]
    assert by_name[legacy.name] == []
    assert created.data["role_id"] in [row["role_id"] for row in response.data]


def test_delete_role_cascades_kinds(operator):
    created = _create(operator, kinds=["executor"])
    response = _delete(operator, created["role_id"])
    assert response.status_code == 200
    assert AIRoleKind.objects.count() == 0
