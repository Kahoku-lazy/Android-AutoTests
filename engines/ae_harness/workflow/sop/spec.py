"""
文件名: ➡️ spec.py 🏁
路径: ➡️ engines/ae_harness/workflow/sop/spec.py 🏁
模块功能：➡️ SOP 步骤定义与 YAML 加载 🏁
Python 调试：➡️ python -m engines.ae_harness.workflow.sop.spec 🏁
时间：➡️ 2026-11-13 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-13 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. StepSpec: 一个里程碑：名称、必须达成的结果、最大尝试次数。
2. SopSpec: 整条流程：名称、任务描述与步骤列表。
3. load_spec: 从 YAML 读出 SopSpec，缺字段时给出明确报错。
4. 步骤是流程数据，不属于 agents 的模型配置，允许在本包内直接读 YAML。
🏁
关联模块：➡️
1. engines.ae_harness.workflow.sop.runner: 消费 SopSpec 跑流程。
🏁
测试：➡️
1. 见 engines.ae_harness.workflow.sop_runner。
🏁
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

__all__ = ["SopSpec", "SopSpecError", "StepSpec", "load_spec"]


class SopSpecError(ValueError):
    """步骤文件不合法时抛出。"""


@dataclass
class StepSpec:
    """
    一个里程碑。

    Attributes:
        subject: 步骤名，出现在报告与事件里。
        description: 这一步必须达成的结果，只写终点不写路线。
        max_attempts: 被验收者驳回几次后判失败。
    """

    subject: str
    description: str
    max_attempts: int = 3


@dataclass
class SopSpec:
    """
    整条流程。

    Attributes:
        name: 流程名。
        steps: 按顺序执行的步骤。
        description: 流程用途说明。
        task: 交给第一步的任务描述。
    """

    name: str
    steps: list[StepSpec] = field(default_factory=list)
    description: str = ""
    task: str = ""


def _require_text(raw: dict[str, Any], key: str, where: str) -> str:
    """
    取一个必填的文本字段。

    Args:
        raw: 原始字典。
        key: 字段名。
        where: 出错时的位置描述。

    Returns:
        去空白后的文本。

    Raises:
        SopSpecError: 字段缺失或为空。
    """
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SopSpecError(f"{where} 缺少必填字段 {key}（需要非空字符串）")
    return value.strip()


def load_spec(path: Path) -> SopSpec:
    """
    从 YAML 读出流程定义。

    Args:
        path: YAML 文件路径。

    Returns:
        解析好的流程定义。

    Raises:
        SopSpecError: 文件不存在、不是合法 YAML、或字段不符合要求。
    """
    if not path.is_file():
        raise SopSpecError(f"步骤文件不存在: {path}")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise SopSpecError(f"步骤文件不是合法 YAML: {path}（{exc}）") from exc
    if not isinstance(raw, dict):
        raise SopSpecError(f"步骤文件顶层必须是映射: {path}")

    name = _require_text(raw, "name", "顶层")
    raw_steps = raw.get("steps")
    if not isinstance(raw_steps, list) or not raw_steps:
        raise SopSpecError("顶层 steps 必须是非空列表")

    steps: list[StepSpec] = []
    for index, item in enumerate(raw_steps, 1):
        where = f"第 {index} 步"
        if not isinstance(item, dict):
            raise SopSpecError(f"{where} 必须是映射")
        attempts = item.get("max_attempts", 3)
        if not isinstance(attempts, int) or attempts < 1:
            raise SopSpecError(f"{where} 的 max_attempts 必须是正整数")
        steps.append(
            StepSpec(
                subject=_require_text(item, "subject", where),
                description=_require_text(item, "description", where),
                max_attempts=attempts,
            )
        )

    return SopSpec(
        name=name,
        steps=steps,
        description=str(raw.get("description") or "").strip(),
        task=str(raw.get("task") or "").strip(),
    )
