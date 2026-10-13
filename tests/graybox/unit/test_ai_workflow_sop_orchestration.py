"""灰盒·单元测试 — SOP 编排（变更 2026-10-09-sop-executor-verifier）。

零网络、零设备：用桩角色（planner / executor / verifier）驱动真实的
`SOPEngine` + `ExecutionSOPStep`，断言六件事：

1. 全部步骤通过 → success，过程记录逐轮追加；
2. 某步被驳回一次后通过 → 驳回原因回灌给执行者，过程记录两轮；
3. 驳回用尽 → 该步与整轮失败，后续步骤不再执行；
4. 运行状态可序列化与重建，已完成的步骤被跳过；
5. 步骤数与保存的状态不匹配时报错（不静默错位继续）；
6. 进度载荷形状与改造前一致（运行中检查点、终态同构）。
"""

from __future__ import annotations

import json

from types import SimpleNamespace

import pytest

from agentscope.message import TextBlock
from agentscope.sop import SOP, SOPEngine, SOPPhase, SOPRunState

from engines.ai.agents.config import DeviceExecutionConfig
from engines.ai.messaging import RoleResult
from engines.ai.workflow.sop_step import (
    ExecutionSOPStep,
    ExecutionStepState,
    ExecutorAdapter,
    StepAttemptSink,
    VerifierAdapter,
    handover_text,
    retry_hint_from,
    verdict_payload,
)
from engines.ai.workflow.workflow import (
    DeviceExecutionWorkflow,
    ExecutionOutput,
    VerificationOutput,
)

# ── 桩角色 ──


def _result(output: str, role: str) -> RoleResult:
    """桩角色返回：只填编排会用到的字段。"""
    return RoleResult(
        role=role,
        model_name=f"stub-{role}",
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


class StubPlanner:
    model_name = "stub-planner"

    def __init__(self, steps: list[dict]):
        self._steps = steps
        self.reset_calls = 0

    def reset_context(self) -> None:
        self.reset_calls += 1

    async def run(self, goal: str) -> RoleResult:
        return _result(json.dumps({"plan": {"steps": self._steps}}), "planner")


class StubExecutor:
    """桩执行角色：按调用次序回放执行结果，记录每次拿到的重试提示。"""

    model_name = "stub-executor"

    def __init__(self, outputs: list[dict]):
        self._outputs = outputs
        self.calls: list[dict] = []
        self.reset_calls = 0

    def reset_context(self) -> None:
        self.reset_calls += 1

    async def run(self, serial, action, idx, total, retry_hint="") -> RoleResult:
        self.calls.append({"action": action, "idx": idx, "retry_hint": retry_hint})
        out = self._outputs[min(len(self.calls) - 1, len(self._outputs) - 1)]
        return _result(json.dumps(out), "executor")


class StubVerifier:
    """桩验收角色：按调用次序回放验收结论，记录拿到的验收输入口径。"""

    model_name = "stub-verifier"

    def __init__(self, verdicts: list[dict]):
        self._verdicts = verdicts
        self.seen: list[dict] = []
        self.reset_calls = 0

    def reset_context(self) -> None:
        self.reset_calls += 1

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
        self.seen.append(
            {
                "assertion": assertion,
                "idx": idx,
                "total": total,
                "exec_result": exec_result,
                "exec_evidence": exec_evidence,
                "keyword_catalog": keyword_catalog,
            }
        )
        out = self._verdicts[min(len(self.seen) - 1, len(self._verdicts) - 1)]
        return _result(json.dumps(out), "verifier")


def _workflow(
    steps: list[dict],
    execs: list[dict],
    verdicts: list[dict],
    *,
    max_loops: int = 2,
    on_progress=None,
    run_state=None,
) -> DeviceExecutionWorkflow:
    return DeviceExecutionWorkflow(
        planner=StubPlanner(steps),
        executor=StubExecutor(execs),
        verifier=StubVerifier(verdicts),
        config=DeviceExecutionConfig(max_loops=max_loops),
        serial="dev-1",
        on_progress=on_progress,
        run_state=run_state,
    )


def _pass(click="t1", shot=""):
    return {"result": "PASS", "click_timer": click, "screenshot": shot}


def _fail(click="t1", shot=""):
    return {"result": "FAIL", "click_timer": click, "screenshot": shot}


# ── 1. 全部通过 ──


@pytest.mark.unit
async def test_all_steps_pass_marks_run_success() -> None:
    wf = _workflow(
        [{"action": "打开开关", "assert": "灯亮"}, {"action": "调亮度", "assert": "亮度 50%"}],
        [_pass(), _pass("t2")],
        [{"result": "PASS", "actual": "已达成"}],
    )

    result = await wf.run("开灯并调亮度")

    assert result["status"] == "success"
    assert result["completed"] == ["打开开关", "调亮度"]
    assert [row["loop"] for row in result["log"]] == [1, 1]
    assert [row["executor"]["click_timer"] for row in result["log"]] == ["t1", "t2"]
    assert result["max_loops"] == 2
    assert [call["idx"] for call in wf.executor.calls] == [1, 2]
    assert wf.run_state.phase is SOPPhase.COMPLETED


# ── 2. 驳回一次后通过 ──


@pytest.mark.unit
async def test_rejected_once_then_pass_feeds_reason_back() -> None:
    wf = _workflow(
        [{"action": "打开开关", "assert": "灯亮"}],
        [_fail(), _pass("t2", "s2.jpg")],
        [{"result": "FAIL", "actual": "灯没亮"}, {"result": "PASS", "actual": "灯已亮"}],
    )

    result = await wf.run("开灯")

    assert result["status"] == "success"
    assert [call["retry_hint"] for call in wf.executor.calls] == ["", "灯没亮"]
    assert [row["loop"] for row in result["log"]] == [1, 2]
    assert [row["verifier"]["result"] for row in result["log"]] == ["FAIL", "PASS"]
    assert wf.run_state.steps[0].phase is SOPPhase.COMPLETED
    # 框架把每次尝试都记成一条结论，尝试计数即结论条数
    assert len(wf.run_state.steps[0].verifications) == 2


# ── 3. 驳回用尽 → 整轮失败 ──


@pytest.mark.unit
async def test_attempts_exhausted_fails_step_and_whole_run() -> None:
    wf = _workflow(
        [{"action": "打开开关", "assert": "灯亮"}, {"action": "调亮度", "assert": "亮度 50%"}],
        [_fail()],
        [{"result": "FAIL", "actual": "灯没亮"}],
        max_loops=2,
    )

    result = await wf.run("开灯")

    assert result["status"] == "fail"
    assert result["reason"] == "步骤未通过：打开开关"
    assert result["completed"] == []
    assert result["failed"] == [{"action": "打开开关", "assert": "灯亮", "actual": "灯没亮"}]
    # 用尽 max_loops=2 次驳回后不再重试；第二步整轮不执行
    assert len(wf.executor.calls) == 2
    assert [call["action"] for call in wf.executor.calls] == ["打开开关", "打开开关"]
    assert wf.run_state.steps[0].phase is SOPPhase.FAILED
    assert wf.run_state.steps[1].phase is SOPPhase.PENDING


# ── 4. 状态保存 → 重建 → 跳过已完成 ──


@pytest.mark.unit
async def test_run_state_round_trip_skips_completed_steps() -> None:
    steps = [
        {"action": "打开开关", "assert": "灯亮"},
        {"action": "调亮度", "assert": "亮度 50%"},
    ]
    first = _workflow(steps, [_pass()], [{"result": "PASS", "actual": "已达成"}])
    # 只跑第一步：把第一步预先标成已完成（等价于上次运行已通过它）
    first.run_state = SOPRunState(
        steps=[
            ExecutionStepState(phase=SOPPhase.COMPLETED),
            ExecutionStepState(),
        ]
    )
    saved = first.run_state.model_dump_json()

    restored = SOPRunState.model_validate_json(saved)
    assert len(restored.steps) == 2
    assert restored.steps[0].phase is SOPPhase.COMPLETED
    assert restored.phase is SOPPhase.RUNNING

    resumed = _workflow(
        steps,
        [_pass("t2")],
        [{"result": "PASS", "actual": "已达成"}],
        run_state=restored,
    )
    result = await resumed.run("开灯并调亮度")

    assert result["status"] == "success"
    assert result["completed"] == ["打开开关", "调亮度"]
    # 已完成的步骤被跳过：执行者只被调用一次，且是第二步
    assert [call["action"] for call in resumed.executor.calls] == ["调亮度"]
    assert [row["action"] for row in result["log"]] == ["调亮度"]


@pytest.mark.unit
async def test_step_state_keeps_platform_facts_through_engine_rebuild() -> None:
    """重建运行（`SOPEngine` 按 `state_type` 还原）后，平台事实仍在，已完成的步骤被跳过。"""
    state = SOPRunState(
        steps=[
            ExecutionStepState(
                phase=SOPPhase.COMPLETED,
                exec_out={"result": "PASS", "click_timer": "t1", "screenshot": "s.jpg"},
                verdict={"result": "PASS", "actual": "灯已亮"},
                screenshot="ai_tasks/9/s1_l1.jpg",
                log_evidence={"conclusion": "hit"},
                executor_log_check={"clicks": [], "log": None},
            )
        ]
    )
    saved = state.model_dump_json()
    restored = SOPRunState.model_validate_json(saved)
    # 基类读回时额外字段仍在（extra="allow"），逐字段可读
    assert restored.steps[0].exec_out["result"] == "PASS"
    assert restored.steps[0].screenshot == "ai_tasks/9/s1_l1.jpg"

    step = ExecutionSOPStep(
        subject="步骤 1/1",
        description="灯亮",
        executor=_executor_adapter(),
        verifier=_verifier_adapter(),
        context=None,
        max_attempts=1,
    )
    engine = SOPEngine(SOP(name="t", steps=[step]), state=restored)

    # 运行状态按步骤的 state_type 还原：平台事实与阶段都还在，无步骤需要重跑
    record = engine.state.steps[0]
    assert isinstance(record, ExecutionStepState)
    assert record.exec_out == {"result": "PASS", "click_timer": "t1", "screenshot": "s.jpg"}
    assert record.verdict == {"result": "PASS", "actual": "灯已亮"}
    assert record.log_evidence == {"conclusion": "hit"}
    assert engine.phase is SOPPhase.COMPLETED


# ── 5. 步骤数与状态不匹配 → 报错 ──


@pytest.mark.unit
def test_engine_rejects_state_with_different_step_count() -> None:
    step = ExecutionSOPStep(
        subject="步骤 1/2",
        description="断言",
        executor=_executor_adapter(),
        verifier=_verifier_adapter(),
        context=None,
        max_attempts=1,
    )
    state = SOPRunState(steps=[ExecutionStepState(), ExecutionStepState(), ExecutionStepState()])

    with pytest.raises(ValueError) as excinfo:
        SOPEngine(SOP(name="t", steps=[step]), state=state)

    assert "State has 3 steps" in str(excinfo.value)


# ── 6. 适配器契约（交付文本 / 结论映射 / 重试回灌解析）──


@pytest.mark.unit
def test_handover_text_carries_three_field_execution_result() -> None:
    text = handover_text(ExecutionOutput(result="PASS", click_timer="t1", screenshot="s.jpg"))

    assert json.loads(text) == {
        "execution": {"result": "PASS", "click_timer": "t1", "screenshot": "s.jpg"}
    }


@pytest.mark.unit
def test_verdict_payload_maps_pass_fail_to_passed_flag() -> None:
    assert verdict_payload(VerificationOutput(result="PASS", actual="灯已亮")) == {
        "passed": True,
        "message": "灯已亮",
    }
    assert verdict_payload(VerificationOutput(result="FAIL", actual="灯没亮")) == {
        "passed": False,
        "message": "灯没亮",
    }


@pytest.mark.unit
def test_retry_hint_read_from_platform_brief_only() -> None:
    """只认平台自己写的 <feedback> 段；框架自带的英文提醒不算回灌口径。"""
    brief = SimpleNamespace(
        content=[
            TextBlock(
                text="第 2/2 次尝试。<feedback>上次执行未通过验收，请修正后重做：\n灯没亮</feedback>"
            )
        ]
    )
    framework_brief = SimpleNamespace(
        content=[TextBlock(text="<system-reminder>Your last attempt was not accepted: x")]
    )

    assert retry_hint_from([brief]) == "灯没亮"
    assert retry_hint_from([framework_brief]) == ""
    assert retry_hint_from(None) == ""


@pytest.mark.unit
def test_sink_commit_projects_attempt_facts_into_state() -> None:
    sink = StepAttemptSink()
    sink.exec_out = ExecutionOutput(result="PASS", click_timer="t1", screenshot="s.jpg")
    sink.verdict = VerificationOutput(result="PASS", actual="灯已亮")
    sink.screenshot = "ai_tasks/1/s1_l1.jpg"
    sink.log_evidence = {"conclusion": "hit"}
    sink.executor_log_check = {"clicks": [], "log": None}
    state = ExecutionStepState()

    sink.commit(state, 1)

    assert state.exec_out == {"result": "PASS", "click_timer": "t1", "screenshot": "s.jpg"}
    assert state.verdict["result"] == "PASS"
    assert state.screenshot == "ai_tasks/1/s1_l1.jpg"
    assert state.log_evidence == {"conclusion": "hit"}


def _executor_adapter() -> ExecutorAdapter:
    """只用于构步骤的占位执行者适配器（不触发任何调用）。"""
    return ExecutorAdapter(None, StepAttemptSink())


def _verifier_adapter() -> VerifierAdapter:
    """只用于构步骤的占位验证者适配器（不触发任何调用）。"""
    return VerifierAdapter(None, StepAttemptSink())


# ── 7. 进度载荷形状 ──


@pytest.mark.unit
async def test_progress_payload_shape_is_unchanged() -> None:
    seen: list[dict] = []
    wf = _workflow(
        [{"action": "打开开关", "assert": "灯亮"}],
        [_pass()],
        [{"result": "PASS", "actual": "灯已亮"}],
        on_progress=seen.append,
    )

    result = await wf.run("开灯")

    # 与改造前一致：先报「已规划 N 个步骤」，每次尝试后再报一条「步骤 x/y 验收 PASS/FAIL」
    assert [item["summary"] for item in seen] == ["已规划 1 个步骤", "步骤 1/1 验收 PASS"]
    planned, after_attempt = seen
    for payload in seen:
        assert payload["status"] == "running"
        assert set(payload) == set(result)
        assert payload["plans"][0]["steps"][0]["assert"] == "灯亮"
        assert payload["models"]["max_loops"] == 2
        assert payload["max_loops"] == 2
    assert planned["log"] == []
    assert planned["completed"] == []
    assert after_attempt["completed"] == []  # 完成勾选在终态收敛时给出
    assert after_attempt["log"][0]["action"] == "打开开关"
    assert after_attempt["log"][0]["loop"] == 1

    # 终态与进度同构（字段集合一致）
    assert set(result) == set(seen[0])


@pytest.mark.unit
def test_verifier_adapter_consumes_context_not_framework_inputs() -> None:
    """验收输入口径由平台拼（角色自己拼 prompt），适配器不消费框架派发的交付文本。"""
    adapter = VerifierAdapter(None, StepAttemptSink())
    assert hasattr(adapter, "reply_stream")
    assert adapter.name == "verifier"
    assert ExecutorAdapter(None, StepAttemptSink()).name == "executor"
