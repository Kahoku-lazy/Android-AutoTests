"""
文件名: ➡️ case_artifact_facts.py 🏁
路径: ➡️ engines/agents/workflow/case_artifact_facts.py 🏁
模块功能：➡️ 三段式产物的事实预检：出处真实、引用完整、数值可追溯 🏁
Python 调试：➡️ python -m engines.agents.workflow.case_artifact_facts 🏁
时间：➡️ 2026-11-05 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-05 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. FactIssue / FactReport: 一条确定性问题或告警，以及整份预检结论。
2. check_artifact_facts: 用需求正文核对产物，只查可机器判定的三类事实。
3. format_facts: 把结论摊成可读文本，供验收工具与任务结果共用。
4. 覆盖率类指标只进告警，不参与通过与否。
🏁
关联模块：➡️
1. engines/agents/workflow/case_artifact.py: 导入 Artifact 与各条目数据类
2. engines/agents/tools/tool_case_artifact.py: 把 format_facts 暴露成只读工具
🏁
测试：➡️
1. tests/graybox/unit/test_case_artifact_facts.py: 单文件调试指令：python -m pytest tests/graybox/unit/test_case_artifact_facts.py -vv --tb=short
🏁
"""

from __future__ import annotations

import re

from dataclasses import dataclass

from engines.agents.workflow.case_artifact import Artifact

__all__ = [
    "FactIssue",
    "FactReport",
    "check_artifact_facts",
    "format_facts",
]

# 归一化时剔除的空白：半角、全角、制表与换行
_SPACES = re.compile(r"[\s\u3000]+")
# 从「动作」里抽数值：整数、小数、百分比、HH:MM 时间
_NUMBER = re.compile(r"\d{1,2}:\d{2}|\d+(?:\.\d+)?%?")
# 允许紧跟数字的单位后缀；其余 ASCII 字母说明这是型号或编号的一部分（H717D 里的 717 不算数值）
_UNIT_SUFFIX = frozenset({"s", "S"})
# 找近似原文时用的窗口长度；太短会到处命中，太长则几乎找不到
_EXCERPT_WINDOWS = (40, 30, 24, 18, 14, 10, 8)


@dataclass(frozen=True)
class FactIssue:
    """
    一条预检结论。

    Attributes:
        code: 机器码，例如 SOURCE_NOT_IN_REQUIREMENT。
        where: 位置，例如「用例 TC-001」。
        detail: 可读说明。
        excerpt: 需求原文里最接近的片段；找不到时为空。
    """

    code: str
    where: str
    detail: str
    excerpt: str = ""

    def render(self) -> str:
        """摊成一行可读文本。"""
        tail = f"；需求原文相近片段：「{self.excerpt}」" if self.excerpt else ""
        return f"[{self.where}] {self.detail}{tail}"


@dataclass(frozen=True)
class FactReport:
    """
    一次事实预检的结论。

    Attributes:
        blocking: 确定性问题；存在任一条时该轮不得判为通过。
        warnings: 告警；不参与通过与否。
    """

    blocking: tuple[FactIssue, ...] = ()
    warnings: tuple[FactIssue, ...] = ()

    @property
    def passed(self) -> bool:
        """没有确定性问题即为通过。"""
        return not self.blocking

    def payload(self) -> dict:
        """还原成可 JSON 序列化的字典。"""
        return {
            "blocking": [
                {
                    "code": item.code,
                    "where": item.where,
                    "detail": item.detail,
                    "excerpt": item.excerpt,
                }
                for item in self.blocking
            ],
            "warnings": [
                {
                    "code": item.code,
                    "where": item.where,
                    "detail": item.detail,
                    "excerpt": item.excerpt,
                }
                for item in self.warnings
            ],
        }


def _normalize(text: str) -> str:
    """去掉全部空白，供子串比对。"""
    return _SPACES.sub("", str(text or ""))


def _excerpt(needle: str, haystack: str) -> str:
    """在需求正文里找与 needle 最接近的一段。

    Args:
        needle: 模型给的 source。
        haystack: 已归一化的需求正文。

    Returns:
        需求里长度接近 needle 的一段原文；找不到时返回空串。
    """
    source = _normalize(needle)
    if not source or not haystack:
        return ""
    for size in _EXCERPT_WINDOWS:
        if size > len(source):
            continue
        for start in range(0, len(source) - size + 1):
            window = source[start : start + size]
            hit = haystack.find(window)
            if hit < 0:
                continue
            begin = max(hit - start, 0)
            return haystack[begin : begin + min(len(source), 120)]
    return ""


def _source_issue(where: str, source: str, requirement: str) -> FactIssue | None:
    """核对一条 source 是否为需求正文子串。

    Args:
        where: 位置描述。
        source: 条目携带的 source。
        requirement: 已归一化的需求正文。

    Returns:
        不在原文里时返回问题；命中时返回 None。
    """
    if _normalize(source) in requirement:
        return None
    return FactIssue(
        code="SOURCE_NOT_IN_REQUIREMENT",
        where=where,
        detail=f"出处不在需求原文中：「{source}」",
        excerpt=_excerpt(source, requirement),
    )


def _numbers(text: str) -> set[str]:
    """抽取文本里的数值字面量，跳过型号与编号里的数字。

    Args:
        text: 待抽取的文本，通常是用例某一步的动作。

    Returns:
        独立出现的数值字面量集合；`H717D` 的 717、`v2` 的 2 不算。
    """
    raw = str(text or "")
    found: set[str] = set()
    for match in _NUMBER.finditer(raw):
        start, end = match.span()
        before = raw[start - 1] if start else ""
        after = raw[end] if end < len(raw) else ""
        if before.isascii() and before.isalpha():
            continue
        if after.isascii() and after.isalpha() and after not in _UNIT_SUFFIX:
            continue
        found.add(match.group(0))
    return found


def check_artifact_facts(artifact: Artifact, requirement_text: str) -> FactReport:
    """用需求正文核对产物，只查三类可机器判定的事实。

    Args:
        artifact: 三段产物。
        requirement_text: 需求正文。

    Returns:
        含确定性问题与告警的结论；没有任何产物时给出空告警。
    """
    requirement = _normalize(requirement_text)
    blocking: list[FactIssue] = []
    warnings: list[FactIssue] = []

    state_ids = {state.id for state in artifact.states}
    transition_ids = {transition.id for transition in artifact.transitions}
    scenario_ids = {scenario.id for scenario in artifact.scenarios}

    for state in artifact.states:
        issue = _source_issue(f"状态 {state.id}", state.source, requirement)
        if issue:
            blocking.append(issue)
        if state.observable and not state.observe_by.strip():
            blocking.append(
                FactIssue(
                    code="STATE_OBSERVE_BY_MISSING",
                    where=f"状态 {state.id}",
                    detail="observable=true 但没有给出观察手段",
                )
            )

    for transition in artifact.transitions:
        issue = _source_issue(f"迁移 {transition.id}", transition.source, requirement)
        if issue:
            blocking.append(issue)
        for attr, value in (("from", transition.from_state), ("to", transition.to_state)):
            if value not in state_ids:
                blocking.append(
                    FactIssue(
                        code="TRANSITION_DANGLING_STATE",
                        where=f"迁移 {transition.id}",
                        detail=f"{attr} 指向未声明的状态：{value}",
                    )
                )

    covered: set[str] = set()
    for scenario in artifact.scenarios:
        issue = _source_issue(f"场景 {scenario.id}", scenario.source, requirement)
        if issue:
            blocking.append(issue)
        for value in scenario.transitions:
            if value not in transition_ids:
                blocking.append(
                    FactIssue(
                        code="SCENARIO_DANGLING_TRANSITION",
                        where=f"场景 {scenario.id}",
                        detail=f"引用了未声明的迁移：{value}",
                    )
                )
            covered.add(value)
        for value in scenario.path:
            if value not in state_ids:
                blocking.append(
                    FactIssue(
                        code="SCENARIO_DANGLING_STATE",
                        where=f"场景 {scenario.id}",
                        detail=f"path 含未声明的状态：{value}",
                    )
                )

    for case in artifact.cases:
        issue = _source_issue(f"用例 {case.id}", case.source, requirement)
        if issue:
            blocking.append(issue)
        if case.scenario_id not in scenario_ids:
            blocking.append(
                FactIssue(
                    code="CASE_DANGLING_SCENARIO",
                    where=f"用例 {case.id}",
                    detail=f"scenario_id 未声明：{case.scenario_id}",
                )
            )
        for state_id in {case.pre_state} | {step.expect_state for step in case.steps}:
            if state_id not in state_ids:
                blocking.append(
                    FactIssue(
                        code="CASE_DANGLING_STATE",
                        where=f"用例 {case.id}",
                        detail=f"引用了未声明的状态：{state_id}",
                    )
                )
        boundary_values = {value for entry in case.boundary for value in entry.values}
        allowed = _numbers(case.source) | boundary_values
        for entry in case.boundary:
            allowed |= _numbers(entry.source)
        for index, step in enumerate(case.steps, start=1):
            for value in _numbers(step.action):
                if value in allowed:
                    continue
                blocking.append(
                    FactIssue(
                        code="CASE_NUMBER_UNTRACEABLE",
                        where=f"用例 {case.id} 第 {index} 步",
                        detail=f"数值「{value}」在用例 source 与边界出处里都找不到",
                    )
                )
        for entry in case.boundary:
            if not (_numbers(entry.source) & set(entry.values)):
                blocking.append(
                    FactIssue(
                        code="BOUNDARY_SOURCE_MISSING",
                        where=f"用例 {case.id} 边界「{entry.param}」",
                        detail="取值的出处里没有出现任何一个边界取值",
                    )
                )

    uncovered = transition_ids - covered
    if uncovered:
        warnings.append(
            FactIssue(
                code="TRANSITION_NOT_COVERED",
                where="场景覆盖",
                detail=f"{len(uncovered)} 条迁移没有任何场景走过：{'、'.join(sorted(uncovered))}",
            )
        )
    if not artifact.states or not artifact.cases:
        warnings.append(
            FactIssue(
                code="ARTIFACT_INCOMPLETE",
                where="产物",
                detail="状态或用例为空，预检没有可核对的对象",
            )
        )
    return FactReport(blocking=tuple(blocking), warnings=tuple(warnings))


def format_facts(report: FactReport) -> str:
    """把预检结论摊成可读文本。

    Args:
        report: 预检结论。

    Returns:
        供验收工具与任务结果共用的文本；无问题时给出「无」。
    """
    lines: list[str] = []
    lines.append(f"确定性问题：{len(report.blocking)} 条")
    for item in report.blocking:
        lines.append(f"- {item.render()}")
    if not report.blocking:
        lines.append("- 无")
    lines.append(f"告警：{len(report.warnings)} 条")
    for item in report.warnings:
        lines.append(f"- {item.render()}")
    if not report.warnings:
        lines.append("- 无")
    return "\n".join(lines)
