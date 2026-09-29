"""灰盒·单元测试 — 工作流的日志证据接线（device-log-evidence / ai-engine-protocol）。

用桩提供者与桩角色断言三件事：
1. 调用顺序为「开窗 → 执行 → 读窗 → 验收」，证据进入验收输入；
2. 证据写进该步骤的过程记录（log_evidence 字段）；
3. 未注入提供者时任务不被中断，验收输入标注「无日志证据」。
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from engines.ai.agentscope.config import DeviceExecutionConfig
from engines.ai.agentscope.workflow import (
    DeviceExecutionWorkflow,
    ExecutionOutput,
    Plan,
    Step,
    VerificationOutput,
    _first_action_time,
    _render_log_evidence,
)

ACTION_TIME = "2026-09-28 17:01:12.645"

EVIDENCE = {
    "conclusion": "hit",
    "channel": "H6810",
    "action_time": ACTION_TIME,
    "threshold_seconds": 5.0,
    "baseline_seconds": 30.0,
    "window_line_count": 2,
    "hits": [
        {
            "keyword": "switch_on",
            "grade": "strong",
            "count": 1,
            "timestamps": ["2026-09-28 17:01:13.104"],
            "features": [{"id": 0, "module": "设备开关", "feature": "打开设备成功"}],
            "baseline_occurrences": [],
        }
    ],
    "out_of_window": [],
    "lines": [{"timestamp": "2026-09-28 17:01:13.104", "source": "tcp", "text": "[APP] switch_on"}],
}


class _StubProvider:
    """桩提供者：记录调用顺序，返回固定证据。"""

    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def open_window(self, device: str, label: str = "") -> str:
        self.calls.append(("open", device, label))
        return "w1"

    def read_window(
        self,
        device: str,
        window_id: str = "",
        action_times: list[str] | None = None,
        wait_seconds: float = 0.0,
    ) -> dict:
        self.calls.append(("read", window_id, list(action_times or []), wait_seconds))
        return dict(EVIDENCE)


def _executor_result(action_time: str = ACTION_TIME, extra_action: str = "") -> SimpleNamespace:
    rows = [
        {"type": "call", "name": "click_ratio", "input": "{}"},
        {
            "type": "result",
            "name": "click_ratio",
            "state": "success",
            "output": f'{{"package": "com.demo", "action_time": "{action_time}"}}',
        },
    ]
    if extra_action:
        rows.append(
            {
                "type": "result",
                "name": "tap_screen",
                "state": "success",
                "output": f'{{"package": "com.demo", "action_time": "{extra_action}"}}',
            }
        )
    return SimpleNamespace(
        tool_usage=rows, thinking=[], output="{}", screenshot_path="", screenshot=None
    )


def _make_workflow(provider) -> DeviceExecutionWorkflow:
    return DeviceExecutionWorkflow(
        planner=None,
        executor=None,
        verifier=None,
        config=DeviceExecutionConfig(max_loops=1),
        serial="dev-1",
        log_evidence=provider,
    )


def _stub_steps(wf: DeviceExecutionWorkflow, record: list[tuple], verifier_input: dict) -> None:
    async def fake_execute(step, idx, total, retry_hint="", **_kwargs):
        record.append(("execute",))
        return (
            ExecutionOutput(result="PASS", click_timer="2026-09-28 17:01:12.645", screenshot=""),
            None,
            _executor_result(),
        )

    async def fake_verify(step, idx, total, exec_out, screenshot, log_evidence=None, **_kwargs):
        record.append(("verify", log_evidence))
        verifier_input["evidence"] = log_evidence
        return (
            VerificationOutput(
                result="PASS",
                click_timer=ACTION_TIME,
                log_assertion_timer="2026-09-28 17:01:14.000",
                screenshot="verify.jpg",
                actual="页面已切换到目标页",
            ),
            None,
            SimpleNamespace(screenshot_path="verify.jpg", tool_usage=[], thinking=[], output="{}"),
        )

    wf._execute_step = fake_execute  # type: ignore[method-assign]
    wf._verify_step = fake_verify  # type: ignore[method-assign]


@pytest.mark.asyncio
async def test_step_opens_window_before_action_and_reads_after() -> None:
    """调用顺序：开窗 → 执行 → 读窗 → 验收；证据进入验收输入与步骤记录。"""
    provider = _StubProvider()
    wf = _make_workflow(provider)
    record: list[tuple] = []
    verifier_input: dict = {}
    _stub_steps(wf, record, verifier_input)

    step = Step(action="点击打开设备", **{"assert": "设备已打开"})
    plan = Plan(goal="打开设备", steps=[step])
    log: list[dict] = []
    verdict = await wf._run_step(step, 1, 1, plan, log, [])

    assert verdict is not None and verdict.result == "PASS"
    assert [item[0] for item in provider.calls] == ["open", "read"]
    assert record[0][0] == "execute"
    assert verifier_input["evidence"]["conclusion"] == "hit"
    assert log[0]["log_evidence"]["hits"][0]["keyword"] == "switch_on"
    # 读窗基准就是执行侧回传的动作发出时刻
    assert provider.calls[1][2] == [ACTION_TIME]


@pytest.mark.asyncio
async def test_missing_provider_degrades_without_breaking_task() -> None:
    """未注入提供者：任务照常完成，验收输入明确标注「无日志证据」。"""
    wf = _make_workflow(None)
    record: list[tuple] = []
    verifier_input: dict = {}
    _stub_steps(wf, record, verifier_input)

    step = Step(action="点击打开设备", **{"assert": "设备已打开"})
    plan = Plan(goal="打开设备", steps=[step])
    log: list[dict] = []
    verdict = await wf._run_step(step, 1, 1, plan, log, [])

    assert verdict is not None and verdict.result == "PASS"
    assert verifier_input["evidence"] is None
    assert "log_evidence" not in log[0]
    assert "无（本次未采集到设备日志证据" in _render_log_evidence(None)


def test_action_time_takes_earliest_side_effect() -> None:
    """一步内多次动作 → 基准取最早那个动作发出时刻。"""
    role = _executor_result(
        action_time="2026-09-28 17:01:15.000", extra_action="2026-09-28 17:01:12.645"
    )
    assert _first_action_time(role) == "2026-09-28 17:01:12.645"


def test_action_time_absent_for_read_only_calls() -> None:
    """只有读取类动作（结果里没有 action_time）→ 基准为空。"""
    role = SimpleNamespace(
        tool_usage=[{"type": "result", "name": "current_app", "output": '{"package": "com.demo"}'}],
        thinking=[],
    )
    assert _first_action_time(role) == ""


def test_action_time_skips_previous_step_results() -> None:
    """上下文累积时，基准只取本步新增的工具返回（真机踩到的缺陷回归）。"""
    previous_step = {
        "type": "result",
        "name": "click_ratio",
        "output": '{"package": "com.demo", "action_time": "2026-09-28 17:01:12.645"}',
    }
    current_step = {
        "type": "result",
        "name": "click_ratio",
        "output": '{"package": "com.demo", "action_time": "2026-09-28 17:01:15.000"}',
    }
    role = SimpleNamespace(tool_usage=[previous_step, current_step], thinking=[])
    # 跳过上一步遗留的 1 条 → 只认本步的 17:01:15.000
    assert _first_action_time(role, skip_results=1) == "2026-09-28 17:01:15.000"
    # 不跳过时会把上一步的当基准（旧行为，正是真机暴露的缺陷）
    assert _first_action_time(role, skip_results=0) == "2026-09-28 17:01:12.645"


def test_action_time_empty_when_no_new_results() -> None:
    """本步没有新增工具返回（被跳过光了）→ 基准为空，交给读窗退回窗口起点。"""
    role = _executor_result(action_time="2026-09-28 17:01:12.645")
    assert _first_action_time(role, skip_results=5) == ""


def test_rendered_evidence_carries_grades_and_strict_rule() -> None:
    """渲染出的证据文本含来源 SKU、等级、功能点与从严采信口径。"""
    text = _render_log_evidence(EVIDENCE)
    assert "来源 H6810" in text
    assert "强证据" in text
    assert "#0 设备开关-打开设备成功" in text
    assert "疑似周期证据不得单独作为通过依据" in text


def test_rendered_periodic_evidence_shows_baseline() -> None:
    """疑似周期证据渲染时带上动作前的同名日志，供模型比较。"""
    evidence = dict(EVIDENCE)
    evidence["hits"] = [
        {
            "keyword": "switch_on",
            "grade": "periodic",
            "count": 1,
            "timestamps": ["2026-09-28 17:01:13.104"],
            "features": [{"id": 0, "module": "设备开关", "feature": "打开设备成功"}],
            "baseline_occurrences": [
                {"timestamp": "2026-09-28 17:01:11.645", "text": "[APP] switch_on"}
            ],
        }
    ]
    text = _render_log_evidence(evidence)
    assert "疑似周期" in text
    assert "2026-09-28 17:01:11.645" in text


@pytest.mark.asyncio
async def test_marked_step_records_executor_log_check_with_log() -> None:
    """标记为需日志核对的步骤：执行侧点击证据带时间点，并附同一份 5 秒窗口证据。"""
    provider = _StubProvider()
    wf = _make_workflow(provider)
    record: list[tuple] = []
    verifier_input: dict = {}
    _stub_steps(wf, record, verifier_input)

    step = Step(action="点击开关", assertion="设备上报 switch_on", log_check=True)
    plan = Plan(goal="开关", steps=[step])
    log: list[dict] = []
    await wf._run_step(step, 1, 1, plan, log, [])

    block = log[0]["executor_log_check"]
    assert block["clicks"][0]["action_time"] == ACTION_TIME
    # 与验收侧证据同源：同一份 dict
    assert block["log"] == log[0]["log_evidence"]


@pytest.mark.asyncio
async def test_unmarked_step_records_clicks_without_log() -> None:
    """未标记的步骤：只有时间点与截图路径，不带日志内容。"""
    provider = _StubProvider()
    wf = _make_workflow(provider)
    record: list[tuple] = []
    verifier_input: dict = {}
    _stub_steps(wf, record, verifier_input)

    step = Step(action="进入详情页", **{"assert": "标题显示 H6810"})
    plan = Plan(goal="进入详情页", steps=[step])
    log: list[dict] = []
    await wf._run_step(step, 1, 1, plan, log, [])

    block = log[0]["executor_log_check"]
    assert block["clicks"][0]["action_time"] == ACTION_TIME
    assert block["log"] is None
    # 验收侧证据照旧存在（两块并存）
    assert log[0]["log_evidence"]["hits"][0]["keyword"] == "switch_on"
