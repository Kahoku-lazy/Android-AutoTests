"""默认设备执行智能体种子迁移：全新库必种一条、已有则跳过、无主回填、回滚只删自己。"""

from __future__ import annotations

import importlib

import pytest

from django.apps import apps as django_apps
from django.contrib.auth import get_user_model

from backend.apps.ai_assistant.models import AIAgent
from backend.apps.task_list.models import Task

pytestmark = [pytest.mark.unit, pytest.mark.django_db, pytest.mark.ai_assistant]

MIGRATION = importlib.import_module(
    "backend.apps.ai_assistant.migrations.0064_seed_default_device_agent"
)
DEVICE_CONTROL = "device_control"


def _run_seed():
    """以真实 app registry 执行迁移的正向函数（测试库不跑历史迁移）。"""
    MIGRATION.seed_default_device_agent(django_apps, None)


def _run_unseed():
    """执行迁移的反向函数。"""
    MIGRATION.unseed_default_device_agent(django_apps, None)


def _device_agents():
    """当前库里的设备执行智能体。"""
    return AIAgent.objects.filter(task_kind=DEVICE_CONTROL)


def test_seed_creates_device_agent_on_empty_db(db):
    """空库执行种子后存在且仅存在一条设备执行智能体。"""
    assert _device_agents().count() == 0

    _run_seed()

    agents = list(_device_agents())
    assert len(agents) == 1
    agent = agents[0]
    assert agent.name == MIGRATION.AGENT_NAME
    assert agent.model_provider == "deepseek"
    assert agent.model_name == "deepseek-flash"
    assert agent.route_configs == {
        "device_control": {"name": MIGRATION.AGENT_NAME, "avatar": MIGRATION.AGENT_AVATAR}
    }


def test_seed_keeps_ownerless_when_no_superuser(db):
    """库里没有超管时种子仍成功，归属留空（由「无主即共享」兜底）。"""
    _run_seed()

    assert _device_agents().get().owner_id is None


def test_seed_backfills_owner_to_first_superuser(db):
    """库里已有超管时，种出的行与历史无主行都回填给该超管。"""
    admin = get_user_model().objects.create_superuser(
        username="seed-admin", email="seed@local", password="x"
    )
    legacy = AIAgent.objects.create(name="历史无主", owner=None)

    _run_seed()

    assert _device_agents().get().owner_id == admin.id
    legacy.refresh_from_db()
    assert legacy.owner_id == admin.id


def test_seed_skips_when_device_agent_exists(db):
    """已有设备执行智能体（含人工改名的历史行）时不新增、不改写。"""
    existing = AIAgent.objects.create(name="Agent-01号", task_kind=DEVICE_CONTROL, tags="手工")

    _run_seed()

    assert _device_agents().count() == 1
    existing.refresh_from_db()
    assert existing.tags == "手工"


def test_seed_is_repeatable(db):
    """重复执行种子不会产生重复记录。"""
    _run_seed()
    _run_seed()

    assert _device_agents().count() == 1


def test_unseed_removes_seeded_row(db):
    """反向迁移删除本迁移种下的行。"""
    _run_seed()

    _run_unseed()

    assert _device_agents().count() == 0


def test_unseed_keeps_row_with_tasks(db):
    """已挂任务的种子行在回滚时保留，避免级联删业务数据。"""
    _run_seed()
    agent = _device_agents().get()
    Task.objects.create(agent=agent, title="历史任务")

    _run_unseed()

    assert _device_agents().filter(id=agent.id).exists()


def test_unseed_keeps_manually_modified_row(db):
    """人工改过的设备执行行不满足种子特征，回滚不误删。"""
    _run_seed()
    agent = _device_agents().get()
    agent.tags = "人工改过"
    agent.save(update_fields=["tags"])

    _run_unseed()

    assert _device_agents().filter(id=agent.id).exists()
