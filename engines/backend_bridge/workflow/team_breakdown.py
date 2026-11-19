"""
文件名: ➡️ team_breakdown.py 🏁
路径: ➡️ engines/backend_bridge/workflow/team_breakdown.py 🏁
模块功能: ➡️ 需求拆解结果校验：只接受模块边界与测试点 🏁
Python 调试: ➡️ python -m engines.backend_bridge.workflow.team_breakdown 🏁
时间: ➡️ 2026-11-18 🏁
作者: ➡️ kahoku 🏁
版本: ➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-18 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明: ➡️
1. validate_modules: 缺边界、测试点或不覆盖范围时整份失败。
2. run_team_breakdown: 从正文读取模块 JSON，不创建后续任务。
🏁
关联模块: ➡️
1. agentscope.pipeline.TeamPipeline: 生产运行由调用方装配，本模块只校验产物。
🏁
测试: ➡️
1. tests/engines/backend_bridge/unit/test_team_breakdown.py: 缺字段失败，合法结果不带用例
🏁
"""

from __future__ import annotations

import json

__all__ = ["run_team_breakdown", "validate_modules"]

_FIELDS = ("name", "boundary", "test_points", "out_of_scope")


def validate_modules(modules: list[dict]) -> tuple[bool, str]:
    """确认每个模块都有名称、边界、测试点和不覆盖范围，且没有用例步骤。"""
    if not modules:
        return False, "没有形成模块清单"
    for item in modules:
        if any(not str(item.get(field) or "").strip() for field in _FIELDS):
            return False, "模块缺少边界、测试点或不覆盖范围"
        if item.get("steps") or item.get("cases"):
            return False, "拆解结果不能包含具体用例"
    return True, ""


def run_team_breakdown(text: str) -> dict:
    """读取拆解正文。正文不是合法模块 JSON 时整次失败。"""
    try:
        modules = json.loads(text or "[]")
    except json.JSONDecodeError:
        modules = []
    if not isinstance(modules, list):
        modules = []
    passed, reason = validate_modules(modules)
    return {
        "status": "success" if passed else "fail",
        "passed": passed,
        "reason": reason,
        "modules": modules if passed else [],
        "module_count": len(modules) if passed else 0,
        "created_followup": False,
    }
