"""真模型评测的运行与逐条过程：创建、追加、收尾都经 api。"""

from __future__ import annotations

import pytest

from backend.apps.ai_assistant import api
from backend.apps.ai_assistant.models import AssistantLiveRun, AssistantLiveSample

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


def test_live_run_appends_sample_then_finishes():
    run = api.create_live_run("assistant", "20261118_EV1", {"role_id": "r"}, ["A1"])
    assert run.status == AssistantLiveRun.STATUS_PENDING
    assert run.progress_total == 1

    api.append_live_sample(
        run.pk, "A1", "同栏第二句", True, [], [{"role": "assistant", "text": "你好"}]
    )
    api.finish_live_run(run.pk, status=AssistantLiveRun.STATUS_DONE, failures=[])

    stored = api.get_live_run(run.pk)
    assert stored.status == AssistantLiveRun.STATUS_DONE
    assert stored.progress_done == 1
    assert stored.failures == []
    sample = AssistantLiveSample.objects.get(run=stored)
    assert sample.passed is True
    assert sample.steps[0]["text"] == "你好"


def test_live_runner_records_the_model_reply(monkeypatch):
    monkeypatch.setattr(
        "engines.backend_bridge.workflow.eval_probe.build_card_agent",
        lambda **_kwargs: _bundle(),
    )
    monkeypatch.setattr(
        "backend.apps.ai_assistant.services.eval_billing.record_eval_usages",
        lambda *_args, **_kwargs: 0,
    )
    run = api.create_live_run("assistant", "missing", {"role_id": "r"}, ["A1"])

    from backend.apps.ai_assistant.services.live_runner import execute

    execute(run.pk)

    stored = api.get_live_run(run.pk)
    texts = [step["text"] for step in stored.samples.first().steps]
    assert stored.status == "done"
    assert "模型回复：你好" in texts
    assert "模型回复：上一句我说了什么" in texts


class TextBlockEndEvent:
    def __init__(self, text: str):
        self.text = text


class _Agent:
    def __init__(self):
        self.toolkit = _Toolkit()

    async def reply_stream(self, message):
        text = message.content
        if isinstance(text, list):
            text = "".join(str(getattr(item, "text", item)) for item in text)
        yield TextBlockEndEvent(f"模型回复：{text}")


class _Toolkit:
    async def add_tool(self, _tool):
        return None


class _Bundle:
    agent = _Agent()
    api_key_env = "DEEPSEEK_API_KEY"


async def _bundle():
    return _Bundle()


def test_old_scripted_record_does_not_release():
    api.record_eval("assistant", "20261118_EV1", {"role_id": "r"}, [])

    assert api.eval_passed("assistant", "20261118_EV1", {"role_id": "r"}) is False
