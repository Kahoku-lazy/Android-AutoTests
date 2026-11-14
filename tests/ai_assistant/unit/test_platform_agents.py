"""平台对话卡片：清单、键判定、一轮对话与入账。

只测 `ai_assistant/platform_agents.py`；会话与账本都用替身，不联网、不碰真机。
"""

from __future__ import annotations

import pytest

import backend.apps.ai_assistant.platform_agents as platform_agents

pytestmark = [pytest.mark.unit]


@pytest.fixture()
def fake_engine(monkeypatch: pytest.MonkeyPatch):
    """把会话与入账都换成替身，记录调用参数。"""
    calls: dict = {"turns": [], "usages": []}

    class _FakeResult:
        final_text = "好的"
        usages = [{"round": 1, "input_tokens": 10}]
        model = "deepseek-flash"

        class report_path:
            parent = type("P", (), {"name": "20261114_210000"})()

    class _FakeSession:
        async def run_turn(self, message: str, **kwargs):
            calls["turns"].append(message)
            return _FakeResult()

    async def fake_session_for(session_id: str, serial: str, **kwargs):
        calls["session"] = (session_id, serial)
        return _FakeSession()

    def fake_record(usages, *, execution_id: str, model: str = "", **kwargs):
        calls["usages"].append((usages, execution_id, model))
        return len(usages)

    monkeypatch.setattr(
        "engines.backend_bridge.session.session_for", fake_session_for, raising=True
    )
    monkeypatch.setattr(platform_agents, "record_run_usages", fake_record)
    return calls


def test_cards_expose_platform_key():
    """清单里有一张卡，键为 platform_ui，且带上线日期。"""
    cards = platform_agents.list_cards()
    assert [card["key"] for card in cards] == [platform_agents.PLATFORM_KEY]
    assert cards[0]["name"]
    assert cards[0]["summary"]
    assert cards[0]["released_at"]


def test_is_platform_key():
    """平台键判定只认自己的键。"""
    assert platform_agents.is_platform_key(platform_agents.PLATFORM_KEY)
    assert not platform_agents.is_platform_key("android_ui")


def test_stream_turn_rejects_other_key():
    """非平台键直接拒绝，不建会话。"""
    with pytest.raises(ValueError):
        platform_agents.stream_turn(key="android_ui", serial="X", message="hi", session_id="s")

def test_stream_turn_returns_text_and_records_usage(fake_engine):
    """一轮对话返回文本，并用报告目录名作为执行 ID 入账。"""
    text = platform_agents.stream_turn(
        key=platform_agents.PLATFORM_KEY,
        serial="RF8N21MSW7A",
        message="打开设置",
        session_id="s-1",
    )

    assert text == "好的"
    assert fake_engine["turns"] == ["打开设置"]
    assert fake_engine["session"] == ("s-1", "RF8N21MSW7A")
    assert fake_engine["usages"][0][1] == "20261114_210000"
    assert fake_engine["usages"][0][2] == "deepseek-flash"


def test_workflow_list_merges_platform_card():
    """对话清单含平台卡片；引擎侧清单当前为空。"""
    from rest_framework.test import APIRequestFactory, force_authenticate

    from backend.apps.ai_assistant.views_drf import WorkflowListView

    request = APIRequestFactory().get("/api/ai/workflows/")
    force_authenticate(request, user=type("U", (), {"id": 1, "is_authenticated": True})())

    response = WorkflowListView.as_view()(request)

    keys = [card["key"] for card in response.data["workflows"]]
    assert keys == [platform_agents.PLATFORM_KEY]
    assert response.data["workflows"][0]["released_at"]
