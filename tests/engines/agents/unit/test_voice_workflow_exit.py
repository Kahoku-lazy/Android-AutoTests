"""语音 workflow 出口：再导出、不直接构造语音智能体。不联网。"""

from __future__ import annotations

import ast
import pathlib

import pytest

pytestmark = [pytest.mark.unit]


def test_voice_exit_reexports_session_transport_and_status() -> None:
    """后端需要的三个名字都能从 workflow.voice 取到。"""
    from engines.agents.workflow import voice

    assert callable(voice.open_voice_session)
    assert callable(voice.build_runtime_status)
    assert voice.WebSocketAudioTransport is not None


def test_open_voice_session_does_not_close_transport() -> None:
    """打开会话只返回对象，不启动、不关闭调用方的传输。"""
    from engines.agents.workflow.voice import open_voice_session

    class _Transport:
        closed = False

        def close(self) -> None:
            """标记被关闭。"""
            self.closed = True

    transport = _Transport()
    session = open_voice_session(object(), transport, lambda payload: None, object())

    assert session.transport is transport
    assert transport.closed is False


def test_voice_workflow_does_not_construct_realtime_agent() -> None:
    """workflow/voice 不得直接构造 RealtimeAgent。"""
    root = pathlib.Path(__file__).resolve().parents[4] / "engines" / "agents" / "workflow" / "voice"
    hits: list[str] = []
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                name = func.id if isinstance(func, ast.Name) else ""
                if name == "RealtimeAgent":
                    hits.append(f"{path}:{node.lineno}")
    assert hits == []
