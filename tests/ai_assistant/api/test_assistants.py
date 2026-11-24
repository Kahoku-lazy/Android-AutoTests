"""助手名片接口：写限助手作者，读限登录，列表不含头像正文。"""

from __future__ import annotations

import io

import pytest

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import resolve
from PIL import Image
from rest_framework.test import APIRequestFactory, force_authenticate

from backend.apps.ai_assistant.api import grant_assistant_author
from backend.apps.ai_assistant.models import AIModelConfig, AIRole
from backend.apps.ai_assistant.views_drf import AssistantAvatarView, AssistantViewSet
from backend.shared.users import OPERATOR_GROUP

pytestmark = [pytest.mark.django_db, pytest.mark.api]


def _png() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (64, 64), (10, 80, 40)).save(buffer, format="PNG")
    return buffer.getvalue()


def _role() -> AIRole:
    config = AIModelConfig.objects.create(
        provider="deepseek",
        api_key_env="DEEPSEEK_API_KEY",
        model_name="deepseek-flash",
    )
    return AIRole.objects.create(role_id="20261116abc", name="执行配置", model_config=config)


def _operator():
    user = get_user_model().objects.create_user(username="ops-assistant", password="pass")
    user.groups.add(Group.objects.create(name=OPERATOR_GROUP))
    return user


def _author(name: str = "author-assistant"):
    user = get_user_model().objects.create_user(username=name, password="pass")
    grant_assistant_author(user.id)
    return user


def _user():
    return get_user_model().objects.create_user(username="plain-assistant", password="pass")


def call(user, method, data=None, *, action="list", assistant_id=None, files=None):
    factory = APIRequestFactory()
    request = getattr(factory, method)(
        "/api/ai/assistants/",
        data or {},
        format="multipart" if files else "json",
    )
    if files:
        request = getattr(factory, method)("/api/ai/assistants/", {**(data or {}), **files})
    request.user_id = str(user.id)
    force_authenticate(request, user=user)
    if assistant_id:
        view = AssistantViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        )
        return view(request, assistant_id=assistant_id)
    view = AssistantViewSet.as_view({"get": action, "post": "create"})
    return view(request)


def test_routes_resolve():
    assert resolve("/api/ai/assistants/").func.cls is AssistantViewSet
    assert resolve("/api/ai/assistants/20261116_K3M/").func.cls is AssistantViewSet
    assert resolve("/api/ai/assistants/20261116_K3M/avatar/").func.cls is AssistantAvatarView


def test_author_create_returns_201_without_avatar_body():
    role = _role()
    response = call(
        _author(), "post", {"display_name": "小助", "role_id": role.role_id, "tools": []}
    )
    assert response.status_code == 201
    assert response.data["display_name"] == "小助"
    assert response.data["role_name"] == "执行配置"
    assert "avatar" not in response.data
    assert response.data["has_avatar"] is False


def test_operator_create_is_403_and_writes_nothing():
    role = _role()
    response = call(
        _operator(), "post", {"display_name": "小助", "role_id": role.role_id, "tools": []}
    )
    assert response.status_code == 403
    assert response.renderer_context["view"].get_queryset().count() == 0


def test_plain_user_create_is_403():
    role = _role()
    response = call(_user(), "post", {"display_name": "小助", "role_id": role.role_id})
    assert response.status_code == 403


def test_anonymous_list_is_401(client):
    response = client.get("/api/ai/assistants/")
    assert response.status_code == 401


def test_unknown_assistant_is_404():
    user = _user()
    factory = APIRequestFactory()
    request = factory.get("/api/ai/assistants/20261116_ZZZ/")
    request.user_id = str(user.id)
    force_authenticate(request, user=user)
    response = AssistantViewSet.as_view({"get": "retrieve"})(request, assistant_id="20261116_ZZZ")
    assert response.status_code == 404


def test_delete_rejects_assistant_bound_by_workflow_and_names_it():
    """被工作流占用时拒绝删除，提示点名到那条工作流，名片保持原样。"""
    from backend.apps.ai_assistant.models import AIAssistant, AISopWorkflow

    role = _role()
    author = _author("author-delete-bound")
    created = call(author, "post", {"display_name": "小助", "role_id": role.role_id, "tools": []})
    assistant_id = created.data["assistant_id"]
    AISopWorkflow.objects.create(
        name="登录回归",
        executor_assistant_id=assistant_id,
        verifier_assistant_id=assistant_id,
    )

    response = call(author, "delete", assistant_id=assistant_id)

    assert response.status_code == 400
    assert "登录回归" in str(response.data)
    assert AIAssistant.objects.filter(assistant_id=assistant_id).exists()


def test_delete_removes_unbound_assistant():
    """没有工作流引用时删除成功，名片不再存在。"""
    from backend.apps.ai_assistant.models import AIAssistant

    role = _role()
    author = _author("author-delete-free")
    created = call(author, "post", {"display_name": "小助", "role_id": role.role_id, "tools": []})
    assistant_id = created.data["assistant_id"]

    response = call(author, "delete", assistant_id=assistant_id)

    assert response.status_code == 200
    assert not AIAssistant.objects.filter(assistant_id=assistant_id).exists()


def test_avatar_endpoint_returns_body():
    role = _role()
    created = call(
        _author(),
        "post",
        {"display_name": "小助", "role_id": role.role_id},
        files={"avatar": io.BytesIO(_png())},
    )
    assert created.status_code == 201
    user = _user()
    factory = APIRequestFactory()
    request = factory.get("/api/ai/assistants/x/avatar/")
    request.user_id = str(user.id)
    force_authenticate(request, user=user)
    response = AssistantAvatarView.as_view()(request, assistant_id=created.data["assistant_id"])
    assert response.status_code == 200
    assert response.data["avatar"]
    listed = call(_author("author-assistant-list"), "get")
    assert "avatar" not in listed.data[0]
