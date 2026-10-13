"""灰盒·单元测试 — 验收模型输出契约（spec: ai-verifier-output）。

零外部依赖：只断言契约与判定口径 ——
1. 输出恰好六个字段，且 `logAssertionTimer` / `logAssertionInfo` 按契约别名下发；
2. 无效输出（缺 result / 布尔 result / 非 JSON 对象）不成契约（由调用方走 FAIL 兜底）；
3. 取不到的坐标默认空串，不编造；
4. 平台按日志检查工具的实际调用回填关键词（并只在模型留空时补时间戳）；
5. 编排走 AgentScope 官方 SOP：`result == "PASS"` 判通过；被驳回时把 `actual` 作为说明
   回灌给执行模型重试，用尽驳回次数则该步与整轮失败，并把原因写进失败步骤记录。
"""

from __future__ import annotations

import json

from types import SimpleNamespace

import pytest

from engines.ai.agents.config import DeviceExecutionConfig
from engines.ai.messaging import RoleResult
from engines.ai.workflow.workflow import (
    DeviceExecutionWorkflow,
    VerificationOutput,
    _coerce,
    _fill_log_assertion,
)

CONTRACT = {
    "result": "PASS",
    "click_timer": "2026-09-28 17:01:12.645",
    "logAssertionTimer": "2026-09-28 17:01:13.100",
    "logAssertionInfo": "switch_on",
    "screenshot": "ai_tasks/9/s1_l1.jpg",
    "actual": "截图显示设备已打开",
}


# ── 契约本身 ──


def test_contract_has_exactly_six_fields_with_alias() -> None:
    out = _coerce(VerificationOutput, CONTRACT)
    assert out is not None
    assert out.model_dump(by_alias=True) == CONTRACT


def test_placeholder_keys_absent() -> None:
    out = _coerce(VerificationOutput, CONTRACT)
    assert out is not None
    dumped = out.model_dump(by_alias=True)
    assert "action" not in dumped
    assert "assert" not in dumped


def test_missing_coordinates_default_to_empty() -> None:
    out = _coerce(VerificationOutput, {"result": "FAIL", "actual": "页面未跳转"})
    assert out is not None
    assert out.click_timer == ""
    assert out.log_assertion_timer == ""
    assert out.screenshot == ""
    assert out.actual == "页面未跳转"


@pytest.mark.parametrize(
    "raw",
    [
        {"click_timer": "t"},  # 缺 result
        {"result": True},  # 旧布尔契约不再成立
        {"result": "OK"},  # 非 PASS/FAIL
        "PASS",  # 非 JSON 对象
    ],
)
def test_invalid_output_is_rejected(raw) -> None:
    assert _coerce(VerificationOutput, raw) is None


# ── 平台按工具调用回填日志字段 ──


def _check_call(keyword: str) -> dict:
    return {"type": "call", "name": "check_device_log", "input": {"keyword": keyword}}


def _check_result(detected: bool, stamps: list[str]) -> dict:
    return {
        "type": "result",
        "name": "check_device_log",
        "output": json.dumps({"detected": detected, "timestamps": stamps}, ensure_ascii=False),
    }


def _role(rows: list[dict]) -> SimpleNamespace:
    return SimpleNamespace(tool_usage=rows, thinking=[], output="{}", screenshot_path="")


def test_log_assertion_info_filled_from_tool_calls() -> None:
    verdict = VerificationOutput(result="PASS", log_assertion_info="模型乱写的")
    filled = _fill_log_assertion(
        verdict,
        _role([_check_call("switch_on"), _check_call("switch_off"), _check_call("switch_on")]),
    )
    assert filled.log_assertion_info == "switch_on、switch_off"


def test_log_assertion_timer_filled_only_when_model_left_empty() -> None:
    rows = [_check_call("switch_on"), _check_result(True, ["2026-09-29 11:47:04.687"])]

    blank = _fill_log_assertion(VerificationOutput(result="PASS"), _role(rows))
    assert blank.log_assertion_timer == "2026-09-29 11:47:04.687"

    written = _fill_log_assertion(
        VerificationOutput(result="PASS", log_assertion_timer="模型抄的"), _role(rows)
    )
    assert written.log_assertion_timer == "模型抄的"


def test_log_assertion_untouched_without_tool_call() -> None:
    filled = _fill_log_assertion(
        VerificationOutput(result="PASS", log_assertion_info="x"), _role([])
    )
    assert filled.log_assertion_info == "x"
    assert filled.log_assertion_timer == ""


def test_not_detected_leaves_timer_empty() -> None:
    rows = [_check_call("switch_on"), _check_result(False, [])]
    filled = _fill_log_assertion(VerificationOutput(result="FAIL"), _role(rows))
    assert filled.log_assertion_info == "switch_on"
    assert filled.log_assertion_timer == ""


# ── 判定与回灌（编排走官方 SOP）──


def _role_result(output: str, role: str) -> RoleResult:
    return RoleResult(
        role=role,
        model_name="stub",
        output=output,
        input_text="",
        thinking=[],
        tool_usage=[],
        context=[],
        screenshot=None,
        screenshot_path="",
        usage={"input_tokens": 1, "output_tokens": 1, "cache_input_tokens": 0},
        cost=0.0,
    )


class _StubPlanner:
    """桩规划角色：直接给出计划，不碰模型。"""

    model_name = "stub-planner"

    def __init__(self, steps: list[dict]):
        self._steps = steps

    def reset_context(self) -> None:
        pass

    async def run(self, goal: str) -> RoleResult:
        return _role_result(json.dumps({"plan": {"steps": self._steps}}), "planner")


class _StubExecutor:
    """桩执行角色：按顺序回放给定的执行结果，记录每次拿到的重试提示。"""

    model_name = "stub-executor"

    def __init__(self, outputs: list[dict]):
        self._outputs = outputs
        self.hints: list[str] = []

    def reset_context(self) -> None:
        pass

    async def run(self, serial, action, idx, total, retry_hint="") -> RoleResult:
        self.hints.append(retry_hint)
        out = self._outputs[min(len(self.hints) - 1, len(self._outputs) - 1)]
        return _role_result(json.dumps(out), "executor")


class _StubVerifier:
    """桩验收角色：按顺序回放给定的验收结论。"""

    model_name = "stub-verifier"

    def __init__(self, verdicts: list[dict]):
        self._verdicts = verdicts
        self.seen: list[tuple] = []

    def reset_context(self) -> None:
        pass

    async def run(
        self,
        serial,
        assertion,
        idx,
        total,
        exec_result,
        exec_evidence,
        screenshot,
        log_evidence="",
        keyword_catalog="",
    ) -> RoleResult:
        self.seen.append((assertion, exec_result, exec_evidence))
        out = self._verdicts[min(len(self.seen) - 1, len(self._verdicts) - 1)]
        return _role_result(json.dumps(out), "verifier")


def _workflow(
    steps: list[dict],
    execs: list[dict],
    verdicts: list[dict],
    max_loops: int = 2,
) -> DeviceExecutionWorkflow:
    return DeviceExecutionWorkflow(
        planner=_StubPlanner(steps),
        executor=_StubExecutor(execs),
        verifier=_StubVerifier(verdicts),
        config=DeviceExecutionConfig(max_loops=max_loops),
        serial="dev-1",
    )


@pytest.mark.asyncio
async def test_fail_verdict_feeds_actual_back_as_retry_hint() -> None:
    wf = _workflow(
        [{"action": "点击开关", "assert": "灯亮"}],
        [{"result": "FAIL", "click_timer": "t1", "screenshot": ""}],
        [{"result": "FAIL", "actual": "灯没亮"}],
    )

    result = await wf.run("开灯")

    assert wf.executor.hints == ["", "灯没亮"]  # 第二次执行拿到失败原因
    assert result["status"] == "fail"
    assert result["log"][0]["verifier"]["result"] == "FAIL"
    assert result["log"][0]["verifier"]["actual"] == "灯没亮"


@pytest.mark.asyncio
async def test_pass_verdict_passes_without_retry() -> None:
    wf = _workflow(
        [{"action": "点击开关", "assert": "灯亮"}],
        [{"result": "PASS", "click_timer": "t1", "screenshot": ""}],
        [{"result": "PASS", "actual": "灯已亮"}],
        max_loops=3,
    )

    result = await wf.run("开灯")

    assert result["status"] == "success"
    assert wf.executor.hints == [""]  # 一次即过，不再重试
    assert result["completed"] == ["点击开关"]


@pytest.mark.asyncio
async def test_failed_step_record_keeps_actual_as_reason() -> None:
    wf = _workflow(
        [{"action": "点击开关", "assert": "灯亮"}],
        [{"result": "FAIL", "click_timer": "t1", "screenshot": ""}],
        [{"result": "FAIL", "actual": "灯没亮"}],
        max_loops=1,
    )

    result = await wf.run("开灯")

    assert result["status"] == "fail"
    assert result["failed"][0]["actual"] == "灯没亮"
    assert result["failed"][0]["action"] == "点击开关"
    assert result["failed"][0]["assert"] == "灯亮"
