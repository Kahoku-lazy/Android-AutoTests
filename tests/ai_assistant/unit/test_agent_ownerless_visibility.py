"""无主智能体（迁移种子）按平台共享：普通用户可见、可提交，写权限仍仅超管。"""

from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model

from backend.apps.ai_assistant.api import filter_agents_for_user
from backend.apps.ai_assistant.models import AIAgent
from backend.apps.ai_assistant.permissions import (
    check_agent_owner,
    check_agent_visible,
    check_can_update_agent,
)

pytestmark = [pytest.mark.unit, pytest.mark.django_db, pytest.mark.ai_assistant]


@pytest.fixture
def plate(db):
    """一份最小盘子：超管共享、无主（种子）、他人私有各一条智能体。"""
    user_model = get_user_model()
    admin = user_model.objects.create_superuser(
        username="ownerless-admin", email="admin@local", password="x"
    )
    viewer = user_model.objects.create_user(username="ownerless-viewer", password="x")
    other = user_model.objects.create_user(username="ownerless-other", password="x")
    shared = AIAgent.objects.create(name="Agent-共享", owner=admin)
    ownerless = AIAgent.objects.create(name="Agent-无主", owner=None)
    foreign = AIAgent.objects.create(name="Agent-他人", owner=other)
    return admin, viewer, other, shared, ownerless, foreign


def _listed_ids(user):
    """按接口同款调用取该用户可见的智能体 id 集合。"""
    qs = filter_agents_for_user(AIAgent.objects.all(), str(user.id))
    return set(qs.values_list("id", flat=True))


def test_ownerless_agent_visible_in_list_for_normal_user(plate):
    """普通用户的列表包含无主智能体与超管共享智能体，不含他人私有。"""
    _admin, viewer, _other, shared, ownerless, foreign = plate

    listed = _listed_ids(viewer)

    assert ownerless.id in listed
    assert shared.id in listed
    assert foreign.id not in listed


def test_ownerless_agent_visible_by_id(plate):
    """无主智能体对普通用户按 id 判定为可见（提交前置条件）。"""
    _admin, viewer, _other, _shared, ownerless, _foreign = plate

    assert check_agent_visible(str(viewer.id), ownerless.id) is True


def test_foreign_agent_still_hidden(plate):
    """他人私有智能体对普通用户仍不可见。"""
    _admin, viewer, _other, _shared, _ownerless, foreign = plate

    assert check_agent_visible(str(viewer.id), foreign.id) is False


def test_write_permissions_not_widened_by_ownerless(plate):
    """无主不放开写权限：普通用户既不拥有它，也不能改配置。"""
    admin, viewer, _other, _shared, ownerless, _foreign = plate

    assert check_agent_owner(str(viewer.id), ownerless.id) is False
    assert check_can_update_agent(str(viewer.id), ownerless.id) is False
    assert check_can_update_agent(str(admin.id), ownerless.id) is True
