"""
python -m 调试路径: engines.agents.workflow.case_file

本模块的业务功能如下：
1. validate_platform_yaml: 平台提交与执行前检查 YAML，要求唯一智能体 sop。
2. load_manual_cases: 手工入口读取用例，缺少 agent 时按 sop。
"""

from __future__ import annotations

from dataclasses import dataclass

import yaml

SOP_AGENT = "sop"
LOAD_OK = "配置加载成功"
LOAD_FAIL = "加载失败"


@dataclass(frozen=True)
class CaseStep:
    action: str
    expected: str


@dataclass(frozen=True)
class CaseItem:
    agent: str
    title: str
    steps: tuple[CaseStep, ...]


def _as_case_list(data) -> list:
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return data
    return []


def parse_cases(
    data, *, require_agent: bool, fill_missing_agent: bool = False
) -> tuple[list[CaseItem], str]:
    """把 YAML 根节点收成用例。失败时返回空列表和可读原因。"""
    raw_cases = _as_case_list(data)
    if not raw_cases:
        return [], "YAML 必须是非空的用例列表，或单条用例"
    items: list[CaseItem] = []
    agents: list[str] = []
    for case in raw_cases:
        if not isinstance(case, dict):
            return [], "每条用例必须是映射"
        agent = str(case.get("agent") or "").strip()
        title = str(case.get("title") or "").strip()
        steps_raw = case.get("steps")
        if not agent and fill_missing_agent:
            agent = SOP_AGENT
        if require_agent and not agent:
            return [], "用例缺少 agent"
        if not title:
            return [], "用例缺少 title"
        if not isinstance(steps_raw, list) or not steps_raw:
            return [], f"用例「{title}」缺少 steps"
        steps: list[CaseStep] = []
        for step in steps_raw:
            if not isinstance(step, dict):
                return [], f"用例「{title}」的步骤必须是映射"
            action = str(step.get("action") or "").strip()
            expected = str(step.get("assert") or "").strip()
            if not action or not expected:
                return [], f"用例「{title}」的步骤缺少 action 或 assert"
            steps.append(CaseStep(action=action, expected=expected))
        if require_agent or fill_missing_agent:
            agents.append(agent)
        else:
            agents.append(agent or SOP_AGENT)
        items.append(CaseItem(agent=agents[-1], title=title, steps=tuple(steps)))
    enforce = require_agent or fill_missing_agent
    if enforce and len(set(agents)) != 1:
        return [], "同一份 YAML 只能指定一个智能体"
    if enforce and agents[0] != SOP_AGENT:
        return [], f"未登记的智能体: {agents[0]}"
    return items, ""


def validate_platform_yaml(text: str) -> tuple[list[CaseItem], str]:
    """检查平台 YAML 文本。成功返回用例与空原因，失败返回空列表与原因。"""
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return [], f"YAML 无法解析: {exc}"
    return parse_cases(data, require_agent=False, fill_missing_agent=True)


def load_manual_cases(text: str) -> tuple[list[CaseItem], str]:
    """手工入口读取用例。缺少 agent 时记为 sop。结构不合法时返回原因。"""
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return [], f"YAML 无法解析: {exc}"
    return parse_cases(data, require_agent=False)
