"""每个 SOP 步骤新建一对角色实例：实例互不相同、步骤提示按步拼装。"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import engines.agents.workflow.ui_auto_workflow as workflow_module
from engines.agents.workflow.case_file import CaseStep, LogEvidence

pytestmark = [pytest.mark.unit]


class _Agent:
    """最小角色替身：只要 name 与 model。"""

    def __init__(self, name: str) -> None:
        self.name = name
        self.model = SimpleNamespace(model="fake-model")


class _SOP:
    """SOP 替身：只留名字与步骤，供断言检查。"""

    def __init__(self, name: str, steps: list) -> None:
        self.name = name
        self.steps = steps


class _Engine:
    """SOPEngine 替身：不真的跑模型，只暴露空的运行状态。"""

    def __init__(self, sop: _SOP) -> None:
        self.sop = sop
        self.state = SimpleNamespace(steps=[])
        self.phase = "running"

    async def reply_stream(self, inputs=None):
        """不产出任何事件，模拟一次立即结束的推进。"""
        return
        yield  # noqa: unreachable - 让函数保持异步生成器语义


async def _run(monkeypatch: pytest.MonkeyPatch, steps: list[CaseStep]):
    """用替身跑一次装配，返回（工作流, 每次工厂调用记录）。"""
    built: list[tuple[str, _Agent]] = []

    def executor_factory():
        agent = _Agent("ui_executor_role")
        built.append(("executor", agent))
        return agent

    def verifier_factory():
        agent = _Agent("ui_verifier_role")
        built.append(("verifier", agent))
        return agent

    monkeypatch.setattr(workflow_module, "SOP", _SOP)
    monkeypatch.setattr(workflow_module, "SOPEngine", _Engine)
    workflow = workflow_module.AgentSOPWorkflow(executor_factory, verifier_factory)
    phase = await workflow.run_workflow("测试流程", steps, "开场输入")
    return workflow, built, phase


async def test_each_step_builds_its_own_agents(monkeypatch: pytest.MonkeyPatch) -> None:
    """两步的流程会调用两次执行者工厂与两次验收者工厂，实例互不相同。"""
    steps = [
        CaseStep(action="第一步动作", expected="第一步结果"),
        CaseStep(action="第二步动作", expected="第二步结果"),
    ]

    _, built, phase = await _run(monkeypatch, steps)

    executors = [agent for kind, agent in built if kind == "executor"]
    verifiers = [agent for kind, agent in built if kind == "verifier"]
    assert phase == "running"
    assert len(executors) == 2 and len(verifiers) == 2
    assert len({id(agent) for agent in executors}) == 2
    assert len({id(agent) for agent in verifiers}) == 2


async def test_opening_context_is_replayed_on_every_step(monkeypatch: pytest.MonkeyPatch) -> None:
    """设备 serial 这类开场上下文必须出现在每一步的两份提示里。"""
    steps = [
        CaseStep(action="第一步动作", expected="第一步结果"),
        CaseStep(action="第二步动作", expected="第二步结果"),
    ]
    captured: list[_SOP] = []

    def engine_factory(sop: _SOP) -> _Engine:
        captured.append(sop)
        return _Engine(sop)

    monkeypatch.setattr(workflow_module, "SOP", _SOP)
    monkeypatch.setattr(workflow_module, "SOPEngine", engine_factory)
    workflow = workflow_module.AgentSOPWorkflow(
        lambda: _Agent("ui_executor_role"),
        lambda: _Agent("ui_verifier_role"),
    )
    await workflow.run_workflow("测试流程", steps, "本次要操作的设备 serial 是：R5CT62RH88F。")

    for step in captured[0].steps:
        assert "R5CT62RH88F" in step.subject
        assert "R5CT62RH88F" in step.description


async def test_step_briefs_are_built_per_step(monkeypatch: pytest.MonkeyPatch) -> None:
    """锚点进执行者提示、日志证据进验收者提示，且两步的内容互不串味。"""
    steps = [
        CaseStep(
            action="设置 5:00 定时",
            expected="定时列表出现 5:00",
            anchor={"page": "定时页"},
            log=LogEvidence(sku="H6810", port=7005, keywords=("timer_configs_set_success",)),
        ),
        CaseStep(action="回到桌面", expected="桌面可见"),
    ]

    captured: list[_SOP] = []

    def engine_factory(sop: _SOP) -> _Engine:
        captured.append(sop)
        return _Engine(sop)

    monkeypatch.setattr(workflow_module, "SOP", _SOP)
    monkeypatch.setattr(workflow_module, "SOPEngine", engine_factory)
    workflow = workflow_module.AgentSOPWorkflow(
        lambda: _Agent("ui_executor_role"),
        lambda: _Agent("ui_verifier_role"),
    )
    await workflow.run_workflow("测试流程", steps, "开场输入")

    first, second = captured[0].steps
    assert "设置 5:00 定时" in first.subject
    assert "【本步页面锚点】" in first.subject
    assert "timer_configs_set_success" not in first.subject
    assert "定时列表出现 5:00" not in first.subject

    assert "定时列表出现 5:00" in first.description
    assert "keyword=timer_configs_set_success" in first.description
    assert "设置 5:00 定时" not in first.description
    assert "【本步页面锚点】" not in first.description

    assert second.subject.endswith("回到桌面")
    assert second.description.endswith("桌面可见")
    assert second.subject.startswith("开场输入")
    assert second.description.startswith("开场输入")


async def test_case_sku_fills_keyword_catalog_for_steps_without_log(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """用例没写 log 时，用标题里的型号把关键词表补进验收提示。"""
    steps = [CaseStep(action="设置定时", expected="定时列表出现新时间")]
    captured: list[_SOP] = []

    def engine_factory(sop: _SOP) -> _Engine:
        captured.append(sop)
        return _Engine(sop)

    monkeypatch.setattr(workflow_module, "SOP", _SOP)
    monkeypatch.setattr(workflow_module, "SOPEngine", engine_factory)
    workflow = workflow_module.AgentSOPWorkflow(
        lambda: _Agent("ui_executor_role"),
        lambda: _Agent("ui_verifier_role"),
    )
    await workflow.run_workflow("H6810 定时功能测试", steps, "设备 R5CT62RH88F。", default_sku="H6810")

    description = captured[0].steps[0].description
    assert "【本步关键词表】" in description
    assert "timer_configs_set_success" in description
    assert "【本步日志证据】" not in description


async def test_empty_steps_are_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    """步骤列表为空时拒绝装配。"""
    monkeypatch.setattr(workflow_module, "SOP", _SOP)
    monkeypatch.setattr(workflow_module, "SOPEngine", _Engine)
    workflow = workflow_module.AgentSOPWorkflow(_Agent, _Agent)

    with pytest.raises(ValueError, match="步骤列表为空"):
        await workflow.run_workflow("空流程", [], "开场输入")
