"""
文件名: ➡️ case_artifact_render.py 🏁
路径: ➡️ engines/agents/workflow/case_artifact_render.py 🏁
模块功能：➡️ 把三段式产物确定性渲染成 Markdown 文档与 Mermaid 状态图 🏁
Python 调试：➡️ python -m engines.agents.workflow.case_artifact_render 🏁
时间：➡️ 2026-11-05 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-05 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. render_markdown: 状态机摘要 + 场景表 + 用例表，顺序固定，供人读与入库追溯。
2. render_mermaid: stateDiagram-v2 状态图，只由产物派生，不允许模型另写一份。
3. render: 一次产出文档与图，二者永远同源。
🏁
关联模块：➡️
1. engines/agents/workflow/case_artifact.py: 导入 Artifact 及各条目数据类
🏁
测试：➡️
1. tests/graybox/unit/test_case_artifact_render.py: 单文件调试指令：python -m pytest tests/graybox/unit/test_case_artifact_render.py -vv --tb=short
🏁
"""

from __future__ import annotations

from engines.agents.workflow.case_artifact import Artifact

__all__ = ["render", "render_markdown", "render_mermaid"]

# Mermaid 里需要转义的字符：引号会截断 state 标签，反斜杠会吃掉后一个字符
_MERMAID_ESCAPE = {"\\": "/", '"': "'", "\n": " "}


def _cell(text: str) -> str:
    """把文本收成表格单元格安全的一行。"""
    return str(text or "").replace("|", "\\|").replace("\n", " ").strip() or "-"


def _flag(value: bool) -> str:
    """布尔值的中文显示。"""
    return "是" if value else "否"


def _state_label(text: str) -> str:
    """Mermaid state 标签转义。"""
    for source, target in _MERMAID_ESCAPE.items():
        text = text.replace(source, target)
    return text.strip()


def render_mermaid(artifact: Artifact) -> str:
    """把状态机渲染成 Mermaid stateDiagram-v2。

    Args:
        artifact: 三段产物。

    Returns:
        Mermaid 文本；没有状态时返回空串。
    """
    if not artifact.states:
        return ""
    lines = ["stateDiagram-v2"]
    for state in artifact.states:
        mark = "" if state.observable else "（不可观察）"
        lines.append(f'    state "{_state_label(state.name)}{mark}" as {_state_label(state.id)}')
    for transition in artifact.transitions:
        source = _state_label(transition.from_state)
        target = _state_label(transition.to_state)
        label = _state_label(transition.event)
        if transition.guard:
            label = f"{label} [{_state_label(transition.guard)}]"
        lines.append(f"    {source} --> {target} : {label}")
    return "\n".join(lines)


def _state_table(artifact: Artifact) -> list[str]:
    """状态与迁移两张表。"""
    lines = [
        "| 状态 ID | 名称 | 可观察 | 观察手段 | 出处 |",
        "|---|---|:--:|---|---|",
    ]
    for state in artifact.states:
        name = state.name + ("（待确认）" if state.uncertain else "")
        lines.append(
            f"| {_cell(state.id)} | {_cell(name)} | {_flag(state.observable)} | "
            f"{_cell(state.observe_by)} | {_cell(state.source)} |"
        )
    lines.extend(
        [
            "",
            "| 迁移 ID | 从 | 到 | 触发 | 条件 | 副作用 | 出处 |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for transition in artifact.transitions:
        lines.append(
            f"| {_cell(transition.id)} | {_cell(transition.from_state)} | "
            f"{_cell(transition.to_state)} | {_cell(transition.event)} | "
            f"{_cell(transition.guard)} | {_cell(transition.effect)} | "
            f"{_cell(transition.source)} |"
        )
    return lines


def _scenario_table(artifact: Artifact) -> list[str]:
    """场景表。"""
    lines = [
        "| 场景 ID | 标题 | 类型 | 路径 | 覆盖迁移 | 出处 |",
        "|---|---|---|---|---|---|",
    ]
    for scenario in artifact.scenarios:
        lines.append(
            f"| {_cell(scenario.id)} | {_cell(scenario.title)} | {_cell(scenario.type)} | "
            f"{_cell(' → '.join(scenario.path))} | {_cell('、'.join(scenario.transitions))} | "
            f"{_cell(scenario.source)} |"
        )
    return lines


def _case_table(artifact: Artifact) -> list[str]:
    """用例表：步骤按「动作 → 期望状态」逐条摊开。"""
    lines = [
        "| 用例 ID | 标题 | 场景 | 起始状态 | 步骤 | 边界 | 方法 | 优先级 | 出处 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for case in artifact.cases:
        steps = "<br>".join(
            f"{index}) {step.action} → {step.expect_state}"
            for index, step in enumerate(case.steps, start=1)
        )
        boundaries = "<br>".join(
            f"{entry.param}：{'/'.join(entry.values)}" for entry in case.boundary
        )
        title = case.title + ("（待确认）" if case.uncertain else "")
        lines.append(
            f"| {_cell(case.id)} | {_cell(title)} | {_cell(case.scenario_id)} | "
            f"{_cell(case.pre_state)} | {_cell(steps)} | {_cell(boundaries)} | "
            f"{_cell('、'.join(case.method))} | {_cell(case.priority)} | "
            f"{_cell(case.source)} |"
        )
    return lines


def render_markdown(artifact: Artifact) -> str:
    """把三段产物渲染成 Markdown 文档。

    Args:
        artifact: 三段产物。

    Returns:
        依次含状态机摘要、场景表、用例表的文档；产物为空时给出可读空态。
    """
    counts = artifact.counts
    lines = [
        "# 测试用例（状态机 → 业务流场景 → 用例）",
        "",
        f"> 状态 {counts['states']} 个、迁移 {counts['transitions']} 条、"
        f"场景 {counts['scenarios']} 条、用例 {counts['cases']} 条。",
        "",
        "## 一、需求状态机",
        "",
    ]
    if not artifact.states:
        lines.append("（尚未产出状态机）")
    else:
        lines.extend(_state_table(artifact))
    lines.extend(["", "## 二、业务流场景", ""])
    if not artifact.scenarios:
        lines.append("（尚未产出场景）")
    else:
        lines.extend(_scenario_table(artifact))
    lines.extend(["", "## 三、测试用例", ""])
    if not artifact.cases:
        lines.append("（尚未产出用例）")
    else:
        lines.extend(_case_table(artifact))
    return "\n".join(lines)


def render(artifact: Artifact) -> tuple[str, str]:
    """一次渲染文档与状态图。

    Args:
        artifact: 三段产物。

    Returns:
        (Markdown 文档, Mermaid 状态图)。
    """
    return render_markdown(artifact), render_mermaid(artifact)
