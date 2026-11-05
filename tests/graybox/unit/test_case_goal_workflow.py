"""目标流水线：产物累积、预检拦截与渲染。"""

from __future__ import annotations

import pytest

from agentscope.message import Msg

from engines.agents.workflow import case_goal_workflow
from engines.agents.workflow.case_artifact import (
    ArtifactStore,
)
from engines.agents.workflow.case_goal_workflow import (
    build_case_run_input,
    run_case_authoring_artifact,
)

pytestmark = [pytest.mark.unit]

REQUIREMENT = "打开 App 后进入设备详情页。点击场景模式后进入场景页。"


@pytest.fixture(autouse=True)
def _dummy_key(monkeypatch):
    """构造角色只需要非空密钥，不会发起模型调用（GoalPipeline 被替换）。"""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")


class _RecordingStore(ArtifactStore):
    """记录最近一次实例，供假流水线写入产物。"""

    last: "_RecordingStore | None" = None

    def __init__(self) -> None:
        super().__init__()
        _RecordingStore.last = self


def _fill(store: ArtifactStore) -> None:
    """写入一份能通过事实预检的最小产物。"""
    store.put_state_machine(
        [
            {
                "id": "S1",
                "name": "详情页",
                "observable": True,
                "observe_by": "截图：顶栏显示型号",
                "source": "打开 App 后进入设备详情页",
            },
            {
                "id": "S2",
                "name": "场景页",
                "observable": True,
                "observe_by": "截图：功能格场景高亮",
                "source": "点击场景模式后进入场景页",
            },
        ],
        [
            {
                "id": "T1",
                "from": "S1",
                "to": "S2",
                "event": "点击场景模式",
                "source": "点击场景模式后进入场景页",
            },
        ],
    )
    store.append_scenarios(
        [
            {
                "id": "SC-001",
                "title": "进入场景页",
                "path": ["S1", "S2"],
                "transitions": ["T1"],
                "type": "主流程",
                "source": "点击场景模式后进入场景页",
            },
        ]
    )
    store.append_cases(
        [
            {
                "id": "TC-001",
                "title": "点击场景模式",
                "scenario_id": "SC-001",
                "pre_state": "S1",
                "steps": [{"action": "点击场景模式", "expect_state": "S2"}],
                "boundary": [],
                "method": ["场景法"],
                "priority": "P1",
                "source": "点击场景模式后进入场景页",
            },
        ]
    )


def _fake_pipeline(monkeypatch, *, fill: bool, verdict: str = "pass", message: str = "通过"):
    """替换 GoalPipeline：按需写产物，并把判决作为最终消息吐出。"""

    class FakePipeline:
        def __init__(self, executor, verifier, **kwargs):
            self.verifier = verifier
            self.kwargs = kwargs

        async def reply_stream(self, inputs):
            if fill and _RecordingStore.last is not None:
                _fill(_RecordingStore.last)
            yield Msg(
                name=self.verifier.name,
                role="assistant",
                content=[],
                structured_output={"result": verdict, "message": message},
            )

    monkeypatch.setattr(case_goal_workflow, "GoalPipeline", FakePipeline)
    monkeypatch.setattr(case_goal_workflow, "ArtifactStore", _RecordingStore)


def test_run_input_carries_project_and_requirement() -> None:
    text = build_case_run_input("需求正文", "H6810", "V2")
    assert "H6810" in text and "V2" in text and "需求正文" in text


def test_run_input_rejects_blank_requirement() -> None:
    with pytest.raises(ValueError, match="需求正文不能为空"):
        build_case_run_input("   ")


@pytest.mark.asyncio
async def test_pipeline_pass_builds_artifact_and_renders(monkeypatch):
    _fake_pipeline(monkeypatch, fill=True)

    result = await run_case_authoring_artifact(REQUIREMENT)

    assert result.phase == "completed"
    assert result.passed is True
    assert result.artifact.counts == {"states": 2, "transitions": 1, "scenarios": 1, "cases": 1}
    assert result.artifact.diagram.startswith("stateDiagram-v2")
    assert "## 三、测试用例" in result.document
    assert result.verdicts[-1][0] is True


@pytest.mark.asyncio
async def test_facts_block_even_when_verifier_passes(monkeypatch):
    _fake_pipeline(monkeypatch, fill=True)
    # 需求里没有「场景页」以外的东西，把需求换掉即可让 source 全部不成立
    result = await run_case_authoring_artifact("完全无关的需求正文")

    assert result.passed is False
    assert result.phase == "failed"
    assert result.verdicts[-1][2] == "case_artifact_facts"
    assert "【确定性问题】" in result.verdicts[-1][1]


@pytest.mark.asyncio
async def test_empty_artifact_cannot_pass(monkeypatch):
    _fake_pipeline(monkeypatch, fill=False)

    result = await run_case_authoring_artifact(REQUIREMENT)

    assert result.passed is False
    assert "没有用例" in result.reason


@pytest.mark.asyncio
async def test_verifier_fail_keeps_message_as_reason(monkeypatch):
    _fake_pipeline(monkeypatch, fill=True, verdict="fail", message="TC-001 的数值与原文不符")

    result = await run_case_authoring_artifact(REQUIREMENT)

    assert result.passed is False
    assert result.reason == "TC-001 的数值与原文不符"


@pytest.mark.asyncio
async def test_fabricated_number_fails_task_and_names_the_case(monkeypatch):
    """故意在用例步骤里塞一个需求没有的数值：整轮判失败，且原因点名该用例。"""

    class FakePipeline:
        def __init__(self, executor, verifier, **kwargs):
            self.verifier = verifier

        async def reply_stream(self, inputs):
            store = _RecordingStore.last
            assert store is not None
            _fill(store)
            bad = store.cases[0]
            step_type = type(bad.steps[0])
            store.cases[0] = type(bad)(
                bad.id,
                bad.title,
                bad.scenario_id,
                bad.pre_state,
                (step_type("3 秒内点击场景模式", bad.steps[0].expect_state, ""),),
                bad.boundary,
                bad.method,
                bad.priority,
                bad.source,
            )
            yield Msg(
                name=self.verifier.name,
                role="assistant",
                content=[],
                structured_output={"result": "pass", "message": "通过"},
            )

    monkeypatch.setattr(case_goal_workflow, "GoalPipeline", FakePipeline)
    monkeypatch.setattr(case_goal_workflow, "ArtifactStore", _RecordingStore)

    result = await run_case_authoring_artifact(REQUIREMENT)

    assert result.phase == "failed"
    assert result.passed is False
    assert any(item.code == "CASE_NUMBER_UNTRACEABLE" for item in result.facts.blocking)
    assert "TC-001" in result.reason


@pytest.mark.asyncio
async def test_pipeline_uses_single_executor_and_three_iters(monkeypatch):
    _fake_pipeline(monkeypatch, fill=True)
    captured: dict = {}
    original = case_goal_workflow.GoalPipeline

    class SpyPipeline(original):
        def __init__(self, executor, verifier, **kwargs):
            captured["kwargs"] = kwargs
            super().__init__(executor, verifier, **kwargs)

    monkeypatch.setattr(case_goal_workflow, "GoalPipeline", SpyPipeline)

    await run_case_authoring_artifact(REQUIREMENT)

    assert captured["kwargs"]["max_iters"] == 3
    assert captured["kwargs"]["verifier_reset_context"] is True
