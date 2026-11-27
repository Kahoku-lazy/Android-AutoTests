import threading

import pytest

from backend.apps.ai_assistant.models import AIAssistantMessage, AIAssistantThread
from backend.apps.ai_assistant.services import assistant_threads

pytestmark = pytest.mark.integration


@pytest.fixture
def conversation(db):
    thread = AIAssistantThread.objects.create(
        thread_id="thread-loop-0001",
        assistant_id="A-LOOP",
        title="事件循环回归",
        snapshot={},
        status=AIAssistantThread.STATUS_RUNNING,
    )
    thread.messages.create(role=AIAssistantMessage.ROLE_USER, content="你好")
    return thread


def test_two_turns_reuse_one_event_loop(monkeypatch, conversation):
    worker_ids: list[int] = []

    async def fake_agent(thread_id, snapshot):
        worker_ids.append(threading.get_ident())
        return object()

    async def fake_reply(
        agent, content, *, assistant_id, thread_id, snapshot=None, observer=None, report_title=None
    ):
        worker_ids.append(threading.get_ident())
        return "好的", "report-loop", [], "fake-model"

    monkeypatch.setattr(
        "engines.backend_bridge.agents.thread_run.thread_agent",
        fake_agent,
    )
    monkeypatch.setattr(assistant_threads, "_reply", fake_reply)

    assistant_threads._run_turn(conversation.thread_id)
    assert AIAssistantThread.objects.get(pk=conversation.pk).status == (
        AIAssistantThread.STATUS_DONE
    )

    AIAssistantThread.objects.filter(pk=conversation.pk).update(
        status=AIAssistantThread.STATUS_RUNNING
    )
    assistant_threads._run_turn(conversation.thread_id)

    assert worker_ids, "回合没有在事件循环里执行"
    assert len(set(worker_ids)) == 1, f"两轮对话跑在不同线程/循环上：{worker_ids}"
    assert worker_ids[0] != threading.get_ident(), "回合不应留在调用线程里跑"
    assert AIAssistantThread.objects.get(pk=conversation.pk).status == (
        AIAssistantThread.STATUS_DONE
    )
    replies = conversation.messages.filter(role=AIAssistantMessage.ROLE_ASSISTANT).count()
    assert replies == 2
