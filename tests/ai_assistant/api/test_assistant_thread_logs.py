from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate

from backend.apps.ai_assistant.models import AIAssistant, AIAssistantMessage, AIAssistantThread
from backend.apps.ai_assistant.views_drf import AssistantThreadLogView

pytestmark = [pytest.mark.django_db, pytest.mark.api]


def _thread(status: str) -> AIAssistantThread:
    AIAssistant.objects.create(
        assistant_id="20261116_K3M",
        display_name="小助",
        marker="teal",
        role_id="20261116abc",
    )
    return AIAssistantThread.objects.create(
        thread_id="lane1",
        assistant_id="20261116_K3M",
        status=status,
    )


def call(thread_id: str, report_id: str = ""):
    user = get_user_model().objects.create_user(
        username=f"log-{thread_id}-{report_id or 'list'}", password="pass"
    )
    factory = APIRequestFactory()
    request = factory.get("/api/ai/assistants/threads/x/logs/")
    request.user_id = str(user.id)
    force_authenticate(request, user=user)
    return AssistantThreadLogView.as_view()(request, thread_id=thread_id, report_id=report_id)


def test_unknown_report_is_404():
    thread = _thread(AIAssistantThread.STATUS_DONE)
    response = call(thread.thread_id, "../secret")
    assert response.status_code == 404
    assert "logs" not in str(response.data)


def test_running_report_is_409():
    thread = _thread(AIAssistantThread.STATUS_RUNNING)
    response = call(thread.thread_id, "20261116_180000")
    assert response.status_code == 409


def test_log_rows_carry_local_time():
    thread = _thread(AIAssistantThread.STATUS_DONE)
    message = thread.messages.create(
        role=AIAssistantMessage.ROLE_ASSISTANT,
        content="跑完了",
        report_id="20261116_180000",
    )
    response = call(thread.thread_id)
    assert response.status_code == 200
    row = response.data[0]
    assert row["created_at"].endswith("+08:00")
    assert row["created_at"].startswith(message.created_at.strftime("%Y-%m-%dT%H:%M"))


def test_running_log_row_has_no_time():
    thread = _thread(AIAssistantThread.STATUS_RUNNING)
    response = call(thread.thread_id)
    assert response.status_code == 200
    assert response.data[-1] == {
        "report_id": "",
        "summary": "还在写",
        "created_at": "",
        "writing": True,
    }
