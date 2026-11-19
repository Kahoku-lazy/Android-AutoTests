"""助手日志目录与报告编号解析。"""

from __future__ import annotations

import pytest

from backend.apps.ai_assistant.models import AIAssistant, AIAssistantMessage, AIAssistantThread
from backend.apps.ai_assistant.services.assistant_threads import (
    resolve_thread_report,
    thread_log_dir,
)
from engines.backend_bridge.reports import ASSISTANT_LOG_ROOT, REPORT_ROOT

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


def test_assistant_log_root_is_separate_from_sop():
    assert ASSISTANT_LOG_ROOT.name == "assistants"
    assert ASSISTANT_LOG_ROOT != REPORT_ROOT


def test_report_id_must_stay_inside_lane(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "engines.backend_bridge.reports.paths.ASSISTANT_LOG_ROOT",
        tmp_path,
    )
    AIAssistant.objects.create(
        assistant_id="20261116_K3M",
        display_name="小助",
        marker="teal",
        role_id="20261116abc",
    )
    thread = AIAssistantThread.objects.create(
        thread_id="lane1",
        assistant_id="20261116_K3M",
        status=AIAssistantThread.STATUS_DONE,
    )
    folder = thread_log_dir(thread.assistant_id, thread.thread_id) / "20261116_180000"
    folder.mkdir(parents=True)
    (folder / "20261116_180000_assistant.html").write_text("<p>ok</p>", encoding="utf-8")
    AIAssistantMessage.objects.create(
        thread=thread,
        role=AIAssistantMessage.ROLE_ASSISTANT,
        content="完成",
        report_id="20261116_180000",
    )
    assert resolve_thread_report(thread, "20261116_180000") is not None
    assert resolve_thread_report(thread, "../other") is None
    assert resolve_thread_report(thread, "20261116_180000/../../secret") is None
