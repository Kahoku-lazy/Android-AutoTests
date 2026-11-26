from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

__all__ = ["SopSpec", "SopSpecError", "StepSpec", "load_spec"]


class SopSpecError(ValueError):
    pass


@dataclass
class StepSpec:
    subject: str
    description: str
    max_attempts: int = 3


@dataclass
class SopSpec:
    name: str
    steps: list[StepSpec] = field(default_factory=list)
    description: str = ""
    task: str = ""


def _require_text(raw: dict[str, Any], key: str, where: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SopSpecError(f"{where} 缺少必填字段 {key}（需要非空字符串）")
    return value.strip()


def load_spec(path: Path) -> SopSpec:
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
