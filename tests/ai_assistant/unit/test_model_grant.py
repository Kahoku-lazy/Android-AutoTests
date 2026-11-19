"""模型使用名单：空名单拒绝，重复授予不新增，新配置只给超级管理员。"""

from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model

from backend.apps.ai_assistant.api import (
    can_select_model,
    create_model_config,
    grant_model_use,
    list_selectable_model_configs,
)
from backend.apps.ai_assistant.models import ModelUseGrant

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


def _user(name: str, *, superuser: bool = False):
    return get_user_model().objects.create_user(
        username=name,
        password="pass",
        is_superuser=superuser,
    )


def _payload(name: str) -> dict:
    return {
        "provider": "deepseek",
        "api_key_env": "DEEPSEEK_API_KEY",
        "model_name": name,
    }


def test_empty_grant_rejects_every_model():
    user = _user("grant-empty")
    root = _user("grant-root", superuser=True)
    config = create_model_config(_payload("deepseek-empty"))

    assert can_select_model(user.id, config.id) is False
    assert list(list_selectable_model_configs(user.id)) == []
    assert can_select_model(root.id, config.id) is True


def test_repeat_grant_keeps_one_row():
    user = _user("grant-repeat")
    _user("grant-root-2", superuser=True)
    config = create_model_config(_payload("deepseek-repeat"))

    first = grant_model_use(user.id, config.id)
    second = grant_model_use(user.id, config.id)

    assert first.pk == second.pk
    assert ModelUseGrant.objects.filter(user_id=user.id, model_config=config).count() == 1


def test_new_config_is_absent_from_plain_user():
    user = _user("grant-plain")
    _user("grant-root-3", superuser=True)

    config = create_model_config(_payload("deepseek-new"))

    assert config.id not in [row.id for row in list_selectable_model_configs(user.id)]
