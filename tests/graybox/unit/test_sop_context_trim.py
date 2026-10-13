"""SOP 上下文只保留最近 3 步截图，更早步骤收成文字结论。"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from agentscope.message import (
    AssistantMsg,
    Base64Source,
    DataBlock,
    TextBlock,
    ToolResultBlock,
    ToolResultState,
    UserMsg,
)
from agentscope.sop import SOPStepRunState

from engines.agents.workflow.context_trim import compress_older_steps, image_blocks

pytestmark = [pytest.mark.unit]


def _open_exec(subject: str):
    return UserMsg(
        name="sop",
        content=(
            "<system-reminder>You are running one step of the SOP.\n\n"
            f"## {subject}\n\n</system-reminder>"
        ),
    )


def _open_ver(description: str):
    return UserMsg(
        name="sop",
        content=(
            "<system-reminder>Judge the work below against what "
            f"this step had to prove.\n\n{description}</system-reminder>"
        ),
    )


def _shot(conclusion: str, *, nested: bool = False):
    image = DataBlock(source=Base64Source(data="aGVsbG8=", media_type="image/png"))
    if nested:
        content = [
            ToolResultBlock(
                id="shot-1",
                name="screenshot_page",
                output=[TextBlock(text="已截图"), image],
                state=ToolResultState.SUCCESS,
            )
        ]
    else:
        content = [TextBlock(text=conclusion), image]
    return AssistantMsg(
        name="executor",
        content=content,
        structured_output={"handover": conclusion},
    )


def _exec_steps(*names: str, nested_first: bool = False) -> list:
    rows = [UserMsg(name="user", content="开场")]
    for index, name in enumerate(names):
        rows.append(_open_exec(name))
        rows.append(_shot(f"{name}已完成", nested=nested_first and index == 0))
    return rows


def _texts(messages) -> str:
    parts: list[str] = []
    for msg in messages:
        content = msg.content
        if isinstance(content, str):
            parts.append(content)
            continue
        for block in content:
            parts.append(getattr(block, "text", "") or "")
    return "\n".join(parts)


def _images(messages) -> int:
    return sum(len(image_blocks(msg)) for msg in messages)


def test_new_step_keeps_only_two_finished_steps_of_screenshots() -> None:
    """新步骤还没进上下文，已完成的只留最近 2 步截图，更早的收成结论。"""
    messages = _exec_steps("甲", "乙", "丙", "丁", nested_first=True)
    trimmed = compress_older_steps(messages, upcoming_key="exec:戊")

    assert len(image_blocks(messages[2])) == 1
    text = _texts(trimmed)
    assert text.startswith("开场")
    assert "【此前步骤结论】甲" in text
    assert "甲已完成" in text
    assert "【此前步骤结论】乙" in text
    assert "## 丙" in text and "## 丁" in text
    assert _images(trimmed) == 2


def test_retry_keeps_the_current_step_with_the_previous_two() -> None:
    """重试与上一次同属一步，这一步的截图继续留着。"""
    messages = [
        *_exec_steps("甲", "乙", "丙"),
        _open_exec("丙"),
        _shot("丙第一次没点中"),
    ]
    trimmed = compress_older_steps(messages, upcoming_key="exec:丙")

    assert trimmed is messages
    assert _images(trimmed) == 4


def test_verifier_uses_the_assertion_as_the_step_key() -> None:
    """验收按要核对的结果分步，UI 步骤的旧截图同样收成文字结论。"""
    messages = []
    for name in ("页面出现开关", "颜色已选中", "亮度大于70", "弹窗已关闭"):
        messages.append(_open_ver(name))
        messages.append(
            AssistantMsg(
                name="verifier",
                content=[
                    TextBlock(text=name),
                    DataBlock(source=Base64Source(data="aGVsbG8=", media_type="image/png")),
                ],
                structured_output={"passed": True, "message": f"{name}看到了"},
            )
        )
    trimmed = compress_older_steps(messages, upcoming_key="ver:应用已退出")
    text = _texts(trimmed)

    assert "【此前步骤结论】页面出现开关" in text
    assert "通过。页面出现开关看到了" in text
    assert _images(trimmed) == 2


def test_step_trims_executor_context_before_a_fresh_attempt() -> None:
    """执行开始前裁剪；验收半程和挂起恢复不裁。"""
    from engines.agents.workflow import SopStepInput, SopSteps

    class _Role:
        def __init__(self, agent) -> None:
            self.agent = agent

    class _Agent:
        name = "stub"

        async def reply_stream(self, *args, **kwargs):
            if False:
                yield None

    executor = SimpleNamespace(state=SimpleNamespace(context=_exec_steps("甲", "乙", "丙", "丁")))
    verifier = SimpleNamespace(state=SimpleNamespace(context=[]))
    step = (
        SopSteps(
            _Role(executor),
            _Role(verifier),
            [SopStepInput("戊", "日志出现关闭成功")],
        )
        .build()
        .steps[0]
    )

    step._trim_context([UserMsg(name="sop", content="开场")], SOPStepRunState())
    assert _images(executor.state.context) == 2
    assert "【此前步骤结论】甲" in _texts(executor.state.context)

    fresh = _exec_steps("甲", "乙", "丙", "丁")
    executor.state.context = list(fresh)
    state = SOPStepRunState()
    state.submission = [TextBlock(text="已交出")]
    step._trim_context(None, state)
    assert _images(executor.state.context) == 4

    step._trim_context(object(), SOPStepRunState())
    assert _images(executor.state.context) == 4
