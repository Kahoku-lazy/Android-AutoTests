"""
模块功能：➡️ 测试对话接口：建栏不跑模型，缺配置时发送返回 409 🏁
Python 调试：➡️ python -m pytest -c tests/pytest.ini tests/ai_assistant/api/test_assistant_threads.py 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 覆盖 backend/apps/ai_assistant
🏁
"""

from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate

from backend.apps.ai_assistant.models import AIAssistant, AIAssistantMessage, AIAssistantThread
from backend.apps.ai_assistant.views_drf import (
    AssistantThreadDeleteView,
    AssistantThreadDetailView,
    AssistantThreadView,
)

pytestmark = [pytest.mark.django_db, pytest.mark.api]


def _user(name: str = "thread-user"):
    return get_user_model().objects.create_user(username=name, password="pass")


def _card() -> AIAssistant:
    return AIAssistant.objects.create(
        assistant_id="20261116_K3M",
        display_name="小助",
        marker="teal",
        role_id="20261116abc",
        tools=[],
    )


def call(view, user, method, path, data=None, **kwargs):
    factory = APIRequestFactory()
    request = getattr(factory, method)(path, data or {}, format="json")
    request.user_id = str(user.id)
    force_authenticate(request, user=user)
    return view(request, **kwargs)


def test_create_thread_does_not_run_model():
    card = _card()
    response = call(
        AssistantThreadView.as_view(),
        _user(),
        "post",
        "/api/ai/assistants/x/threads/",
        assistant_id=card.assistant_id,
    )
    assert response.status_code == 201
    thread = AIAssistantThread.objects.get(thread_id=response.data["thread_id"])
    assert thread.status == "idle"
    assert thread.snapshot == {}


def test_send_without_role_is_409():
    card = _card()
    created = call(
        AssistantThreadView.as_view(),
        _user(),
        "post",
        "/api/ai/assistants/x/threads/",
        assistant_id=card.assistant_id,
    )
    response = call(
        AssistantThreadDetailView.as_view(),
        _user("thread-user-send"),
        "post",
        "/api/ai/assistants/threads/x/",
        {"content": "你好"},
        thread_id=created.data["thread_id"],
    )
    assert response.status_code == 409


def test_poll_unknown_thread_is_404():
    response = call(
        AssistantThreadDetailView.as_view(),
        _user(),
        "get",
        "/api/ai/assistants/threads/missing/",
        thread_id="missing",
    )
    assert response.status_code == 404


def test_poll_messages_carry_local_time():
    thread = _thread()
    message = thread.messages.create(role=AIAssistantMessage.ROLE_USER, content="你好")
    response = call(
        AssistantThreadDetailView.as_view(),
        _user("thread-user-time"),
        "get",
        "/api/ai/assistants/threads/x/",
        thread_id=thread.thread_id,
    )
    assert response.status_code == 200
    row = response.data["messages"][0]
    assert row["content"] == "你好"
    assert row["created_at"].endswith("+08:00")
    assert row["created_at"].startswith(message.created_at.strftime("%Y-%m-%dT%H:%M"))


def _thread(title: str = "") -> AIAssistantThread:
    card = AIAssistant.objects.filter(assistant_id="20261116_K3M").first() or _card()
    return AIAssistantThread.objects.create(
        thread_id=f"t{card.assistant_id}",
        assistant_id=card.assistant_id,
        title=title,
    )


def test_rename_thread_sets_title():
    thread = _thread()
    response = call(
        AssistantThreadDetailView.as_view(),
        _user(),
        "patch",
        "/api/ai/assistants/threads/x/",
        {"title": "  第一轮排查  "},
        thread_id=thread.thread_id,
    )
    assert response.status_code == 200
    thread.refresh_from_db()
    assert thread.title == "第一轮排查"
    assert response.data["title"] == "第一轮排查"


def test_rename_thread_with_blank_title_resets_to_default():
    thread = _thread(title="旧名字")
    response = call(
        AssistantThreadDetailView.as_view(),
        _user(),
        "patch",
        "/api/ai/assistants/threads/x/",
        {"title": "   "},
        thread_id=thread.thread_id,
    )
    assert response.status_code == 200
    thread.refresh_from_db()
    assert thread.title == ""


def test_rename_unknown_thread_is_404():
    response = call(
        AssistantThreadDetailView.as_view(),
        _user(),
        "patch",
        "/api/ai/assistants/threads/missing/",
        {"title": "x"},
        thread_id="missing",
    )
    assert response.status_code == 404


def test_delete_thread_removes_messages():
    thread = _thread(title="待删")
    thread.messages.create(role=AIAssistantMessage.ROLE_USER, content="你好")
    thread_pk = thread.pk
    response = call(
        AssistantThreadDeleteView.as_view(),
        _user(),
        "post",
        f"/api/ai/assistants/threads/{thread.thread_id}/delete/",
        thread_id=thread.thread_id,
    )
    assert response.status_code == 200
    assert response.data["deleted"] is True
    assert not AIAssistantThread.objects.filter(thread_id=thread.thread_id).exists()
    assert not AIAssistantMessage.objects.filter(thread_id=thread_pk).exists()


def test_delete_unknown_thread_is_404():
    response = call(
        AssistantThreadDeleteView.as_view(),
        _user(),
        "post",
        "/api/ai/assistants/threads/missing/delete/",
        thread_id="missing",
    )
    assert response.status_code == 404
