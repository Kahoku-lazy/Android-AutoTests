"""对话栏实例：同栏复用，新栏不复用，取消互不影响。"""

from __future__ import annotations

import pytest

from engines.backend_bridge.agents import thread_run

pytestmark = [pytest.mark.unit]


@pytest.fixture(autouse=True)
def _clear_threads():
    yield
    thread_run.drop_thread("lane-a")
    thread_run.drop_thread("lane-b")


@pytest.mark.asyncio
async def test_same_lane_reuses_instance(monkeypatch):
    created = {"n": 0}

    async def fake_build(**kwargs):
        created["n"] += 1

        class Bundle:
            agent = object()

        return Bundle()

    monkeypatch.setattr(thread_run, "build_card_agent", fake_build)
    snapshot = {
        "provider": "deepseek",
        "api_key_env": "DEEPSEEK_API_KEY",
        "model_name": "deepseek-flash",
        "tools": [],
    }
    first = await thread_run.thread_agent("lane-a", snapshot)
    second = await thread_run.thread_agent("lane-a", snapshot)
    other = await thread_run.thread_agent("lane-b", snapshot)
    assert first is second
    assert other is not first
    assert created["n"] == 2


def test_cancel_one_lane_does_not_touch_the_other():
    thread_run.thread_cancel_token("lane-a")
    thread_run.thread_cancel_token("lane-b")
    assert thread_run.request_thread_cancel("lane-a") is True
    assert thread_run.thread_cancel_token("lane-a").cancelled is True
    assert thread_run.thread_cancel_token("lane-b").cancelled is False
