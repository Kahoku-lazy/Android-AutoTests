"""设备提示词历史存档：自动档滚动三份 / 永久档唯一 / 覆盖前先留档（spec: ai-device-prompts 增量）。"""

from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model

from apps.ai_assistant import api
from apps.ai_assistant.models import AIAgent, AIDevicePromptArchive
from shared.auth.jwt_auth import create_access_token

pytestmark = [pytest.mark.unit, pytest.mark.django_db(transaction=True)]

User = get_user_model()

LIST_URL = "/api/ai/device-prompt-archives/"
UPDATE_URL = "/api/ai/device-prompts/update/"


def _headers(user) -> dict:
    return {"HTTP_AUTHORIZATION": f"Bearer {create_access_token(str(user.id))}"}


@pytest.fixture
def admin():
    return User.objects.create_superuser(username="arch_admin", password="x")


@pytest.fixture
def member():
    return User.objects.create_user(username="arch_member", password="x")


@pytest.fixture
def agent(admin):
    """归属超管的活跃智能体 —— get_platform_agent() 会选中它。"""
    return AIAgent.objects.create(
        owner=admin,
        name="平台智能体",
        prompt_planner="p0",
        prompt_executor="e0",
        prompt_verifier="v0",
    )


def _save(agent, n: int, *, archive: str = "auto", user_id: str = "1") -> dict:
    return api.update_device_prompts(
        agent,
        {"planner": f"p{n}", "prompt_x": "ignored", "executor": f"e{n}", "verifier": f"v{n}"},
        archive=archive,
        user_id=user_id,
    )


def _autos(agent) -> list[AIDevicePromptArchive]:
    return list(
        AIDevicePromptArchive.objects.filter(
            agent=agent, kind=AIDevicePromptArchive.KIND_AUTO
        ).order_by("id")
    )


def _current_prompts(agent) -> dict:
    """读库里的当前提示词（先刷新实例，避免读到内存里的旧值）。"""
    agent.refresh_from_db()
    return api.get_device_prompts(agent)


def _permanents(agent) -> list[AIDevicePromptArchive]:
    return list(
        AIDevicePromptArchive.objects.filter(
            agent=agent, kind=AIDevicePromptArchive.KIND_PERMANENT
        ).order_by("id")
    )


# ── 自动档：滚动保留最新三份 ──


def test_auto_archives_keep_latest_three(agent):
    for n in range(1, 5):
        _save(agent, n)

    autos = _autos(agent)
    assert len(autos) == 3
    assert [a.planner for a in autos] == ["p2", "p3", "p4"]


def test_permanent_archive_is_unique_and_survives_pruning(agent):
    _save(agent, 1, archive="permanent")
    for n in range(2, 6):
        _save(agent, n)

    permanents = _permanents(agent)
    assert len(permanents) == 1
    assert permanents[0].planner == "p1"
    assert len(_autos(agent)) == 3


def test_update_without_archive_creates_no_permanent(agent):
    _save(agent, 1)

    assert _permanents(agent) == []
    assert len(_autos(agent)) == 1


def test_unknown_archive_kind_rejected(agent):
    with pytest.raises(ValueError):
        _save(agent, 1, archive="bogus")

    assert AIDevicePromptArchive.objects.filter(agent=agent).count() == 0


def test_restore_keeps_pre_state_and_source_archive(agent):
    _save(agent, 1)  # 自动档 1 = p1（后面要被用来覆盖）
    source = _autos(agent)[0]
    _save(agent, 2)  # 当前 = p2

    api.restore_device_prompt_from_archive(source, user_id="1")

    assert _current_prompts(agent)["planner"] == "p1"
    autos = _autos(agent)
    assert len(autos) <= api.DEVICE_PROMPT_AUTO_KEEP
    # 覆盖前的当前值（p2）已留档，且被用作来源的那份仍在
    assert any(a.planner == "p2" for a in autos)
    assert any(a.id == source.id for a in autos)


def test_restore_rolls_back_when_pre_archive_fails(agent, monkeypatch):
    _save(agent, 1)
    source = _autos(agent)[0]
    _save(agent, 2)
    before = _current_prompts(agent)
    archive_ids = list(
        AIDevicePromptArchive.objects.filter(agent=agent).values_list("id", flat=True)
    )

    def _boom(*args, **kwargs):
        raise RuntimeError("archive write failed")

    monkeypatch.setattr(api, "save_device_prompt_archive", _boom)
    with pytest.raises(RuntimeError):
        api.restore_device_prompt_from_archive(source, user_id="1")

    assert _current_prompts(agent) == before
    assert (
        list(AIDevicePromptArchive.objects.filter(agent=agent).values_list("id", flat=True))
        == archive_ids
    )


# ── HTTP：参数与权限 ──


def test_update_defaults_to_auto_archive(client, admin, agent):
    resp = client.post(
        UPDATE_URL,
        data={"planner": "px", "executor": "ex", "verifier": "vx"},
        content_type="application/json",
        **_headers(admin),
    )

    assert resp.status_code == 200
    assert _permanents(agent) == []
    assert len(_autos(agent)) == 1


def test_update_with_permanent_overwrites_single_archive(client, admin, agent):
    for n in (1, 2):
        resp = client.post(
            UPDATE_URL,
            data={
                "planner": f"p{n}",
                "executor": f"e{n}",
                "verifier": f"v{n}",
                "archive": "permanent",
            },
            content_type="application/json",
            **_headers(admin),
        )
        assert resp.status_code == 200

    permanents = _permanents(agent)
    assert len(permanents) == 1
    assert permanents[0].planner == "p2"


def test_update_with_unknown_archive_returns_400(client, admin, agent):
    resp = client.post(
        UPDATE_URL,
        data={"planner": "p", "executor": "e", "verifier": "v", "archive": "bogus"},
        content_type="application/json",
        **_headers(admin),
    )

    assert resp.status_code == 400
    assert AIDevicePromptArchive.objects.filter(agent=agent).count() == 0


def test_empty_prompt_still_rejected(client, admin, agent):
    resp = client.post(
        UPDATE_URL,
        data={"planner": "   ", "executor": "e", "verifier": "v"},
        content_type="application/json",
        **_headers(admin),
    )

    assert resp.status_code == 400
    assert AIDevicePromptArchive.objects.filter(agent=agent).count() == 0


def test_archive_endpoints_require_superuser(client, member, agent):
    _save(agent, 1)
    _save(agent, 2, archive="permanent")
    permanent = _permanents(agent)[0]

    assert client.get(LIST_URL, **_headers(member)).status_code == 403
    assert client.get(f"{LIST_URL}{permanent.id}/", **_headers(member)).status_code == 403
    assert client.post(f"{LIST_URL}{permanent.id}/delete/", **_headers(member)).status_code == 403
    assert client.post(f"{LIST_URL}{permanent.id}/restore/", **_headers(member)).status_code == 403
    # 非超管的失败请求 MUST NOT 改动数据
    assert len(_permanents(agent)) == 1
    assert _current_prompts(agent)["planner"] == "p2"


def test_superuser_lists_details_and_deletes_permanent(client, admin, agent):
    _save(agent, 1)
    _save(agent, 2, archive="permanent")
    auto = _autos(agent)[0]
    permanent = _permanents(agent)[0]

    listed = client.get(LIST_URL, **_headers(admin))
    assert listed.status_code == 200
    kinds = {item["kind"] for item in listed.json()["data"]["items"]}
    assert kinds == {"auto", "permanent"}

    detail = client.get(f"{LIST_URL}{permanent.id}/", **_headers(admin))
    assert detail.status_code == 200
    assert detail.json()["data"]["planner"] == "p2"

    # 自动档不可手动删除
    assert client.post(f"{LIST_URL}{auto.id}/delete/", **_headers(admin)).status_code == 400

    deleted = client.post(f"{LIST_URL}{permanent.id}/delete/", **_headers(admin))
    assert deleted.status_code == 200
    assert _permanents(agent) == []


def test_restore_endpoint_overwrites_current(client, admin, agent):
    _save(agent, 1)
    source = _autos(agent)[0]
    _save(agent, 2)

    resp = client.post(f"{LIST_URL}{source.id}/restore/", **_headers(admin))

    assert resp.status_code == 200
    assert resp.json()["data"]["planner"] == "p1"
    assert _current_prompts(agent)["planner"] == "p1"


def test_restore_unknown_archive_404(client, admin, agent):
    assert client.post(f"{LIST_URL}999999/restore/", **_headers(admin)).status_code == 404
    assert client.get(f"{LIST_URL}999999/", **_headers(admin)).status_code == 404
