import asyncio
import importlib

import pytest

from backend.apps.ai_assistant.services import assistant_threads

pytestmark = pytest.mark.integration


class FakeModel:
    model = "fake-model"


class FakeToolkit:
    async def get_tool_schemas(self):
        return []


class FakeAgent:
    name = "assistant"
    model = FakeModel()
    toolkit = FakeToolkit()

    async def reply_stream(self, message):
        if False:
            yield message


def test_turn_writes_report_artifacts(monkeypatch, tmp_path):
    reports = importlib.import_module("engines.backend_bridge.reports")
    monkeypatch.setattr(reports, "ASSISTANT_LOG_ROOT", tmp_path)

    reply, report_id, usages, model = asyncio.run(
        assistant_threads._reply(
            FakeAgent(),
            "你好",
            assistant_id="A-ART",
            thread_id="thread-art-01",
            snapshot={"provider": "deepseek", "model_name": "fake-model"},
            observer=None,
        )
    )

    root = tmp_path / "A-ART" / "thread-art-01"
    names = sorted(path.name for path in root.rglob("*") if path.is_file())

    assert reply == ""
    assert report_id
    assert model == "fake-model"
    assert usages == []
    assert any(name.endswith(".html") for name in names), names
    assert any(name.endswith(".raw.jsonl") for name in names), names
    assert any(name.endswith(".aligned.json") for name in names), names
    assert any(name.endswith(".jsonl") and not name.endswith(".raw.jsonl") for name in names), names
