"""
模块功能：➡️ 模型名单接口：列表、角色保存和运营后台三类入口 🏁
Python 调试：➡️ python -m pytest -c tests/pytest.ini tests/ai_assistant/api/test_model_grant.py 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 覆盖 backend/apps/ai_assistant、backend/apps/ops_console、backend/shared/users.py
🏁
"""

from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIRequestFactory, force_authenticate

from backend.apps.ai_assistant.models import AIModelConfig
from backend.apps.ai_assistant.views_drf import ModelConfigViewSet, RoleViewSet
from backend.apps.ops_console.views import OpsUserModelGrantView
from backend.shared.users import OPERATOR_GROUP

pytestmark = [pytest.mark.django_db, pytest.mark.api]


def _user(name: str, *, superuser: bool = False, operator: bool = False):
    user = get_user_model().objects.create_user(
        username=name,
        password="pass",
        is_superuser=superuser,
    )
    if operator:
        user.groups.add(Group.objects.get_or_create(name=OPERATOR_GROUP)[0])
    return user


def _config(name: str = "deepseek-listed") -> AIModelConfig:
    return AIModelConfig.objects.create(
        provider="deepseek",
        api_key_env="DEEPSEEK_API_KEY",
        model_name=name,
    )


def _call(user, method: str, path: str, data=None, *, view=None, query="", **kwargs):
    factory = APIRequestFactory()
    request = getattr(factory, method)(path + query, data or {}, format="json")
    request.user_id = str(user.id)
    force_authenticate(request, user=user)
    return view(request, **kwargs)


def test_selectable_list_hides_models_outside_grant():
    root = _user("model-root", superuser=True)
    plain = _user("model-plain")
    own = _config("deepseek-own")
    _config("deepseek-hidden")
    from backend.apps.ai_assistant.api import grant_model_use

    grant_model_use(plain.id, own.id)

    response = _call(
        plain,
        "get",
        "/api/ai/model-configs/",
        view=ModelConfigViewSet.as_view({"get": "list"}),
        query="?selectable=1",
    )

    assert response.status_code == 200
    names = [row["model_name"] for row in response.data["configs"]]
    assert names == ["deepseek-own"]
    assert root.id != plain.id


def test_role_create_rejects_model_outside_grant():
    operator = _user("model-operator", operator=True, superuser=True)
    hidden = _config("deepseek-role")
    from backend.apps.ai_assistant.api import revoke_model_use

    revoke_model_use(operator.id, hidden.id)
    response = _call(
        operator,
        "post",
        "/api/ai/roles/",
        {"name": "不能用", "model_config_id": hidden.id, "kinds": ["executor"]},
        view=RoleViewSet.as_view({"post": "create"}),
    )

    assert response.status_code == 403


def test_operator_cannot_edit_grant_but_superuser_can():
    operator = _user("model-ops", operator=True)
    root = _user("model-root-2", superuser=True)
    target = _user("model-target")
    config = _config("deepseek-grant")
    payload = {"model_config_id": config.id, "enabled": True}

    denied = _call(
        operator,
        "post",
        f"/api/ops/users/{target.id}/model-grants/",
        payload,
        view=OpsUserModelGrantView.as_view(),
        user_id=target.id,
    )
    allowed = _call(
        root,
        "post",
        f"/api/ops/users/{target.id}/model-grants/",
        payload,
        view=OpsUserModelGrantView.as_view(),
        user_id=target.id,
    )

    assert denied.status_code == 403
    assert allowed.status_code == 200
