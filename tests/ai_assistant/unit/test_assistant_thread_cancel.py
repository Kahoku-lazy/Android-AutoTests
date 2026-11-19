"""对话栏取消与重启中断：只改状态，不续跑。"""

from __future__ import annotations

import pytest

from backend.apps.ai_assistant.models import AIAssistant, AIAssistantThread
from backend.apps.ai_assistant.services.assistant_threads import (
    cancel_thread,
    mark_interrupted_running,
)

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


def _thread(status: str, suffix: str) -> AIAssistantThread:
    AIAssistant.objects.create(
        assistant_id=f"20261116_{suffix}",
        display_name="小助",
        marker="teal",
        role_id="20261116abc",
    )
    return AIAssistantThread.objects.create(
        thread_id=f"lane-{suffix}",
        assistant_id=f"20261116_{suffix}",
        status=status,
    )


def test_cancel_only_changes_running_lane():
    running = _thread(AIAssistantThread.STATUS_RUNNING, "AAA")
    idle = _thread(AIAssistantThread.STATUS_IDLE, "AAB")
    assert cancel_thread(running) is True
    assert cancel_thread(idle) is False
    running.refresh_from_db()
    idle.refresh_from_db()
    assert running.status == AIAssistantThread.STATUS_CANCELLED
    assert idle.status == AIAssistantThread.STATUS_IDLE


def test_startup_marks_running_as_interrupted():
    running = _thread(AIAssistantThread.STATUS_RUNNING, "AAC")
    done = _thread(AIAssistantThread.STATUS_DONE, "AAD")
    assert mark_interrupted_running() == 1
    running.refresh_from_db()
    done.refresh_from_db()
    assert running.status == AIAssistantThread.STATUS_INTERRUPTED
    assert done.status == AIAssistantThread.STATUS_DONE
