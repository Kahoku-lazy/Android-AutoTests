"""角色注册表：短标识生成、名称唯一、部分更新、列表排序。"""

from __future__ import annotations

import re

from datetime import timedelta

import pytest

from django.utils import timezone

from backend.apps.ai_assistant.services import agent_configs as api
from backend.apps.ai_assistant.models import AIModelConfig, AIRole
from backend.apps.ai_assistant.services.role_id import generate_role_id, generate_unique_role_id
from backend.apps.ai_assistant.serializers import RoleInputSerializer

pytestmark = [pytest.mark.django_db, pytest.mark.unit]

_ROLE_ID = re.compile(r"^\d{8}[0-9a-z]{3}$")


def test_role_id_matches_date_prefix_format():
    now = timezone.now()
    today = (timezone.localtime(now) if timezone.is_aware(now) else now).strftime("%Y%m%d")
    role_id = generate_role_id()
    assert _ROLE_ID.match(role_id)
    assert role_id.startswith(today)


def test_role_ids_are_unique_across_many_draws():
    # 当日空间 46656，500 次里允许极少数碰撞，但不能集中。
    drawn = {generate_role_id() for _ in range(500)}
    assert len(drawn) >= 490


def test_unique_generator_skips_taken_ids(monkeypatch):
    taken = {"20261115aaa", "20261115aab"}
    sequence = iter(["20261115aaa", "20261115aab", "20261115aac"])
    monkeypatch.setattr(
        "backend.apps.ai_assistant.services.role_id.generate_role_id", lambda: next(sequence)
    )
    assert generate_unique_role_id(taken.__contains__) == "20261115aac"


def test_unique_generator_gives_up_after_limit(monkeypatch):
    monkeypatch.setattr(
        "backend.apps.ai_assistant.services.role_id.generate_role_id", lambda: "20261115aaa"
    )
    with pytest.raises(RuntimeError):
        generate_unique_role_id(lambda _candidate: True)


def _config(name="deepseek-flash"):
    return AIModelConfig.objects.create(
        provider="deepseek",
        api_key_env="DEEPSEEK_API_KEY",
        api_protocol="deepseek",
        model_name=name,
        base_url="https://api.deepseek.com",
    )


def test_create_role_persists_fields():
    config = _config()
    role = api.create_role("页面执行", config.id, "你是执行者")
    assert _ROLE_ID.match(role.role_id)
    assert role.name == "页面执行"
    assert role.model_config_id == config.id
    assert role.system_prompt == "你是执行者"


def test_create_role_allows_blank_prompt():
    role = api.create_role("空提示词", _config().id)
    assert role.system_prompt == ""


def test_create_role_rejects_duplicate_name():
    config = _config()
    api.create_role("页面执行", config.id)
    with pytest.raises(api.RoleConflictError):
        api.create_role("页面执行", config.id)


def test_create_role_retries_when_role_id_collides(monkeypatch):
    """第一次写入撞上已占用的短标识时，换一个再写一次。"""
    config = _config()
    first = api.create_role("已存在", config.id)
    calls = {"n": 0}

    def colliding_then_fresh(_is_taken):
        calls["n"] += 1
        return first.role_id if calls["n"] == 1 else "20990101zzz"

    monkeypatch.setattr(
        "backend.apps.ai_assistant.services.agent_configs.generate_unique_role_id",
        colliding_then_fresh,
    )
    role = api.create_role("新角色", config.id)
    assert role.role_id == "20990101zzz"
    assert calls["n"] == 2


def test_update_keeps_own_name_and_changes_model():
    first = _config("m1")
    second = _config("m2")
    role = api.create_role("页面执行", first.id, "原文")
    updated = api.update_role(role, {"name": "页面执行", "model_config_id": second.id})
    assert updated.model_config_id == second.id
    assert updated.system_prompt == "原文"
    assert updated.role_id == role.role_id


def test_update_rejects_name_taken_by_another():
    config = _config()
    api.create_role("角色甲", config.id)
    other = api.create_role("角色乙", config.id)
    with pytest.raises(api.RoleConflictError):
        api.update_role(other, {"name": "角色甲"})
    assert AIRole.objects.get(pk=other.pk).name == "角色乙"


def test_name_uniqueness_is_case_sensitive():
    config = _config()
    api.create_role("Role", config.id)
    second = api.create_role("role", config.id)
    assert second.name == "role"


def test_list_roles_orders_by_created_at_desc():
    config = _config()
    older = api.create_role("先建", config.id)
    newer = api.create_role("后建", config.id)
    AIRole.objects.filter(pk=older.pk).update(created_at=timezone.now() - timedelta(days=1))
    names = [role.name for role in api.list_roles()]
    assert names == ["后建", "先建"]
    assert newer.name == "后建"


def test_get_role_returns_none_for_unknown():
    assert api.get_role("20261115zzz") is None


def test_delete_role_removes_row():
    role = api.create_role("待删", _config().id)
    api.delete_role(role)
    assert api.get_role(role.role_id) is None


@pytest.mark.parametrize(
    ("payload", "field"),
    [
        ({"name": "", "model_config_id": 1}, "name"),
        ({"name": "   ", "model_config_id": 1}, "name"),
        ({"name": "角色", "model_config_id": 0}, "model_config_id"),
    ],
)
def test_input_serializer_rejects(payload, field):
    serializer = RoleInputSerializer(data=payload)
    assert not serializer.is_valid()
    assert field in serializer.errors


def test_input_serializer_accepts_blank_prompt():
    config = _config()
    serializer = RoleInputSerializer(
        data={"name": "角色", "model_config_id": config.id, "system_prompt": ""}
    )
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["system_prompt"] == ""
