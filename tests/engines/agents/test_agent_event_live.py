"""真机跑一轮工作流，把模型事件写入 tests/reports/agent_events_live.csv。

不修改 test_agents_workflow.py。默认不进普通 pytest，避免误连设备和模型。

手动：
    python -m tests.engines.agents.test_agent_event_live

可选环境变量：AGENT_EVENT_YML、AGENT_EVENT_INPUT、AGENT_EVENT_CASE_TITLE。
"""

from __future__ import annotations

import os

from pathlib import Path

import pytest

from engines.agents.event_sink import bind_sink, reset_sink
from engines.agents.workflow.ui_auto_workflow import run_workflow
from tests.engines.agents.event_csv import CsvEventStore, assert_event_row, load_event_csv

_ROOT = Path(__file__).resolve().parents[3]
_CSV_PATH = _ROOT / "tests" / "reports" / "agent_events_live.csv"
_DEFAULT_YML = "tests/engines/agents/1.yaml"
_DEFAULT_INPUT = "192.168.35.57:39569"


def capture_live_events() -> list[dict]:
    """绑定 CSV 接收方后跑工作流，结束后读回记录。"""
    yml_path = os.environ.get("AGENT_EVENT_YML") or _DEFAULT_YML
    run_input = os.environ.get("AGENT_EVENT_INPUT") or _DEFAULT_INPUT
    case_title = os.environ.get("AGENT_EVENT_CASE_TITLE") or None
    store = CsvEventStore(_CSV_PATH, case_title=case_title or "测试 Agents 工作流")
    token = bind_sink(store)
    try:
        run_workflow(yml_path, run_input, case_title)
    finally:
        reset_sink(token)
        store.flush()
    return load_event_csv(_CSV_PATH)


def assert_live_rows(rows: list[dict]) -> None:
    """真机结果只核对结构和类型，不锁死正文与 token。"""
    assert rows, f"没有事件写入 {_CSV_PATH}"
    kinds = {row["event_type"] for row in rows}
    assert {"ReplyStartEvent", "ModelCallEndEvent", "ReplyEndEvent"} <= kinds
    for index, row in enumerate(rows, start=1):
        assert_event_row(row)
        assert row["seq"] == index
        assert row["duration_ms"] >= 0
        if row["media_type"].startswith("image/"):
            assert row["image_b64"]


@pytest.mark.e2e
@pytest.mark.slow
def test_live_agent_events_round_trip():
    """连真机与模型时才跑。普通 pytest 会跳过。"""
    if os.environ.get("AGENT_EVENT_LIVE") != "1":
        pytest.skip("设 AGENT_EVENT_LIVE=1 后才连真机与模型")
    assert_live_rows(capture_live_events())


if __name__ == "__main__":
    rows = capture_live_events()
    assert_live_rows(rows)
    print(f"写入 {_CSV_PATH}，{len(rows)} 行")
