"""
文件名: ➡️ case_artifact.py 🏁
路径: ➡️ engines/agents/workflow/case_artifact.py 🏁
模块功能：➡️ 三段式用例产物的数据契约与任务级存储：状态机 → 业务流场景 → 用例 🏁
Python 调试：➡️ python -m engines.agents.workflow.case_artifact 🏁
时间：➡️ 2026-11-05 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-05 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. ArtifactState / ArtifactTransition: 需求状态机的状态与迁移，各自必须带需求原文片段。
2. ArtifactScenario: 状态机上的一条业务流路径，类型区分主流程 / 异常 / 回退 / 中断恢复 / 并发。
3. ArtifactCase / ArtifactStep / ArtifactBoundary: 由场景派生的用例、动作到期望状态的步骤与边界取值。
4. ArtifactStore: 一次任务内的增量存储，分批写入、批次原子、单批有上限。
🏁
关联模块：➡️
1. engines/agents/tools/tool_case_artifact.py: 把存储暴露成模型可调的增量工具
2. engines/agents/workflow/case_artifact_facts.py: 对产物做事实预检
3. engines/agents/workflow/case_artifact_render.py: 把产物渲染成 Markdown 与 Mermaid
🏁
测试：➡️
1. tests/graybox/unit/test_case_artifact.py: 单文件调试指令：python -m pytest tests/graybox/unit/test_case_artifact.py -vv --tb=short
🏁
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

__all__ = [
    "ARTIFACT_ERROR",
    "MAX_BATCH",
    "MAX_SOURCE",
    "MAX_STEP",
    "MAX_TITLE",
    "SCENARIO_TYPES",
    "Artifact",
    "ArtifactBoundary",
    "ArtifactCase",
    "ArtifactError",
    "ArtifactScenario",
    "ArtifactState",
    "ArtifactStep",
    "ArtifactStore",
    "ArtifactTransition",
]

# 单批写入上限：一批就是一次模型工具调用的产出，过大等于把长文档换个形状
MAX_BATCH = 20
# 以下长度上限只防「整段抱怨写进字段」，不是内容规范
MAX_TITLE = 200
MAX_SOURCE = 500
MAX_STEP = 200
# 产物结构不合法时的统一错误前缀，便于工具层原样回给模型
ARTIFACT_ERROR = "产物结构不合法："
# 场景类型只允许这五种，避免自由发挥出无法归类的分支
SCENARIO_TYPES = ("主流程", "异常", "回退", "中断恢复", "并发")


class ArtifactError(ValueError):
    """产物结构不合法。消息面向模型，必须能直接照着改。"""


def _text(raw: Any, field_name: str, limit: int) -> str:
    """取一个必填文本字段并做长度校验。

    Args:
        raw: 原始值。
        field_name: 字段名，错误消息里点名用。
        limit: 允许的最大字符数。

    Returns:
        去掉首尾空白的文本。

    Raises:
        ArtifactError: 字段为空或超长。
    """
    text = str(raw or "").strip()
    if not text:
        raise ArtifactError(f"{ARTIFACT_ERROR}{field_name} 不能为空")
    if len(text) > limit:
        raise ArtifactError(f"{ARTIFACT_ERROR}{field_name} 超过 {limit} 字符（当前 {len(text)}）")
    return text


def _optional_text(raw: Any, limit: int) -> str:
    """取一个可选文本字段；超长时截断而不是报错。"""
    return str(raw or "").strip()[:limit]


def _mapping(raw: Any, where: str) -> dict:
    """要求入参是映射。

    Args:
        raw: 原始值。
        where: 位置描述，例如「第 3 条用例」。

    Returns:
        原字典。

    Raises:
        ArtifactError: 不是映射。
    """
    if not isinstance(raw, dict):
        raise ArtifactError(f"{ARTIFACT_ERROR}{where} 必须是对象")
    return raw


def _list(raw: Any, where: str) -> list:
    """要求入参是列表。

    Args:
        raw: 原始值。
        where: 位置描述。

    Returns:
        原列表。

    Raises:
        ArtifactError: 不是列表。
    """
    if not isinstance(raw, list):
        raise ArtifactError(f"{ARTIFACT_ERROR}{where} 必须是数组")
    return raw


@dataclass(frozen=True)
class ArtifactState:
    """
    需求状态机里的一个状态。

    Attributes:
        id: 状态标识，全文唯一，例如 S1 或「详情页」。
        name: 状态名，给人看。
        observable: 是否能被截图或日志观察到。
        observe_by: 观察手段；不可观察时必须写明原因。
        source: 需求原文片段。
        uncertain: 需求没写明、需要人工确认的标记。
    """

    id: str
    name: str
    observable: bool
    observe_by: str
    source: str
    uncertain: bool = False

    @classmethod
    def parse(cls, raw: Any, where: str) -> "ArtifactState":
        """从字典解析一个状态。

        Args:
            raw: 模型给的字典。
            where: 位置描述。

        Returns:
            解析后的状态。

        Raises:
            ArtifactError: 必填缺失或类型不对。
        """
        item = _mapping(raw, where)
        observable = item.get("observable")
        if not isinstance(observable, bool):
            raise ArtifactError(f"{ARTIFACT_ERROR}{where} 的 observable 必须是布尔值")
        return cls(
            id=_text(item.get("id"), f"{where} 的 id", 64),
            name=_text(item.get("name"), f"{where} 的 name", MAX_TITLE),
            observable=observable,
            observe_by=_text(item.get("observe_by"), f"{where} 的 observe_by", MAX_SOURCE),
            source=_text(item.get("source"), f"{where} 的 source", MAX_SOURCE),
            uncertain=bool(item.get("uncertain")),
        )

    def payload(self) -> dict:
        """还原成可 JSON 序列化的字典。"""
        return {
            "id": self.id,
            "name": self.name,
            "observable": self.observable,
            "observe_by": self.observe_by,
            "source": self.source,
            "uncertain": self.uncertain,
        }


@dataclass(frozen=True)
class ArtifactTransition:
    """
    状态机里的一条迁移。

    Attributes:
        id: 迁移标识，全文唯一。
        from_state: 起状态 id。
        to_state: 目标状态 id。
        event: 触发动作。
        guard: 触发条件，可空。
        effect: 副作用，可空。
        source: 需求原文片段。
    """

    id: str
    from_state: str
    to_state: str
    event: str
    guard: str
    effect: str
    source: str

    @classmethod
    def parse(cls, raw: Any, where: str) -> "ArtifactTransition":
        """从字典解析一条迁移。

        Args:
            raw: 模型给的字典。
            where: 位置描述。

        Returns:
            解析后的迁移。

        Raises:
            ArtifactError: 必填缺失。
        """
        item = _mapping(raw, where)
        return cls(
            id=_text(item.get("id"), f"{where} 的 id", 64),
            from_state=_text(item.get("from"), f"{where} 的 from", 64),
            to_state=_text(item.get("to"), f"{where} 的 to", 64),
            event=_text(item.get("event"), f"{where} 的 event", MAX_STEP),
            guard=_optional_text(item.get("guard"), MAX_STEP),
            effect=_optional_text(item.get("effect"), MAX_STEP),
            source=_text(item.get("source"), f"{where} 的 source", MAX_SOURCE),
        )

    def payload(self) -> dict:
        """还原成可 JSON 序列化的字典。"""
        return {
            "id": self.id,
            "from": self.from_state,
            "to": self.to_state,
            "event": self.event,
            "guard": self.guard,
            "effect": self.effect,
            "source": self.source,
        }


@dataclass(frozen=True)
class ArtifactScenario:
    """
    状态机上的一条业务流路径。

    Attributes:
        id: 场景标识，全文唯一。
        title: 场景标题。
        path: 状态序列，长度至少 2。
        transitions: 走过的迁移 id 列表。
        type: 主流程 / 异常 / 回退 / 中断恢复 / 并发。
        source: 需求原文片段。
    """

    id: str
    title: str
    path: tuple[str, ...]
    transitions: tuple[str, ...]
    type: str
    source: str

    @classmethod
    def parse(cls, raw: Any, where: str) -> "ArtifactScenario":
        """从字典解析一个场景。

        Args:
            raw: 模型给的字典。
            where: 位置描述。

        Returns:
            解析后的场景。

        Raises:
            ArtifactError: 路径过短或类型非法。
        """
        item = _mapping(raw, where)
        path = tuple(
            str(value or "").strip() for value in _list(item.get("path"), f"{where} 的 path")
        )
        if len(path) < 2 or any(not value for value in path):
            raise ArtifactError(f"{ARTIFACT_ERROR}{where} 的 path 至少要有两个状态 id")
        kind = str(item.get("type") or "").strip()
        if kind not in SCENARIO_TYPES:
            raise ArtifactError(
                f"{ARTIFACT_ERROR}{where} 的 type 必须是 {' / '.join(SCENARIO_TYPES)}"
            )
        transitions = item.get("transitions")
        if not isinstance(transitions, list) or not transitions:
            raise ArtifactError(f"{ARTIFACT_ERROR}{where} 的 transitions 不能为空")
        return cls(
            id=_text(item.get("id"), f"{where} 的 id", 64),
            title=_text(item.get("title"), f"{where} 的 title", MAX_TITLE),
            path=path,
            transitions=tuple(str(value or "").strip() for value in transitions),
            type=kind,
            source=_text(item.get("source"), f"{where} 的 source", MAX_SOURCE),
        )

    def payload(self) -> dict:
        """还原成可 JSON 序列化的字典。"""
        return {
            "id": self.id,
            "title": self.title,
            "path": list(self.path),
            "transitions": list(self.transitions),
            "type": self.type,
            "source": self.source,
        }


@dataclass(frozen=True)
class ArtifactBoundary:
    """
    用例覆盖的一处边界取值。

    Attributes:
        param: 参数名，例如「名称长度」。
        values: 取值列表，必须同时含边界内与边界外。
        source: 需求原文片段。
    """

    param: str
    values: tuple[str, ...]
    source: str

    @classmethod
    def parse(cls, raw: Any, where: str) -> "ArtifactBoundary":
        """从字典解析一处边界。

        Args:
            raw: 模型给的字典。
            where: 位置描述。

        Returns:
            解析后的边界项。

        Raises:
            ArtifactError: 取值少于两个。
        """
        item = _mapping(raw, where)
        raw_values = _list(item.get("values"), f"{where} 的 values")
        values = tuple(str(value).strip() for value in raw_values if str(value).strip())
        if len(values) < 2:
            raise ArtifactError(f"{ARTIFACT_ERROR}{where} 的 values 至少要有边界内与边界外两个取值")
        return cls(
            param=_text(item.get("param"), f"{where} 的 param", MAX_STEP),
            values=values,
            source=_text(item.get("source"), f"{where} 的 source", MAX_SOURCE),
        )

    def payload(self) -> dict:
        """还原成可 JSON 序列化的字典。"""
        return {"param": self.param, "values": list(self.values), "source": self.source}


@dataclass(frozen=True)
class ArtifactStep:
    """
    用例里的一步：动作与期望状态。

    Attributes:
        action: 动作描述。
        expect_state: 期望落在的状态 id。
        note: 可选的备注。
    """

    action: str
    expect_state: str
    note: str

    @classmethod
    def parse(cls, raw: Any, where: str) -> "ArtifactStep":
        """从字典解析一步。

        Args:
            raw: 模型给的字典。
            where: 位置描述。

        Returns:
            解析后的步骤。

        Raises:
            ArtifactError: 必填缺失。
        """
        item = _mapping(raw, where)
        return cls(
            action=_text(item.get("action"), f"{where} 的 action", MAX_STEP),
            expect_state=_text(item.get("expect_state"), f"{where} 的 expect_state", 64),
            note=_optional_text(item.get("note"), MAX_STEP),
        )

    def payload(self) -> dict:
        """还原成可 JSON 序列化的字典。"""
        return {"action": self.action, "expect_state": self.expect_state, "note": self.note}


@dataclass(frozen=True)
class ArtifactCase:
    """
    一条用例。

    Attributes:
        id: 用例编号，全文唯一。
        title: 用例标题。
        scenario_id: 派生自哪个场景。
        pre_state: 起始状态 id。
        steps: 动作到期望状态的步骤序列。
        boundary: 边界取值；无边界参数时为空。
        method: 设计方法，至少含「场景法」。
        priority: P0 / P1 / P2，只作排序用途，不设比例门禁。
        source: 需求原文片段。
        uncertain: 需要人工确认的标记。
    """

    id: str
    title: str
    scenario_id: str
    pre_state: str
    steps: tuple[ArtifactStep, ...]
    boundary: tuple[ArtifactBoundary, ...]
    method: tuple[str, ...]
    priority: str
    source: str
    uncertain: bool = False

    @classmethod
    def parse(cls, raw: Any, where: str) -> "ArtifactCase":
        """从字典解析一条用例。

        Args:
            raw: 模型给的字典。
            where: 位置描述。

        Returns:
            解析后的用例。

        Raises:
            ArtifactError: 步骤为空或方法缺「场景法」。
        """
        item = _mapping(raw, where)
        steps = tuple(
            ArtifactStep.parse(step, f"{where} 的第 {index} 步")
            for index, step in enumerate(_list(item.get("steps"), f"{where} 的 steps"), start=1)
        )
        if not steps:
            raise ArtifactError(f"{ARTIFACT_ERROR}{where} 的 steps 不能为空")
        boundary_raw = item.get("boundary") or []
        boundary = tuple(
            ArtifactBoundary.parse(entry, f"{where} 的第 {index} 处边界")
            for index, entry in enumerate(_list(boundary_raw, f"{where} 的 boundary"), start=1)
        )
        methods = tuple(
            str(value).strip()
            for value in _list(item.get("method") or ["场景法"], f"{where} 的 method")
            if str(value).strip()
        )
        if "场景法" not in methods:
            raise ArtifactError(f"{ARTIFACT_ERROR}{where} 的 method 必须含「场景法」")
        priority = str(item.get("priority") or "P1").strip().upper()
        if priority not in ("P0", "P1", "P2"):
            raise ArtifactError(f"{ARTIFACT_ERROR}{where} 的 priority 只能是 P0 / P1 / P2")
        return cls(
            id=_text(item.get("id"), f"{where} 的 id", 64),
            title=_text(item.get("title"), f"{where} 的 title", MAX_TITLE),
            scenario_id=_text(item.get("scenario_id"), f"{where} 的 scenario_id", 64),
            pre_state=_text(item.get("pre_state"), f"{where} 的 pre_state", 64),
            steps=steps,
            boundary=boundary,
            method=methods,
            priority=priority,
            source=_text(item.get("source"), f"{where} 的 source", MAX_SOURCE),
            uncertain=bool(item.get("uncertain")),
        )

    def payload(self) -> dict:
        """还原成可 JSON 序列化的字典。"""
        return {
            "id": self.id,
            "title": self.title,
            "scenario_id": self.scenario_id,
            "pre_state": self.pre_state,
            "steps": [step.payload() for step in self.steps],
            "boundary": [entry.payload() for entry in self.boundary],
            "method": list(self.method),
            "priority": self.priority,
            "source": self.source,
            "uncertain": self.uncertain,
        }


@dataclass(frozen=True)
class Artifact:
    """
    一次任务的三段产物。

    Attributes:
        states: 状态机的状态。
        transitions: 状态机的迁移。
        scenarios: 业务流场景。
        cases: 用例。
        diagram: 由产物渲染出的 Mermaid 状态图。
        report: 编写角色的结构化摘要。
    """

    states: tuple[ArtifactState, ...] = ()
    transitions: tuple[ArtifactTransition, ...] = ()
    scenarios: tuple[ArtifactScenario, ...] = ()
    cases: tuple[ArtifactCase, ...] = ()
    diagram: str = ""
    report: str = ""

    @property
    def counts(self) -> dict[str, int]:
        """四类产物的条数。"""
        return {
            "states": len(self.states),
            "transitions": len(self.transitions),
            "scenarios": len(self.scenarios),
            "cases": len(self.cases),
        }

    def payload(self) -> dict:
        """还原成可 JSON 序列化的字典。"""
        return {
            "states": [item.payload() for item in self.states],
            "transitions": [item.payload() for item in self.transitions],
            "scenarios": [item.payload() for item in self.scenarios],
            "cases": [item.payload() for item in self.cases],
            "diagram": self.diagram,
            "report": self.report,
            "counts": self.counts,
        }


def _parse_batch(parser, raw_items: Any, where: str) -> list:
    """解析一批产物条目并把批次上限与重复 id 一并校验。

    Args:
        parser: 单条解析函数，接收 (raw, where)。
        raw_items: 模型给的数组。
        where: 批次描述。

    Returns:
        解析后的条目列表。

    Raises:
        ArtifactError: 条数为空、超过上限，或同批出现重复 id。
    """
    items = _list(raw_items, where)
    if not items:
        raise ArtifactError(f"{ARTIFACT_ERROR}{where} 不能为空")
    if len(items) > MAX_BATCH:
        raise ArtifactError(
            f"{ARTIFACT_ERROR}{where} 一次最多 {MAX_BATCH} 条（当前 {len(items)}），请拆成小批"
        )
    parsed = [parser(item, f"{where} 第 {index} 条") for index, item in enumerate(items, start=1)]
    seen: set[str] = set()
    for item in parsed:
        if item.id in seen:
            raise ArtifactError(f"{ARTIFACT_ERROR}{where} 内出现重复 id：{item.id}")
        seen.add(item.id)
    return parsed


@dataclass
class ArtifactStore:
    """
    一次任务内的三段产物存储。

    Attributes:
        states: 已写入的状态。
        transitions: 已写入的迁移。
        scenarios: 已追加的场景。
        cases: 已追加的用例。
        report: 编写角色的结构化摘要。
    """

    states: list[ArtifactState] = field(default_factory=list)
    transitions: list[ArtifactTransition] = field(default_factory=list)
    scenarios: list[ArtifactScenario] = field(default_factory=list)
    cases: list[ArtifactCase] = field(default_factory=list)
    report: str = ""

    def put_state_machine(self, states: Any, transitions: Any) -> dict[str, int]:
        """整份写入（覆盖）状态机。

        Args:
            states: 状态数组。
            transitions: 迁移数组。

        Returns:
            写入后的四类条数。

        Raises:
            ArtifactError: 结构不合法或 id 重复。
        """
        parsed_states = _parse_batch(ArtifactState.parse, states, "states")
        parsed_transitions = _parse_batch(ArtifactTransition.parse, transitions, "transitions")
        state_ids = {item.id for item in parsed_states}
        for item in parsed_transitions:
            for attr, value in (("from", item.from_state), ("to", item.to_state)):
                if value not in state_ids:
                    raise ArtifactError(
                        f"{ARTIFACT_ERROR}迁移 {item.id} 的 {attr} 指向未声明的状态：{value}"
                    )
        self.states = list(parsed_states)
        self.transitions = list(parsed_transitions)
        return self.counts()

    def append_scenarios(self, scenarios: Any) -> dict[str, int]:
        """写入一批场景：新 id 追加，已有 id 原位覆盖。

        Args:
            scenarios: 场景数组。

        Returns:
            写入后的四类条数。

        Raises:
            ArtifactError: 结构不合法，或迁移/状态 id 未声明。
        """
        parsed = _parse_batch(ArtifactScenario.parse, scenarios, "scenarios")
        transition_ids = {item.id for item in self.transitions}
        state_ids = {item.id for item in self.states}
        for item in parsed:
            missing = [value for value in item.transitions if value not in transition_ids]
            if missing:
                raise ArtifactError(
                    f"{ARTIFACT_ERROR}场景 {item.id} 引用了未声明的迁移：{'、'.join(missing)}"
                )
            unknown = [value for value in item.path if value not in state_ids]
            if unknown:
                raise ArtifactError(
                    f"{ARTIFACT_ERROR}场景 {item.id} 的 path 含未声明的状态：{'、'.join(unknown)}"
                )
        self._upsert(self.scenarios, parsed)
        return self.counts()

    def append_cases(self, cases: Any) -> dict[str, int]:
        """追加一批用例。

        Args:
            cases: 用例数组。

        Returns:
            追写后的四类条数。

        Raises:
            ArtifactError: 结构不合法、id 重复，或引用的场景/状态未声明。
        """
        parsed = _parse_batch(ArtifactCase.parse, cases, "cases")
        scenario_ids = {item.id for item in self.scenarios}
        state_ids = {item.id for item in self.states}
        for item in parsed:
            if item.scenario_id not in scenario_ids:
                raise ArtifactError(
                    f"{ARTIFACT_ERROR}用例 {item.id} 的 scenario_id 未声明：{item.scenario_id}"
                )
            unknown = [item.pre_state] + [step.expect_state for step in item.steps]
            missing = [value for value in unknown if value not in state_ids]
            if missing:
                raise ArtifactError(
                    f"{ARTIFACT_ERROR}用例 {item.id} 引用了未声明的状态：{'、'.join(missing)}"
                )
        self._upsert(self.cases, parsed)
        return self.counts()

    @staticmethod
    def _upsert(target: list, parsed: list) -> None:
        """按 id 原位覆盖，新 id 追加；保持原有顺序。

        Args:
            target: 目标列表（场景或用例）。
            parsed: 本批解析结果。
        """
        position = {item.id: index for index, item in enumerate(target)}
        for item in parsed:
            if item.id in position:
                target[position[item.id]] = item
            else:
                position[item.id] = len(target)
                target.append(item)

    def counts(self) -> dict[str, int]:
        """四类产物的条数。"""
        return {
            "states": len(self.states),
            "transitions": len(self.transitions),
            "scenarios": len(self.scenarios),
            "cases": len(self.cases),
        }

    def artifact(self, *, diagram: str = "") -> Artifact:
        """打包成不可变产物。

        Args:
            diagram: 由渲染器生成的 Mermaid 文本。

        Returns:
            三段产物。
        """
        return Artifact(
            states=tuple(self.states),
            transitions=tuple(self.transitions),
            scenarios=tuple(self.scenarios),
            cases=tuple(self.cases),
            diagram=diagram,
            report=self.report,
        )

    def read(self, section: str = "all", *, counts_only: bool = True) -> str:
        """读产物；默认只回计数，避免把全文灌回上下文。

        Args:
            section: `all` / `states` / `transitions` / `scenarios` / `cases`。
            counts_only: 为真时只回条数。

        Returns:
            可读文本；`counts_only` 时是计数摘要，否则是 JSON 原文。
        """
        counts = self.counts()
        if counts_only:
            return (
                f"状态 {counts['states']} 条、迁移 {counts['transitions']} 条、"
                f"场景 {counts['scenarios']} 条、用例 {counts['cases']} 条"
            )
        chosen = section.strip().lower() or "all"
        mapping = {
            "states": [item.payload() for item in self.states],
            "transitions": [item.payload() for item in self.transitions],
            "scenarios": [item.payload() for item in self.scenarios],
            "cases": [item.payload() for item in self.cases],
        }
        if chosen != "all" and chosen not in mapping:
            return f"未知分节：{chosen}；可选 all / states / transitions / scenarios / cases"
        payload = mapping if chosen == "all" else {chosen: mapping[chosen]}
        return str(payload)
