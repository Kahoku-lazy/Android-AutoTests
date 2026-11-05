"""
文件名: ➡️ tool_case_artifact.py 🏁
路径: ➡️ engines/agents/tools/tool_case_artifact.py 🏁
模块功能：➡️ 三段式用例产物的增量交付工具：保存状态机、追加场景、追加用例、读取产物 🏁
Python 调试：➡️ python -m engines.agents.tools.tool_case_artifact 🏁
时间：➡️ 2026-11-05 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-05 🏁
类型: ➡️ 工具模块 🏁
简介说明：➡️
1. build_artifact_store_tools: 按角色组装产物工具，编写可写、验收只读。
2. build_writer_artifact_tools: 保存状态机 + 追加场景 + 追加用例 + 读取。
3. build_verifier_artifact_tools: 只读，供验收角色核对实际产物。
4. 写工具只回条数不回正文，避免把全文灌回模型上下文。
🏁
关联模块：➡️
1. engines/agents/workflow/case_artifact.py: 导入 ArtifactError, ArtifactStore
2. engines/agents/tools_config.py: 由 build_case_artifact_tools 组装进角色工具包
🏁
测试：➡️
1. tests/graybox/unit/test_case_artifact_tools.py: 单文件调试指令：python -m pytest tests/graybox/unit/test_case_artifact_tools.py -vv --tb=short
🏁
"""

from __future__ import annotations

import json

from typing import Any

from agentscope.permission import PermissionBehavior, PermissionDecision
from agentscope.tool import FunctionTool

from engines.agents.workflow.case_artifact import ArtifactError, ArtifactStore
from engines.agents.workflow.case_artifact_facts import check_artifact_facts, format_facts

__all__ = [
    "build_artifact_store_tools",
    "build_verifier_artifact_tools",
    "build_writer_artifact_tools",
]

# 平台内部存储不是外部副作用，统一放行，避免流水线停在人工授权上
_ALLOW = PermissionDecision(PermissionBehavior.ALLOW, "平台内部产物存储")


def _as_items(raw: Any, field_name: str) -> list:
    """把模型给的参数收敛成列表；允许传 JSON 字符串。

    Args:
        raw: 参数原值，可能是列表或 JSON 字符串。
        field_name: 参数名，错误消息里点名用。

    Returns:
        条目列表。

    Raises:
        ArtifactError: 传入无法解析成列表。
    """
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ArtifactError(f"产物结构不合法：{field_name} 不是合法 JSON（{exc}）") from exc
        if isinstance(parsed, list):
            return parsed
    raise ArtifactError(f"产物结构不合法：{field_name} 必须是数组")


def _summary(action: str, counts: dict[str, int]) -> str:
    """拼一条不回显正文的结果摘要。

    Args:
        action: 本次动作的可读描述。
        counts: 四类产物条数。

    Returns:
        例如「已追加 10 条场景；累计：状态 8 条、迁移 12 条、场景 6 条、用例 30 条」。
    """
    return (
        f"{action}；累计：状态 {counts['states']} 条、迁移 {counts['transitions']} 条、"
        f"场景 {counts['scenarios']} 条、用例 {counts['cases']} 条"
    )


def _save_tool(store: ArtifactStore) -> FunctionTool:
    """构造状态机写入工具；整份覆盖，方便编写角色一次性定好状态与迁移。"""

    async def save_state_machine(states: list, transitions: list) -> str:
        """整份保存需求状态机：states 与 transitions 两个数组，覆盖上一次的内容。"""
        try:
            counts = store.put_state_machine(
                _as_items(states, "states"), _as_items(transitions, "transitions")
            )
        except ArtifactError as exc:
            return f"写入失败：{exc}"
        return _summary("已保存状态机", counts)

    return FunctionTool(
        save_state_machine,
        name="save_state_machine",
        description=(
            "保存需求状态机（整份覆盖）。states 每项含 id/name/observable/observe_by/source；"
            "transitions 每项含 id/from/to/event/guard/effect/source。"
            "单批最多 20 条，非法数据不会写入。"
        ),
        is_read_only=True,
        permission=_ALLOW,
    )


def _append_scenarios_tool(store: ArtifactStore) -> FunctionTool:
    """构造场景追加工具；每批有上限，失败不落半份。"""

    async def append_scenarios(scenarios: list) -> str:
        """追加一批业务流场景，每项含 id/title/path/transitions/type/source。"""
        items = _as_items(scenarios, "scenarios")
        try:
            counts = store.append_scenarios(items)
        except ArtifactError as exc:
            return f"写入失败：{exc}"
        return _summary(f"已追加 {len(items)} 条场景", counts)

    return FunctionTool(
        append_scenarios,
        name="append_scenarios",
        description=(
            "追加业务流场景。type 取 主流程/异常/回退/中断恢复/并发；path 至少两个状态 id；"
            "transitions 必须是已声明的迁移 id。单批最多 20 条。"
        ),
        is_read_only=True,
        permission=_ALLOW,
    )


def _append_cases_tool(store: ArtifactStore) -> FunctionTool:
    """构造用例追加工具。"""

    async def append_cases(cases: list) -> str:
        """追加一批用例，每项含 id/title/scenario_id/pre_state/steps/boundary/method/priority/source。"""
        items = _as_items(cases, "cases")
        try:
            counts = store.append_cases(items)
        except ArtifactError as exc:
            return f"写入失败：{exc}"
        return _summary(f"已追加 {len(items)} 条用例", counts)

    return FunctionTool(
        append_cases,
        name="append_cases",
        description=(
            "追加测试用例。steps 为「动作 → 期望状态」数组且 expect_state 必须是已声明状态；"
            "method 必须含「场景法」；有边界参数时给 boundary（param/values/source，至少两个取值）。"
            "单批最多 20 条。"
        ),
        is_read_only=True,
        permission=_ALLOW,
    )


def _read_tool(store: ArtifactStore, *, counts_only_default: bool) -> FunctionTool:
    """构造产物读取工具；默认可只读计数，减少上下文占用。"""

    async def read_artifact(section: str = "all", counts_only: bool = False) -> str:
        """读取当前产物：section 取 all/states/transitions/scenarios/cases，counts_only 只看条数。"""
        return store.read(section, counts_only=bool(counts_only) or counts_only_default)

    return FunctionTool(
        read_artifact,
        name="read_artifact",
        description=(
            "读取本次任务已写入的三段产物。section 取 all/states/transitions/scenarios/cases；"
            "counts_only=true 时只回条数。"
        ),
        is_read_only=True,
        permission=_ALLOW,
    )


def _facts_tool(store: ArtifactStore, requirement_text: str) -> FunctionTool:
    """构造事实预检工具；需求正文由闭包带入，模型不需要也不允许改它。"""

    async def run_facts_check() -> str:
        """按需求正文核对产物：出处是否真实、引用是否完整、数值是否可追溯。"""
        report = check_artifact_facts(store.artifact(), requirement_text)
        return format_facts(report)

    return FunctionTool(
        run_facts_check,
        name="check_artifact_facts",
        description=(
            "按需求正文核对本次产物，返回确定性问题与告警。"
            "确定性问题存在时本轮不得判为通过；覆盖率类只出现在告警里。"
        ),
        is_read_only=True,
        permission=_ALLOW,
    )


def build_writer_artifact_tools(store: ArtifactStore) -> list[FunctionTool]:
    """编写角色的产物工具：可写可读。

    Args:
        store: 本次任务共享的产物存储。

    Returns:
        四个 FunctionTool：保存状态机、追加场景、追加用例、读取产物。
    """
    return [
        _save_tool(store),
        _append_scenarios_tool(store),
        _append_cases_tool(store),
        _read_tool(store, counts_only_default=False),
    ]


def build_verifier_artifact_tools(
    store: ArtifactStore,
    requirement_text: str = "",
) -> list[FunctionTool]:
    """验收角色的产物工具：只读 + 事实预检。

    Args:
        store: 本次任务共享的产物存储。
        requirement_text: 需求正文；非空时额外提供事实预检工具。

    Returns:
        读取工具，以及（给了需求正文时）事实预检工具。
    """
    tools = [_read_tool(store, counts_only_default=False)]
    if str(requirement_text or "").strip():
        tools.append(_facts_tool(store, requirement_text))
    return tools


def build_artifact_store_tools(
    store: ArtifactStore,
    *,
    read_only: bool = False,
    requirement_text: str = "",
) -> list[FunctionTool]:
    """按角色组装产物工具。

    Args:
        store: 本次任务共享的产物存储。
        read_only: 为真时只返回读取工具（验收角色）。
        requirement_text: 需求正文；验收角色用它开启事实预检。

    Returns:
        可直接挂到 Toolkit 的 FunctionTool 列表。
    """
    if read_only:
        return build_verifier_artifact_tools(store, requirement_text)
    return build_writer_artifact_tools(store)
