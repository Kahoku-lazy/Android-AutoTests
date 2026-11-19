"""平台执行会话：按连接复用角色、换设备只改字段、逐轮出报告。

只测 `session.py`；用替身角色，不联网、不碰真机。
"""

from __future__ import annotations

import json

from dataclasses import dataclass, field
from pathlib import Path

import pytest

import engines.backend_bridge.session as session_module

from engines.ae_harness.agents.creator import AgentBundle
from engines.ae_harness.middleware import ObservationMiddleware
from engines.backend_bridge.session import (
    UiExecutorSession,
    drop_session,
    open_session,
    session_for,
)

pytestmark = [pytest.mark.unit]

STAMP = "2026-11-14T21:00:00.000001"
SERIAL = "RF8N21MSW7A"


@dataclass
class ModelCallEndEvent:
    """替身：模型调用结束，带四类 token。"""

    input_tokens: int = 100
    output_tokens: int = 5
    cache_input_tokens: int = 60
    cache_creation_input_tokens: int = 0
    finished_reason: str = "completed"
    reply_id: str = "r1"
    created_at: str = STAMP
    id: str = "e1"
    metadata: dict = field(default_factory=dict)


@dataclass
class TextBlockEndEvent:
    """替身：文本块结束。"""

    block_id: str = "b1"
    text: str = "收到"
    reply_id: str = "r1"
    created_at: str = STAMP
    id: str = "e2"
    metadata: dict = field(default_factory=dict)


class _Toolkit:
    """替身：工具包。"""

    async def get_tool_schemas(self) -> list:
        """返回空工具表。"""
        return []


class _Agent:
    """替身：智能体，记录收到的提示词。"""

    name = "ui_executor"
    toolkit = _Toolkit()

    def __init__(self) -> None:
        """初始化收到的提示词清单。"""
        self.prompts: list[str] = []

    async def reply_stream(self, message: object):
        """产出一轮最小事件流，并记下提示词。"""
        content = getattr(message, "content", "")
        if isinstance(content, list):
            self.prompts.append("".join(getattr(block, "text", "") for block in content))
        else:
            self.prompts.append(str(content))
        yield ModelCallEndEvent()
        yield TextBlockEndEvent()


async def _fake_build(
    *,
    system_prompt="",
    provider=None,
    api_key_env=None,
    model_name=None,
    base_url=None,
    observer=None,
    controls=None,
):
    del system_prompt, controls
    """替身：装配角色。"""
    del provider, api_key_env, model_name, base_url
    watcher = observer if observer is not None else ObservationMiddleware()
    return AgentBundle(agent=_Agent(), api_key_env="OPENAI_API_KEY"), watcher


async def test_session_for_reuses_same_instance(monkeypatch: pytest.MonkeyPatch):
    """同一连接键复用同一个会话，换设备只更新字段。"""
    monkeypatch.setattr(session_module, "build_ui_executor", _fake_build)
    drop_session("s-reuse")

    first = await session_for(
        "s-reuse",
        "AAA",
        system_prompt="你是执行者。",
        provider="openai",
        api_key_env="OPENAI_API_KEY",
        model_name="deepseek-flash",
    )
    second = await session_for(
        "s-reuse",
        "BBB",
        system_prompt="你是执行者。",
        provider="openai",
        api_key_env="OPENAI_API_KEY",
        model_name="deepseek-flash",
    )

    assert first is second
    assert second.serial == "BBB"
    drop_session("s-reuse")


async def test_session_for_requires_session_id(monkeypatch: pytest.MonkeyPatch):
    """空连接键直接拒绝。"""
    monkeypatch.setattr(session_module, "build_ui_executor", _fake_build)
    with pytest.raises(ValueError):
        await session_for(
            "   ",
            "AAA",
            system_prompt="你是执行者。",
            provider="openai",
            api_key_env="OPENAI_API_KEY",
            model_name="deepseek-flash",
        )


async def test_run_turn_prefixes_serial(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """每轮把设备序列号带在消息前面。"""
    monkeypatch.setattr(session_module, "build_ui_executor", _fake_build)
    session = await open_session(
        SERIAL,
        system_prompt="你是执行者。",
        provider="openai",
        api_key_env="OPENAI_API_KEY",
        model_name="deepseek-flash",
    )
    assert isinstance(session, UiExecutorSession)

    result = await session.run_turn("打开设置", report_root=tmp_path)

    assert result.final_text == "收到"
    prompt = session._bundle.agent.prompts[0]  # noqa: SLF001 - 断言替身收到的内容
    assert SERIAL in prompt
    assert prompt.endswith("打开设置")


async def test_run_turn_writes_one_report_per_turn(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """两轮各出一份报告，落在不同时间戳目录。"""
    monkeypatch.setattr(session_module, "build_ui_executor", _fake_build)
    session = await open_session(
        SERIAL,
        system_prompt="你是执行者。",
        provider="openai",
        api_key_env="OPENAI_API_KEY",
        model_name="deepseek-flash",
    )

    first = await session.run_turn("第一轮", report_root=tmp_path)
    second = await session.run_turn("第二轮", report_root=tmp_path)

    assert first.report_path.exists() and second.report_path.exists()
    assert first.report_path.parent != second.report_path.parent
    assert first.tokens == {"input": 100, "output": 5, "cache_hit": 60, "cache_creation": 0}
    assert first.by_api_key_env == {"OPENAI_API_KEY": 1}
    assert first.usages[0]["api_key_env"] == "OPENAI_API_KEY"
    rows = [
        json.loads(line) for line in Path(first.log_path).read_text(encoding="utf-8").splitlines()
    ]
    assert any(row["event"] == "summary" for row in rows)
