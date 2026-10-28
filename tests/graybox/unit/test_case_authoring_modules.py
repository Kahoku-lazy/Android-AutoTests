"""模块化用例编写：规划切分、截断拆分、文本拼装与整份模式回退。"""

from __future__ import annotations

import pytest

from engines.agents.workflow import case_authoring_workflow as workflow_module
from engines.agents.workflow.case_authoring_workflow import (
    CASE_MAX_ATTEMPTS,
    CaseAuthoringResult,
    build_run_input,
    run_case_authoring_modules,
)
from engines.agents.workflow.case_module_plan import (
    MIN_SPLIT_LINES,
    ModuleRange,
    ModuleSpec,
    build_module_document,
    fallback_modules,
    normalize_modules,
    split_module,
)

pytestmark = [pytest.mark.unit]


def _module(key: str, name: str, lines: list[str], start: int = 1) -> ModuleRange:
    return ModuleRange(
        key=key,
        name=name,
        start_line=start,
        end_line=start + len(lines) - 1,
        text="\n".join(lines),
    )


def test_build_run_input_adds_module_scope_and_atom_range():
    """模块化输入给出模块名、KEY 与原子编号区段，需求标题改为片段。"""
    text = build_run_input(
        "待机下单击 POWER 开机",
        project_code="H717D",
        module_name="按键与模式",
        module_key="BTN",
        atom_start=101,
    )

    assert "## 本次模块" in text
    assert "模块名：按键与模式" in text
    assert "模块KEY：BTN" in text
    assert "REQ-101 ~ REQ-200" in text
    assert "## 本模块需求片段" in text
    assert "## 需求正文" not in text


def test_build_run_input_keeps_full_mode_without_module_key():
    """未给模块 KEY 时保持整份文档输入。"""
    text = build_run_input("需求正文")
    assert "## 需求正文\n需求正文" in text
    assert "## 本次模块" not in text


def test_fallback_modules_splits_long_requirement_and_covers_lines():
    """长需求按章节/固定行数切块，至少两块且不丢内容。"""
    lines = [f"## {index}. 功能 {index}" for index in range(1, 25)]
    lines += [f"需求内容 {index}" for index in range(1, 120)]
    text = "\n".join(lines)

    modules = fallback_modules(text)

    assert len(modules) >= 2
    assert all(module.text.strip() for module in modules)
    assert sum(len(module.text.splitlines()) for module in modules) >= len(lines) * 0.9


def test_fallback_modules_keeps_short_requirement_whole():
    """非空行不足拆分门槛时只返回一个模块。"""
    text = "\n".join(f"需求 {index}" for index in range(MIN_SPLIT_LINES))

    modules = fallback_modules(text)

    assert len(modules) == 1
    assert modules[0].key == "ALL"


def test_normalize_modules_clamps_overlap_and_repairs_keys():
    """重叠区间被拉开、非法 key 被补齐，覆盖率达标才返回。"""
    text = "\n".join(f"第 {index} 行需求" for index in range(1, 121))
    specs = [
        ModuleSpec(key="btn", name="按键", start_line=1, end_line=60),
        ModuleSpec(key="btn", name="指示灯", start_line=50, end_line=120),
    ]

    modules = normalize_modules(text, specs)

    assert len(modules) == 2
    assert modules[0].end_line < modules[1].start_line
    assert modules[0].key != modules[1].key
    assert all(len(module.key) >= 3 for module in modules)


def test_normalize_modules_falls_back_when_ranges_leave_gaps():
    """规划只覆盖一小段时整份回退，避免丢需求。"""
    text = "\n".join(f"第 {index} 行需求" for index in range(1, 300))
    specs = [ModuleSpec(key="BTN", name="按键", start_line=1, end_line=5)]

    modules = normalize_modules(text, specs)

    assert len(modules) > 1


def test_split_module_halves_at_blank_line():
    """截断模块在中点空行处一分为二，行区间连续。"""
    lines = [f"需求 {index}" for index in range(1, 41)]
    lines[20] = ""
    module = _module("BTN", "按键", lines, start=10)

    parts = split_module(module)

    assert parts is not None
    first, second = parts
    assert first.start_line == 10
    assert first.end_line + 1 == second.start_line
    assert second.end_line == module.end_line
    assert first.key != second.key


def test_build_module_document_marks_each_module_status():
    """拼接文档带模块标题、验收状态与分隔线。"""
    first = CaseAuthoringResult(
        phase="completed", document="## 一、需求原子表\nA", verdicts=((True, "ok", "verifier"),)
    )
    second = CaseAuthoringResult(
        phase="failed", document="## 一、需求原子表\nB", verdicts=((False, "bad", "verifier"),)
    )

    text = build_module_document(
        [
            (_module("BTN", "按键", ["需求"]), first),
            (_module("IND", "指示灯", ["需求"]), second),
        ],
        "H717D",
        "V1",
    )

    assert "H717D / V1" in text
    assert "模块：按键（BTN）· 验收 PASS" in text
    assert "模块：指示灯（IND）· 验收 FAIL" in text
    assert "## 一、需求原子表\nA" in text


def test_case_result_truncated_is_never_passed():
    """截断结果即使有 pass 判决也只能算未通过。"""
    result = CaseAuthoringResult(
        phase="failed",
        document="半截",
        verdicts=((True, "sop", "sop"),),
        truncated=True,
    )
    assert result.passed is False


def test_module_outcome_marks_truncated_message():
    """截断模块的摘要写 OUTPUT_TRUNCATED，不被空判决覆盖。"""
    result = CaseAuthoringResult(phase="failed", document="半截", verdicts=(), truncated=True)
    module = _module("BTN", "按键", ["需求"])
    outcome = workflow_module._module_outcome(module, result)

    assert outcome.truncated is True
    assert "OUTPUT_TRUNCATED" in outcome.message
    assert outcome.document_length == len("半截")


@pytest.mark.asyncio
async def test_pipeline_splits_truncated_module_and_combines(monkeypatch):
    """首块截断时自动拆成两块重跑，全部通过后拼装为一篇文档。"""
    monkeypatch.setenv("CASE_AUTHORING_ENGINE", "sop")
    lines = [f"需求 {index}" for index in range(1, 41)]
    lines[20] = ""
    root = _module("BTN", "按键", lines)
    calls: list[str] = []

    async def fake_plan(*args, **kwargs):
        return (root,)

    class FakeWorkflow:
        def __init__(self, writer, verifier):
            pass

        async def run(self, run_input):
            calls.append(run_input)
            if len(calls) == 1:
                return CaseAuthoringResult(
                    phase="failed", document="半截", verdicts=(), truncated=True
                )
            return CaseAuthoringResult(
                phase="completed",
                document="## 一、需求原子表\n完整",
                verdicts=((True, "通过", "case_verifier_role"),),
            )

    monkeypatch.setattr(workflow_module, "plan_case_modules", fake_plan)
    monkeypatch.setattr(workflow_module, "CaseAuthoringWorkflow", FakeWorkflow)

    result = await run_case_authoring_modules("需求正文占位")

    assert len(calls) == 3
    assert result.passed is True
    assert result.truncated is False
    assert len(result.modules) == 2
    assert "模块：按键（上）" in result.document
    assert "验收 PASS" in result.document


@pytest.mark.asyncio
async def test_workflow_retry_feeds_previous_document_and_verdict(monkeypatch):
    """重写时把上一版文档一并交给编写角色，避免整篇重写引入新错。"""
    workflow = workflow_module.CaseAuthoringWorkflow(object(), object(), max_attempts=2)
    inputs: list[str] = []

    async def fake_run_once(run_input):
        inputs.append(run_input)
        if len(inputs) == 1:
            return CaseAuthoringResult(
                phase="failed",
                document="旧文档正文",
                verdicts=((False, "[阻断] 只修这条", "case_verifier_role"),),
            )
        return CaseAuthoringResult(
            phase="completed",
            document="新文档",
            verdicts=((True, "通过", "case_verifier_role"),),
        )

    monkeypatch.setattr(workflow, "_run_once", fake_run_once)
    result = await workflow.run("需求正文")

    assert "旧文档正文" in inputs[1]
    assert "[阻断] 只修这条" in inputs[1]
    assert "未点名的段落" in inputs[1]
    assert result.passed is True


@pytest.mark.asyncio
async def test_workflow_tries_three_times_by_default(monkeypatch):
    """默认首稿 + 两次重写；三次都驳回才判失败。"""
    workflow = workflow_module.CaseAuthoringWorkflow(object(), object())
    calls: list[str] = []

    async def fake_run_once(run_input):
        calls.append(run_input)
        return CaseAuthoringResult(
            phase="failed",
            document=f"第 {len(calls)} 版",
            verdicts=((False, f"[阻断] 第 {len(calls)} 版问题", "case_verifier_role"),),
        )

    monkeypatch.setattr(workflow, "_run_once", fake_run_once)
    result = await workflow.run("需求正文")

    assert CASE_MAX_ATTEMPTS == 3
    assert workflow.max_attempts == 3
    assert len(calls) == 3
    assert result.passed is False
    assert "第 2 版" in calls[2]


@pytest.mark.asyncio
async def test_pipeline_keeps_full_mode_for_single_all_module(monkeypatch):
    """只有 ALL 模块时保持整份文档模式，不强行加模块标题。"""
    monkeypatch.setenv("CASE_AUTHORING_ENGINE", "sop")
    root = ModuleRange("ALL", "全部需求", 1, 2, "需求正文")
    captured: dict[str, str] = {}

    async def fake_plan(*args, **kwargs):
        return (root,)

    class FakeWorkflow:
        def __init__(self, writer, verifier):
            pass

        async def run(self, run_input):
            captured["input"] = run_input
            return CaseAuthoringResult(
                phase="completed",
                document="## 一、需求原子表\n完整",
                verdicts=((True, "通过", "case_verifier_role"),),
            )

    monkeypatch.setattr(workflow_module, "plan_case_modules", fake_plan)
    monkeypatch.setattr(workflow_module, "CaseAuthoringWorkflow", FakeWorkflow)

    result = await run_case_authoring_modules("需求正文")

    assert "## 本次模块" not in captured["input"]
    assert result.document == "## 一、需求原子表\n完整"
    assert "> 需求按模块拆分" not in result.document
