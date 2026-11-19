"""ae_harness 记录器：一次模型调用一条记录、时间锚点、标签落盘。

只测 `event/record.py` 的采集行为（用替身事件，不连模型、不联网）。
不测报告 HTML 渲染。
"""

from __future__ import annotations

import json

from dataclasses import dataclass
from pathlib import Path

import pytest

from engines.ae_harness.event.record import AgentEventRecorder, RunRecord
from engines.ae_harness.event.usage import TokenUsage, summarize

pytestmark = [pytest.mark.unit]

LABEL = "OPENAI_API_KEY"


@dataclass
class ModelCallStartEvent:
    """替身：模型调用开始。"""

    reply_id: str = "r1"
    model_name: str = "deepseek-flash"


@dataclass
class ModelCallEndEvent:
    """替身：模型调用结束，带上四类 token。"""

    input_tokens: int
    output_tokens: int
    cache_input_tokens: int = 0
    cache_creation_input_tokens: int = 0
    finished_reason: str = "completed"
    reply_id: str = "r1"


@dataclass
class ReplyStartEvent:
    """替身：一条回复开始，带 reply_id 与 agent 名。"""

    reply_id: str
    name: str = "ui_executor"


@dataclass
class CustomEvent:
    """替身：自定义事件，SOP 用它标记步骤起点。"""

    name: str
    value: dict


def _recorder(tmp_path: Path, *, api_key_env: str = LABEL) -> AgentEventRecorder:
    """建一个指向临时目录的记录器。"""
    return AgentEventRecorder(tmp_path, "probe", api_key_env=api_key_env)


def _run_two_calls(recorder: AgentEventRecorder) -> RunRecord:
    """喂两次模型调用（不合并），返回整轮记录。"""
    recorder.begin("probe task")
    recorder.on_event(ModelCallStartEvent())
    recorder.on_event(ModelCallEndEvent(10, 1))
    recorder.on_event(ModelCallStartEvent())
    recorder.on_event(ModelCallEndEvent(20, 2, cache_input_tokens=5))
    return recorder.finish(1.5)


def test_two_calls_produce_two_records(tmp_path: Path):
    """同一轮的两次调用各自成条，不合并。"""
    record = _run_two_calls(_recorder(tmp_path))
    assert [item.round_index for item in record.usages] == [1, 2]
    assert [item.input_tokens for item in record.usages] == [10, 20]
    assert len(record.usages) == 2


def test_usage_carries_label_and_tokens(tmp_path: Path):
    """每条用量记录都带密钥名与四类 token。"""
    record = _run_two_calls(_recorder(tmp_path))
    first = record.usages[0]
    assert isinstance(first, TokenUsage)
    assert first.api_key_env == LABEL
    assert first.output_tokens == 1
    assert first.cache_input_tokens == 0
    assert record.usages[1].cache_input_tokens == 5


def test_absolute_time_recoverable_with_anchor(tmp_path: Path):
    """有起始墙钟时，绝对时刻可解析。"""
    from datetime import datetime

    record = _run_two_calls(_recorder(tmp_path))
    started = record.usages[0].started_at
    assert started
    moment = datetime.strptime(started, "%Y-%m-%d_%H-%M-%S.%f")
    assert moment.year >= 2024
    assert record.usages[0].ended_at


def test_missing_label_degrades_to_empty_string(tmp_path: Path):
    """未传标签时标签为空串，其余照常产出。"""
    record = _run_two_calls(_recorder(tmp_path, api_key_env=""))
    assert len(record.usages) == 2
    assert record.usages[0].api_key_env == ""
    assert record.usages[0].input_tokens == 10


def test_no_anchor_does_not_fake_absolute_time(tmp_path: Path):
    """没调用 begin（无起始墙钟）时绝对时刻留空，不伪造。"""
    recorder = _recorder(tmp_path)
    recorder.on_event(ModelCallEndEvent(7, 3))
    record = recorder.finish(0.1)
    assert len(record.usages) == 1
    assert record.usages[0].started_at == ""
    assert record.usages[0].ended_at == ""
    assert record.usages[0].input_tokens == 7


def test_summary_line_carries_label(tmp_path: Path):
    """汇总行落盘带密钥名，事后审计不必读内存对象。"""
    record = _run_two_calls(_recorder(tmp_path))
    lines = Path(record.log_path).read_text(encoding="utf-8").strip().splitlines()
    summary = json.loads(lines[-1])
    assert summary["event"] == "summary"
    assert summary["api_key_env"] == LABEL
    assert summary["tokens"] == {"input": 30, "output": 3, "cache_hit": 5, "cache_creation": 0}


@dataclass
class ReplyStartEvent:
    """替身：一条回复开始，带 reply_id 与 agent 名。"""

    reply_id: str
    name: str = "ui_executor"


@dataclass
class CustomEvent:
    """替身：自定义事件，SOP 用它标记步骤起点。"""

    name: str
    value: dict


def test_label_follows_agent_name(tmp_path: Path):
    """密钥绑在角色上：两个角色各绑一把，标签按 agent 名反查，不整轮共用一个。"""
    recorder = AgentEventRecorder(
        tmp_path,
        "probe",
        api_key_env="OPENAI_API_KEY",
        role_api_keys={"ui_executor": "OPENAI_API_KEY", "ui_verifier": "DEEPSEEK_API_KEY"},
    )
    recorder.begin("mixed task")
    recorder.on_event(CustomEvent("SOP_STEP_STARTED", {"step": "1"}))
    recorder.on_event(ReplyStartEvent("r1", "ui_executor"))
    recorder.on_event(ModelCallStartEvent("r1"))
    recorder.on_event(ModelCallEndEvent(10, 1, reply_id="r1"))
    recorder.on_event(ReplyStartEvent("r2", "ui_verifier"))
    recorder.on_event(ModelCallStartEvent("r2"))
    recorder.on_event(ModelCallEndEvent(20, 2, reply_id="r2"))
    record = recorder.finish(1.0)

    assert [item.api_key_env for item in record.usages] == ["OPENAI_API_KEY", "DEEPSEEK_API_KEY"]
    summary = summarize(record.usages)
    assert summary.by_api_key_env == {"OPENAI_API_KEY": 1, "DEEPSEEK_API_KEY": 1}
    assert summary.input_tokens == 30


def test_unregistered_role_falls_back(tmp_path: Path):
    """角色没登记绑定时回落到兜底标签，记录照常产出。"""
    recorder = AgentEventRecorder(
        tmp_path,
        "probe",
        api_key_env="FALLBACK_KEY",
        role_api_keys={"ui_executor": "OPENAI_API_KEY"},
    )
    recorder.begin("fallback")
    recorder.on_event(ReplyStartEvent("r9", "someone_else"))
    recorder.on_event(ModelCallEndEvent(5, 1, reply_id="r9"))
    record = recorder.finish(0.1)
    assert record.usages[0].api_key_env == "FALLBACK_KEY"


def test_label_persisted_on_model_call_rows(tmp_path: Path):
    """逐次调用的密钥名落进事件行，只读 JSONL 也能按密钥复算。"""
    recorder = AgentEventRecorder(
        tmp_path,
        "probe",
        role_api_keys={"ui_executor": "OPENAI_API_KEY", "ui_verifier": "DEEPSEEK_API_KEY"},
    )
    recorder.begin("mixed")
    recorder.on_event(CustomEvent("SOP_STEP_STARTED", {"step": "1"}))
    recorder.on_event(ReplyStartEvent("r1", "ui_executor"))
    recorder.on_event(ModelCallEndEvent(10, 1, reply_id="r1"))
    recorder.on_event(ReplyStartEvent("r2", "ui_verifier"))
    recorder.on_event(ModelCallEndEvent(20, 2, reply_id="r2"))
    record = recorder.finish(1.0)

    rows = [
        json.loads(line) for line in Path(record.log_path).read_text(encoding="utf-8").splitlines()
    ]
    ends = [row for row in rows if row["event"] == "ModelCallEndEvent"]
    assert [row["api_key_env"] for row in ends] == ["OPENAI_API_KEY", "DEEPSEEK_API_KEY"]
    assert rows[-1]["by_api_key_env"] == {"OPENAI_API_KEY": 1, "DEEPSEEK_API_KEY": 1}


def test_run_record_carries_label(tmp_path: Path):
    """整轮记录上也能直接读密钥名。"""
    record = _run_two_calls(_recorder(tmp_path))
    assert record.api_key_env == LABEL


async def test_observations_written_as_own_rows(tmp_path: Path):
    """观测记录落成独立行，类型字段与事件行不同，并可从记录对象读取。"""
    from engines.ae_harness.middleware import ObservationMiddleware

    observer = ObservationMiddleware()
    recorder = AgentEventRecorder(tmp_path, "probe", observations=observer.records)
    recorder.begin("observe")
    await observer.on_system_prompt(None, "你是执行者。")
    recorder.on_event(ModelCallEndEvent(1, 1))
    record = recorder.finish(0.1)

    rows = [
        json.loads(line) for line in Path(record.log_path).read_text(encoding="utf-8").splitlines()
    ]
    kinds = [row["event"] for row in rows]
    assert "observation" in kinds
    assert record.observations[0]["kind"] == "system_prompt"
    assert record.observations[0]["text"] == "你是执行者。"


def test_no_observations_keeps_row_kinds(tmp_path: Path):
    """不挂观测中间件时，产物里不出现观测行。"""
    record = _run_two_calls(_recorder(tmp_path))
    rows = [
        json.loads(line) for line in Path(record.log_path).read_text(encoding="utf-8").splitlines()
    ]
    assert "observation" not in {row["event"] for row in rows}
    assert record.observations == []
