"""平台运行入口：返回结构化结果、报告落盘、不打印。

只测 `run.py` 的契约；用替身智能体，不联网、不碰真机。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

import engines.backend_bridge.session as session_module

from engines.ae_harness.agents.creator import AgentBundle
from engines.ae_harness.middleware import ObservationMiddleware
from engines.backend_bridge.run import UiRunResult, run_ui_task

pytestmark = [pytest.mark.unit]

STAMP = "2026-11-14T19:00:00.000001"


@dataclass
class ModelCallStartEvent:
    """替身：模型调用开始。"""

    reply_id: str = "r1"
    model_name: str = "deepseek-flash"
    created_at: str = STAMP
    id: str = "e1"
    metadata: dict = field(default_factory=dict)


@dataclass
class ModelCallEndEvent:
    """替身：模型调用结束，带四类 token。"""

    input_tokens: int = 100
    output_tokens: int = 10
    cache_input_tokens: int = 60
    cache_creation_input_tokens: int = 0
    finished_reason: str = "completed"
    reply_id: str = "r1"
    created_at: str = STAMP
    id: str = "e2"
    metadata: dict = field(default_factory=dict)


@dataclass
class TextBlockEndEvent:
    """替身：文本块结束，给出最终文本。"""

    block_id: str = "b1"
    text: str = "OK"
    reply_id: str = "r1"
    created_at: str = STAMP
    id: str = "e3"
    metadata: dict = field(default_factory=dict)


class _Toolkit:
    """替身：工具包，只提供取 schema 的异步方法。"""

    async def get_tool_schemas(self) -> list:
        """返回空工具表。"""
        return []


class _Agent:
    """替身：智能体，只提供名字、工具包与事件流。"""

    name = "ui_executor"
    toolkit = _Toolkit()

    async def reply_stream(self, message: object):
        """产出一轮最小事件流。"""
        del message
        yield ModelCallStartEvent()
        yield ModelCallEndEvent()
        yield TextBlockEndEvent()


async def _fake_build(
    *,
    system_prompt: str = "",
    provider: str | None = None,
    api_key_env: str | None = None,
    model_name: str | None = None,
    base_url: str | None = None,
    observer: ObservationMiddleware | None = None,
    controls: list | None = None,
) -> tuple[AgentBundle, ObservationMiddleware]:
    """替身：装配角色，返回假智能体与观测中间件。"""
    del system_prompt, provider, api_key_env, model_name, base_url, controls
    watcher = observer if observer is not None else ObservationMiddleware()
    return AgentBundle(agent=_Agent(), api_key_env="GOVEE_API_KEY"), watcher


async def test_run_returns_structured_result(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """跑完后返回最终文本、报告路径与用量四类合计。"""
    monkeypatch.setattr(session_module, "build_ui_executor", _fake_build)

    result = await run_ui_task(
        "只回复 OK",
        system_prompt="你是执行者。",
        provider="govee",
        api_key_env="GOVEE_API_KEY",
        model_name="deepseek-flash",
        report_root=tmp_path,
    )

    assert isinstance(result, UiRunResult)
    assert result.final_text == "OK"
    assert result.tokens == {"input": 100, "output": 10, "cache_hit": 60, "cache_creation": 0}
    assert result.by_api_key_env == {"GOVEE_API_KEY": 1}
    assert len(result.usages) == 1
    assert result.usages[0]["api_key_env"] == "GOVEE_API_KEY"


async def test_report_and_log_written_under_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """报告与日志都落在传入的根目录下，且同属一个时间戳子目录。"""
    monkeypatch.setattr(session_module, "build_ui_executor", _fake_build)

    result = await run_ui_task(
        "只回复 OK",
        system_prompt="你是执行者。",
        provider="govee",
        api_key_env="GOVEE_API_KEY",
        model_name="deepseek-flash",
        report_root=tmp_path,
    )

    assert result.report_path.exists()
    assert result.log_path.exists()
    assert result.report_path.suffix == ".html"
    assert result.report_path.parent == result.log_path.parent
    assert result.report_path.parent.parent == tmp_path


async def test_run_prints_nothing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys):
    """运行入口不向标准输出写任何内容。"""
    monkeypatch.setattr(session_module, "build_ui_executor", _fake_build)

    await run_ui_task(
        "只回复 OK",
        system_prompt="你是执行者。",
        provider="govee",
        api_key_env="GOVEE_API_KEY",
        model_name="deepseek-flash",
        report_root=tmp_path,
    )

    captured = capsys.readouterr()
    assert captured.out == ""
