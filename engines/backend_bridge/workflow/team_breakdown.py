from __future__ import annotations

import json

__all__ = ["run_team_breakdown", "validate_modules"]

_FIELDS = ("name", "boundary", "test_points", "out_of_scope")


def validate_modules(modules: list[dict]) -> tuple[bool, str]:
    if not modules:
        return False, "没有形成模块清单"
    for item in modules:
        if any(not str(item.get(field) or "").strip() for field in _FIELDS):
            return False, "模块缺少边界、测试点或不覆盖范围"
        if item.get("steps") or item.get("cases"):
            return False, "拆解结果不能包含具体用例"
    return True, ""


def run_team_breakdown(text: str) -> dict:
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
