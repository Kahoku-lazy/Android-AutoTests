"""
文件名: ➡️ case_file.py 🏁
路径: ➡️ engines/agents/workflow/case_file.py 🏁
模块功能：➡️ 2. load_manual_cases: 手工入口读取用例，缺少 agent 时按 sop 🏁
Python 调试：➡️ python -m engines.agents.workflow.case_file 🏁
时间：➡️ 2026-10-28 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.1.0 🏁
修改时间: ➡️ 2026-11-03 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. validate_platform_yaml: 平台提交与执行前检查 YAML，要求唯一智能体 sop
2. load_manual_cases: 手工入口读取用例，缺少 agent 时按 sop
3. CaseStep / LogEvidence: 一步的结构化输入；anchor（页面锚点）与 log（日志证据）可选
4. _parse_anchor / _parse_log: 可选字段的校验，失败时给出可读原因而不抛异常
5. parse_step_hints: 把可选执行提示校验成可入库的纯字典，供平台用例库复用
🏁
关联模块：➡️
1. 暂无本地 engines/utils 依赖
🏁
测试：➡️
1. tests/graybox/unit/test_case_step_fields.py: 步骤结构字段的解析与拒绝
2. tests/graybox/unit/test_platform_case_title.py: 平台 SOP 指定用例
3. tests/graybox/unit/test_case_yaml_import.py: parse_step_hints 的合法/非法两路
🏁
"""

from __future__ import annotations

import re

from collections.abc import Mapping
from dataclasses import dataclass

import yaml

SOP_AGENT = "sop"
LOAD_OK = "配置加载成功"
LOAD_FAIL = "加载失败"

ANCHOR_KEYS: tuple[str, ...] = ("page", "entry", "target")
"""`anchor` 允许的键：页面、入口、目标元素。"""

ANCHOR_VALUE_MAX = 120
"""`anchor` 每个值的最大字符数。"""

KEYWORDS_MAX = 6
"""一步最多带几个日志关键词。"""

_KEYWORD_PATTERN = re.compile(r"^[A-Za-z0-9_.\-]+$")


@dataclass(frozen=True)
class LogEvidence:
    """
    一步的日志证据：型号、端口与关键词。

    同一关键词出现多次表示「这一步要命中它 N 次」（例如开灯 + 关灯两个事件）。

    Attributes:
        sku: 型号，如 H6810。
        port: 日志端口，如 7005。
        keywords: 日志关键词原文，按检查顺序排列；重复项表示需要命中多次。
    """

    sku: str
    port: int
    keywords: tuple[str, ...]

    @property
    def keyword(self) -> str:
        """第一个关键词，兼容只带一个关键词的旧调用。

        Returns:
            关键词列表的第一项。
        """
        return self.keywords[0]


@dataclass(frozen=True)
class CaseStep:
    """
    用例一步：动作、期望，以及可选的页面锚点与日志证据。

    Attributes:
        action: 执行角色这一步要做的动作。
        expected: 验收角色这一步要核对的结果。
        anchor: 可选的页面锚点（page / entry / target），只给执行角色。
        log: 可选的日志证据，只给验收角色。
    """

    action: str
    expected: str
    anchor: Mapping[str, str] | None = None
    log: LogEvidence | None = None


@dataclass(frozen=True)
class CaseItem:
    """一条用例：含步骤列表等结构化字段。"""

    agent: str
    title: str
    steps: tuple[CaseStep, ...]


def _as_case_list(data) -> list:
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return data
    return []


def _parse_anchor(raw: object, *, where: str) -> tuple[Mapping[str, str] | None, str]:
    """校验并收敛一步的页面锚点。

    Args:
        raw: YAML 里的 `anchor` 节点。
        where: 报错定位用的路径。

    Returns:
        (锚点映射或 None, 失败原因)；成功时原因为空串。

    Raises:
        无：校验失败一律通过返回值报出，不打断调用方。
    """
    if raw is None:
        return None, ""
    if not isinstance(raw, dict):
        return None, f"{where} 的 anchor 必须是映射"
    anchor: dict[str, str] = {}
    for key, value in raw.items():
        name = str(key).strip()
        if name not in ANCHOR_KEYS:
            return None, (f"{where} 的 anchor 含未知键 {name!r}；可选：{' / '.join(ANCHOR_KEYS)}")
        text = str(value or "").strip()
        if not text:
            continue
        if len(text) > ANCHOR_VALUE_MAX:
            return None, f"{where} 的 anchor.{name} 超过 {ANCHOR_VALUE_MAX} 字"
        anchor[name] = text
    return (anchor or None), ""


def _parse_log(raw: object, *, where: str) -> tuple[LogEvidence | None, str]:
    """校验并收敛一步的日志证据。

    Args:
        raw: YAML 里的 `log` 节点。
        where: 报错定位用的路径。

    Returns:
        (日志证据或 None, 失败原因)；成功时原因为空串。

    Raises:
        无：校验失败一律通过返回值报出，不打断调用方。
    """
    if raw is None:
        return None, ""
    if not isinstance(raw, dict):
        return None, f"{where} 的 log 必须是映射"
    sku = str(raw.get("sku") or "").strip()
    if not sku:
        return None, f"{where} 的 log.sku 缺失"
    try:
        port = int(raw.get("port"))
    except (TypeError, ValueError):
        return None, f"{where} 的 log.port 必须是正整数"
    if port <= 0:
        return None, f"{where} 的 log.port 必须是正整数"
    keywords, reason = _parse_keywords(raw, where=where)
    if reason:
        return None, reason
    return LogEvidence(sku=sku, port=port, keywords=keywords), ""


def _parse_keywords(raw: dict, *, where: str) -> tuple[tuple[str, ...], str]:
    """校验并收敛一步的日志关键词：单个 `keyword` 或 `keywords` 列表。

    `keywords` 里同一个关键词出现两次，表示这一步要命中它两次（两次独立事件）。

    Args:
        raw: YAML 里的 `log` 节点。
        where: 报错定位用的路径。

    Returns:
        (关键词元组, 失败原因)；成功时原因为空串。

    Raises:
        无：校验失败一律通过返回值报出，不打断调用方。
    """
    single = raw.get("keyword")
    listed = raw.get("keywords")
    if single is not None and listed is not None:
        return (), f"{where} 的 log.keyword 与 log.keywords 只能给一个"
    if single is not None:
        values: list = [single]
    elif listed is not None:
        if not isinstance(listed, list):
            return (), f"{where} 的 log.keywords 必须是列表"
        values = listed
    else:
        return (), f"{where} 的 log.keyword 缺失"
    keywords: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text:
            return (), f"{where} 的 log.keyword 不能为空"
        if not _KEYWORD_PATTERN.match(text):
            return (), f"{where} 的日志关键词 {text!r} 只能含字母、数字、下划线、点和短横"
        keywords.append(text)
    if not keywords:
        return (), f"{where} 的 log.keyword 不能为空"
    if len(keywords) > KEYWORDS_MAX:
        return (), f"{where} 的日志关键词最多 {KEYWORDS_MAX} 个，当前 {len(keywords)} 个"
    return tuple(keywords), ""


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
        for index, step in enumerate(steps_raw, start=1):
            if not isinstance(step, dict):
                return [], f"用例「{title}」的步骤必须是映射"
            where = f"用例「{title}」第 {index} 步"
            action = str(step.get("action") or "").strip()
            expected = str(step.get("assert") or "").strip()
            if not action or not expected:
                return [], f"用例「{title}」的步骤缺少 action 或 assert"
            anchor, reason = _parse_anchor(step.get("anchor"), where=where)
            if reason:
                return [], reason
            log_evidence, reason = _parse_log(step.get("log"), where=where)
            if reason:
                return [], reason
            steps.append(
                CaseStep(action=action, expected=expected, anchor=anchor, log=log_evidence)
            )
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


def parse_step_hints(
    anchor: object, log: object, *, where: str = "步骤"
) -> tuple[dict[str, str], dict[str, object], str]:
    """
    校验一步的可选执行提示，返回可入库的纯字典。

    Args:
        anchor: YAML 或接口里的 `anchor` 节点；None 表示该步没有页面锚点。
        log: YAML 或接口里的 `log` 节点；None 表示该步没有日志证据。
        where: 报错定位用的路径，例如「用例「甲」第 2 步」。

    Returns:
        (页面锚点字典, 日志证据字典, 失败原因)。成功时原因为空串，缺失项为空字典；
        日志证据固定为 `{sku, port, keywords}`，单关键词也收敛成列表。

    Raises:
        无：校验失败一律通过返回值报出，不打断调用方。
    """
    anchor_map, reason = _parse_anchor(anchor, where=where)
    if reason:
        return {}, {}, reason
    evidence, reason = _parse_log(log, where=where)
    if reason:
        return {}, {}, reason
    payload: dict[str, object] = {}
    if evidence is not None:
        payload = {
            "sku": evidence.sku,
            "port": evidence.port,
            "keywords": list(evidence.keywords),
        }
    return dict(anchor_map or {}), payload, ""


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
