"""步骤输入装配：短名、必须达成的结果，以及已启动的角色。"""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.unit]


class _Role:
    def __init__(self, agent, prompt: str = "原提示词") -> None:
        self.agent = agent
        self.system_prompt = prompt
        self.toolkit = object()


class _Agent:
    name = "stub"

    async def reply_stream(self, *args, **kwargs):
        if False:
            yield None


def test_complete_steps_keep_order_and_roles() -> None:
    """完整步骤按提交顺序装配，并绑上已启动角色的 Agent。"""
    from engines.agents.workflow import SopStepInput, SopSteps

    executor_agent = _Agent()
    verifier_agent = _Agent()
    executor = _Role(executor_agent, "执行提示词")
    verifier = _Role(verifier_agent, "验收提示词")
    toolkit = executor.toolkit
    sop = SopSteps(
        executor,
        verifier,
        [
            SopStepInput("关灯", "日志出现关闭成功"),
            SopStepInput("开灯", "日志出现打开成功"),
        ],
        max_attempts=2,
    ).build()

    assert [step.subject for step in sop.steps] == ["关灯", "开灯"]
    assert [step.description for step in sop.steps] == [
        "日志出现关闭成功",
        "日志出现打开成功",
    ]
    assert sop.steps[0].executor is executor_agent
    assert sop.steps[1].executor is executor_agent
    assert sop.steps[0].verifier is verifier_agent
    assert sop.steps[0].max_attempts == 2
    assert executor.system_prompt == "执行提示词"
    assert verifier.system_prompt == "验收提示词"
    assert executor.toolkit is toolkit


def test_empty_or_blank_steps_are_rejected() -> None:
    """空列表、空短名或空结果都不能装配。"""
    from engines.agents.workflow import SopStepInput, SopSteps

    role = _Role(_Agent())
    with pytest.raises(ValueError, match="步骤列表为空"):
        SopSteps(role, role, []).build()
    with pytest.raises(ValueError, match="都不能为空"):
        SopSteps(role, role, [SopStepInput("  ", "日志出现关闭成功")]).build()
    with pytest.raises(ValueError, match="都不能为空"):
        SopSteps(role, role, [SopStepInput("关灯", "")]).build()


def test_each_role_is_asked_only_its_own_text() -> None:
    """执行提示只有动作，验收提示只有结果；驳回说明只回到执行侧。"""
    from agentscope.message import TextBlock
    from agentscope.sop import SOPStepRunState

    from engines.agents.workflow import SopStepInput, SopSteps

    role = _Role(_Agent())
    sop = SopSteps(
        role,
        role,
        [SopStepInput("点击开关", "日志出现关闭成功")],
        max_attempts=2,
    ).build()
    step = sop.steps[0]
    state = SOPStepRunState()
    state.submission = [TextBlock(text="已点击时间戳")]

    executor_text = _msg_text(step._brief(None, state))
    verifier_text = _msg_text(step._question(None, state))
    assert "点击开关" in executor_text
    assert "日志出现关闭成功" not in executor_text
    assert "日志出现关闭成功" in verifier_text
    assert "点击开关" not in verifier_text
    assert "已点击时间戳" in verifier_text

    step.record(state, False, "没点中开关", "verifier")
    assert "没点中开关" in _msg_text(step._brief(None, state))
    assert "没点中开关" not in _msg_text(step._question(None, state))

    paused = object()
    assert step._brief(paused, state) is paused
    assert step._question(paused, state) is paused


def _msg_text(messages) -> str:
    """把提问消息里的文本拼成一段，便于断言包含关系。"""
    parts: list[str] = []
    for msg in messages:
        content = msg.content
        if isinstance(content, str):
            parts.append(content)
            continue
        for block in content:
            parts.append(getattr(block, "text", "") or "")
    return "\n".join(parts)


def test_unstarted_role_names_which_one() -> None:
    """还没 start() 的角色会在报错里指出是执行还是验收。"""
    from engines.agents.workflow import SopStepInput, SopSteps

    started = _Role(_Agent())
    idle = _Role(None)
    step = SopStepInput("关灯", "日志出现关闭成功")
    with pytest.raises(RuntimeError, match="执行角色还没 start"):
        SopSteps(idle, started, [step]).build()
    with pytest.raises(RuntimeError, match="验收角色还没 start"):
        SopSteps(started, idle, [step]).build()
