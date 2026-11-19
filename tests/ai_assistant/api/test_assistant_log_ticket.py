"""报告打开：无票 401，换票后可打开一次。"""

from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate

from backend.apps.ai_assistant.models import AIAssistant, AIAssistantThread
from backend.apps.ai_assistant.views_drf import AssistantThreadLogView

pytestmark = [pytest.mark.django_db, pytest.mark.api]


def _thread() -> AIAssistantThread:
    AIAssistant.objects.create(
        assistant_id="20261116_K3M",
        display_name="小助",
        marker="teal",
        role_id="20261116abc",
    )
    return AIAssistantThread.objects.create(
        thread_id="lane-ticket",
        assistant_id="20261116_K3M",
        status=AIAssistantThread.STATUS_DONE,
    )


def test_open_without_ticket_is_401():
    thread = _thread()
    factory = APIRequestFactory()
    request = factory.get("/api/ai/assistants/threads/x/logs/20261116_180000/")
    response = AssistantThreadLogView.as_view()(
        request, thread_id=thread.thread_id, report_id="20261116_180000"
    )
    assert response.status_code == 401


def test_running_does_not_issue_ticket():
    thread = _thread()
    thread.status = AIAssistantThread.STATUS_RUNNING
    thread.save(update_fields=["status"])
    user = get_user_model().objects.create_user(username="ticket-user", password="pass")
    factory = APIRequestFactory()
    request = factory.post("/api/ai/assistants/threads/x/logs/20261116_180000/")
    request.user_id = str(user.id)
    force_authenticate(request, user=user)
    response = AssistantThreadLogView.as_view()(
        request, thread_id=thread.thread_id, report_id="20261116_180000"
    )
    assert response.status_code == 409
    assert "ticket" not in response.data
