"""单智能体编排：清单、只建一个执行者、连接内复用、事件中间件不进 SOP。"""

from __future__ import annotations

import pytest

from engines.agents.agent_builders import build_ui_executor
from engines.agents.middleware.reply_events import ReplyEventsMiddleware
from engines.agents.workflow import single

pytestmark = [pytest.mark.unit]


def test_catalog_is_empty_and_rejects_unknown_key() -> None:
    """引擎侧清单当前为空（平台角色在 backend_bridge），任何键都报错。"""
    assert single.list_single_agents() == ()
    with pytest.raises(KeyError, match="未知单智能体编排"):
        single.get_single_agent("android_ui")


def test_android_ui_source_does_not_call_sop() -> None:
    """单智能体目录不引用 SOP 工作流。"""
    from pathlib import Path

    root = Path(__file__).resolve().parents[4] / "engines" / "agents" / "workflow" / "single"
    text = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.py"))
    assert "AgentSOPWorkflow" not in text
    assert "ui_auto_workflow" not in text


def test_open_session_builds_one_executor(monkeypatch) -> None:
    """打开会话只建一个执行者，并带默认事件流。"""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    session = single.open_session("serial-1")

    assert session.agent.name == "ui_executor_role"
    assert any(isinstance(item, ReplyEventsMiddleware) for item in session.agent._reply_middlewares)


def test_default_executor_has_no_reply_events(monkeypatch) -> None:
    """SOP 用的执行者自己记录事件，不再挂事件中间件。"""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    agent = build_ui_executor()

    assert not any(isinstance(item, ReplyEventsMiddleware) for item in agent._reply_middlewares)


def test_session_for_rejects_unknown_key(monkeypatch) -> None:
    """清单为空时按连接建会话必须报错，不会静默造角色。"""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    with pytest.raises(KeyError, match="未知单智能体编排"):
        single.session_for("s1", "serial-1", "android_ui")


def test_read_session_events_returns_segment(tmp_path) -> None:
    """只取该会话最后一次开始到结束之间的行，并去掉记录器前缀。"""
    from engines.agents.workflow.single.event_tail import read_session_events

    log = tmp_path / "agent_events.log"
    log.write_text(
        "\n".join(
            [
                "2026-11-11 10:00:00,000 - agent_event - INFO - 单智能体对话 | s1 | 开始 | deepseek-flash",
                "2026-11-11 10:00:01,000 - agent_event - INFO - 开始 | assistant",
                "2026-11-11 10:00:02,000 - agent_event - INFO - 模型费用：0.00000001，0.00000002，0.00000000",
                "2026-11-11 10:00:03,000 - agent_event - INFO - 单智能体对话 | s1 | 结束 | deepseek-flash",
                "2026-11-11 10:00:04,000 - agent_event - INFO - 单智能体对话 | s2 | 开始 | deepseek-flash",
                "2026-11-11 10:00:05,000 - agent_event - INFO - 别的会话",
            ]
        ),
        encoding="utf-8",
    )

    lines = read_session_events("s1", path=log)

    assert len(lines) == 3
    assert lines[0] == "对话开始 · 模型 deepseek-flash"
    assert "开始 | assistant" in lines[1]
    assert "模型费用" in lines[2]
    assert "agent_event" not in lines[1]


def test_read_session_events_missing_log(tmp_path) -> None:
    """日志不存在时返回空列表，不抛异常。"""
    from engines.agents.workflow.single.event_tail import read_session_events

    assert read_session_events("s1", path=tmp_path / "nope.log") == []


@pytest.mark.asyncio
async def test_reply_events_forwards_and_records() -> None:
    """中间件把事件交给接收方，调用方仍能看到原事件。"""
    seen: list[object] = []

    class _Sink:
        def emit(self, record, image_b64: str = "") -> None:
            seen.append(record)

    async def inner(**_kwargs):
        yield type("ModelCallEndEvent", (), {"input_tokens": 1, "output_tokens": 1, "cache_input_tokens": 0})()

    from engines.agents import event_sink

    token = event_sink.bind_sink(_Sink())
    try:
        middleware = ReplyEventsMiddleware()
        async for event in middleware.on_reply(type("A", (), {"name": "ui", "model": None})(), {}, inner):
            assert type(event).__name__ == "ModelCallEndEvent"
    finally:
        event_sink.reset_sink(token)
    assert seen
