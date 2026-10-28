"""GoalPipeline 模块池：模块存储、单模块判定与截断兜底。"""

from __future__ import annotations

import pytest

from agentscope.message import Msg

from engines.agents.tools.tool_case_module_store import ModuleStore
from engines.agents.workflow import case_goal_workflow
from engines.agents.workflow.case_goal_workflow import run_goal_module

pytestmark = [pytest.mark.unit]


@pytest.fixture(autouse=True)
def _dummy_key(monkeypatch):
    """构造角色只需要非空密钥，不会发起模型调用（GoalPipeline 被替换）。"""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")


def test_module_store_saves_and_reads_document():
    store = ModuleStore()

    store.save("BTN", "# 文档")

    assert store.get("BTN") == "# 文档"
    assert store.get("NOPE") == ""


@pytest.mark.asyncio
async def test_goal_module_passes_when_document_saved_and_verifier_passes(monkeypatch):
    store = ModuleStore()

    class FakePipeline:
        def __init__(self, executor, verifier, **kwargs):
            self.verifier = verifier

        async def reply_stream(self, inputs):
            store.save("BTN", "# 一、需求原子表\n" + "用例内容" * 80)
            yield Msg(
                name=self.verifier.name,
                role="assistant",
                content=[],
                structured_output={"result": "pass", "message": "通过"},
            )

    monkeypatch.setattr(case_goal_workflow, "GoalPipeline", FakePipeline)
    monkeypatch.setattr(
        case_goal_workflow, "check_and_fix_document", lambda document: (document, [])
    )

    result = await run_goal_module("需求正文", "BTN", store)

    assert result.passed is True
    assert result.truncated is False
    assert result.verdicts == ((True, "通过", "case_verifier_role"),)
    assert store.get("BTN") in result.document


@pytest.mark.asyncio
async def test_goal_module_deterministic_issue_blocks_pass(monkeypatch):
    store = ModuleStore()

    class FakePipeline:
        def __init__(self, executor, verifier, **kwargs):
            self.verifier = verifier

        async def reply_stream(self, inputs):
            store.save("BTN", "# 一、需求原子表\n" + "用例内容" * 80)
            yield Msg(
                name=self.verifier.name,
                role="assistant",
                content=[],
                structured_output={"result": "pass", "message": "通过"},
            )

    monkeypatch.setattr(case_goal_workflow, "GoalPipeline", FakePipeline)
    monkeypatch.setattr(
        case_goal_workflow,
        "check_and_fix_document",
        lambda document: (document, ["缺少章节：第七节"]),
    )

    result = await run_goal_module("需求正文", "BTN", store)

    assert result.passed is False
    assert any(item[2] == "case_deterministic_check" for item in result.verdicts)
    assert "缺少章节" in result.verdicts[-1][1]


@pytest.mark.asyncio
async def test_goal_module_without_document_is_truncated(monkeypatch):
    store = ModuleStore()

    class FakePipeline:
        def __init__(self, executor, verifier, **kwargs):
            self.verifier = verifier

        async def reply_stream(self, inputs):
            yield Msg(
                name=self.verifier.name,
                role="assistant",
                content=[],
                structured_output={"result": "pass", "message": "通过"},
            )

    monkeypatch.setattr(case_goal_workflow, "GoalPipeline", FakePipeline)

    result = await run_goal_module("需求正文", "BTN", store)

    assert result.passed is False
    assert result.truncated is True
    assert result.document == ""
