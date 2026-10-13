"""对话稿：按次 JSONL、五类块、助手信息栏、工具与上下文拆分。"""

from __future__ import annotations

import json

import pytest

from engines.agents.messaging import dialogue as dialogue_module
from engines.agents.messaging.dialogue import DialogueLog

pytestmark = [pytest.mark.unit]


class ModelCallStartEvent:
    def __init__(self, model_name: str = "", created_at: str = "") -> None:
        self.model_name = model_name
        self.created_at = created_at


class ModelCallEndEvent:
    def __init__(
        self,
        *,
        created_at: str = "",
        input_tokens: int = 0,
        output_tokens: int = 0,
        cache_input_tokens: int = 0,
    ) -> None:
        self.created_at = created_at
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.cache_input_tokens = cache_input_tokens


class ThinkingBlockDeltaEvent:
    def __init__(self, block_id: str, delta: str) -> None:
        self.block_id = block_id
        self.delta = delta


class ThinkingBlockEndEvent:
    def __init__(self, block_id: str) -> None:
        self.block_id = block_id


class TextBlockDeltaEvent:
    def __init__(self, block_id: str, delta: str) -> None:
        self.block_id = block_id
        self.delta = delta


class TextBlockEndEvent:
    def __init__(self, block_id: str, text: str = "") -> None:
        self.block_id = block_id
        self.text = text


class ToolCallStartEvent:
    def __init__(self, tool_call_id: str, tool_call_name: str) -> None:
        self.tool_call_id = tool_call_id
        self.tool_call_name = tool_call_name


class ToolCallDeltaEvent:
    def __init__(self, tool_call_id: str, delta: str) -> None:
        self.tool_call_id = tool_call_id
        self.delta = delta


class ToolCallEndEvent:
    def __init__(self, tool_call_id: str) -> None:
        self.tool_call_id = tool_call_id


class ToolResultTextDeltaEvent:
    def __init__(self, tool_call_id: str, delta: str) -> None:
        self.tool_call_id = tool_call_id
        self.delta = delta


class ToolResultDataDeltaEvent:
    def __init__(self, tool_call_id: str, data: bytes) -> None:
        self.tool_call_id = tool_call_id
        self.data = data


class ToolResultEndEvent:
    def __init__(self, tool_call_id: str, state: str) -> None:
        self.tool_call_id = tool_call_id
        self.state = state


def _rows(log: DialogueLog) -> list[dict]:
    return [json.loads(line) for line in log.path.read_text(encoding="utf-8").splitlines() if line]


def test_path_creates_directory_and_separates_runs(tmp_path, monkeypatch) -> None:
    """目录在第一次写入时创建；两次运行各写各的文件。"""
    monkeypatch.setattr(dialogue_module, "_run_stamp", lambda: "20261012-120000")
    directory = tmp_path / "agent_logs"
    first = DialogueLog(str(directory))
    assert not directory.exists()

    first.write_user(role="sop", content="第一次")

    assert directory.is_dir()
    assert first.path.name == "sop-20261012-120000.jsonl"
    assert first.path.is_file()

    monkeypatch.setattr(dialogue_module, "_run_stamp", lambda: "20261012-120001")
    second = DialogueLog(str(directory))
    second.write_user(role="sop", content="第二次")

    assert first.path != second.path
    assert "第一次" in first.path.read_text(encoding="utf-8")
    assert "第二次" not in first.path.read_text(encoding="utf-8")
    assert "第二次" in second.path.read_text(encoding="utf-8")


def test_path_write_failure_is_swallowed(tmp_path, monkeypatch) -> None:
    """目标不可写时不向外抛出。"""
    log = DialogueLog(str(tmp_path), run_id="sop-fail")

    def _boom(*args, **kwargs):
        raise OSError("read only")

    monkeypatch.setattr("builtins.open", _boom)
    log.write_user(role="sop", content="不会落盘")


def test_blocks_include_kind_timestamp_role_and_assistant_meta(tmp_path) -> None:
    """五类块都带类型、时间戳、角色；助手块带模型、用量、费用与耗时。"""
    log = DialogueLog(str(tmp_path), run_id="sop-blocks")
    log.write_user(role="", content="设备ID", scope="独立运行")
    log.write_assistant(
        role="executor_role",
        content="先看页面",
        model="deepseek-flash",
        tokens={"input": 10, "output": 2, "cache_hit": 3},
        cost=0.00126,
        duration_sec=1.164,
        scope="步骤",
    )
    log.write_tool(
        role="executor_role",
        name="click_ratio",
        tool_input={"nx": 0.1},
        state="success",
        output="ok",
        scope="步骤",
    )
    log.write_context(role="executor_role", content="工具说明", scope="步骤")
    log.write_summary(
        calls=1,
        tokens={"input": 10, "output": 2, "cache_hit": 3},
        cost=0.00126,
        duration_sec=28.391,
    )

    rows = _rows(log)
    assert [row["kind"] for row in rows] == ["用户", "助手", "工具", "上下文", "汇总"]
    for row in rows:
        assert row["role"]
        assert len(row["ts"]) == len("2026-10-12 12:22:55.630")
    assert rows[0]["role"] == "-"
    assistant = rows[1]
    assert assistant["model"] == "deepseek-flash"
    assert assistant["tokens"] == {"input": 10, "output": 2, "cache_hit": 3}
    assert assistant["cost"] == 0.0013
    assert assistant["duration_sec"] == 1.16
    assert rows[2]["name"] == "click_ratio"
    assert rows[2]["input"] == {"nx": 0.1}
    summary = rows[4]
    assert summary["calls"] == 1
    assert summary["cost"] == 0.0013
    assert summary["duration_sec"] == 28.39
    assert summary["role"] == "sop"


def test_assistant_merges_one_call_and_null_duration_without_start(tmp_path) -> None:
    """一次模型调用合成一块助手；没有开始时刻时耗时为 null，无文本也落块。"""
    log = DialogueLog(str(tmp_path), run_id="sop-assistant", model="deepseek-flash")
    log.consume(
        ModelCallStartEvent("deepseek-flash", "2026-10-12T12:22:55.000"),
        role="executor_role",
        scope="步骤",
    )
    log.consume(ThinkingBlockDeltaEvent("t1", "先看页面"), role="executor_role", scope="步骤")
    log.consume(ThinkingBlockEndEvent("t1"), role="executor_role", scope="步骤")
    log.consume(TextBlockDeltaEvent("o1", "开始点击"), role="executor_role", scope="步骤")
    log.consume(TextBlockEndEvent("o1"), role="executor_role", scope="步骤")
    log.consume(
        ModelCallEndEvent(
            created_at="2026-10-12T12:22:56.160",
            input_tokens=7087,
            output_tokens=124,
            cache_input_tokens=5760,
        ),
        role="executor_role",
        scope="步骤",
        cost=0.00126,
    )
    log.consume(
        ModelCallEndEvent(input_tokens=3, output_tokens=1, cache_input_tokens=0),
        role="verifier_role",
        scope="步骤",
    )

    rows = _rows(log)
    assert len(rows) == 2
    first, second = rows
    assert first["kind"] == "助手"
    assert first["content"] == "先看页面\n开始点击"
    assert first["model"] == "deepseek-flash"
    assert first["role"] == "executor_role"
    assert first["tokens"] == {"input": 7087, "output": 124, "cache_hit": 5760}
    assert first["cost"] == 0.0013
    assert first["duration_sec"] == 1.16
    assert second["content"] == ""
    assert second["role"] == "verifier_role"
    assert second["duration_sec"] is None
    assert second["cost"] == 0.0


def test_tool_pairs_result_splits_context_and_drops_binary(tmp_path) -> None:
    """入参与返回合成一块，说明拆成上下文，图片二进制不入文件，未返回的调用状态为 -。"""
    log = DialogueLog(str(tmp_path), run_id="sop-tool")
    output = (
        "clicked true\n"
        "<tool-instructions>\ngesture rules\n</tool-instructions>\n"
        "<system-reminder>\nextra\n</system-reminder>"
    )
    log.consume(ToolCallStartEvent("c1", "click_ratio"), role="executor_role", scope="步骤")
    log.consume(
        ToolCallDeltaEvent("c1", '{"serial": "R5", "nx": 0.9}'),
        role="executor_role",
        scope="步骤",
    )
    log.consume(ToolCallEndEvent("c1"), role="executor_role", scope="步骤")
    log.consume(
        ToolResultDataDeltaEvent("c1", b"BINARYSECRET"),
        role="executor_role",
        scope="步骤",
    )
    log.consume(ToolResultTextDeltaEvent("c1", output), role="executor_role", scope="步骤")
    log.consume(ToolResultEndEvent("c1", "success"), role="executor_role", scope="步骤")
    log.consume(ToolCallStartEvent("c2", "screenshot_page"), role="verifier_role", scope="步骤")
    log.consume(ToolCallDeltaEvent("c2", "{}"), role="verifier_role", scope="步骤")
    log.consume(ToolCallEndEvent("c2"), role="verifier_role", scope="步骤")
    log.finish()

    text = log.path.read_text(encoding="utf-8")
    assert "BINARYSECRET" not in text
    rows = _rows(log)
    assert [row["kind"] for row in rows] == ["工具", "上下文", "上下文", "工具"]
    tool = rows[0]
    assert tool["name"] == "click_ratio"
    assert tool["input"] == {"serial": "R5", "nx": 0.9}
    assert tool["state"] == "success"
    assert tool["output"] == "clicked true"
    assert "<tool-instructions>" not in tool["output"]
    assert rows[1]["content"] == "gesture rules"
    assert rows[1]["role"] == "executor_role"
    assert rows[2]["content"] == "extra"
    assert rows[3]["name"] == "screenshot_page"
    assert rows[3]["state"] == "-"
    assert rows[3]["role"] == "verifier_role"
