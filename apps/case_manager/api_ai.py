"""case-manager AI 工具数据出口 — 结构化 digest + 校验写入.

AI 工具（ai_assistant.tool_registry）只允许 import 本 App 的 ``api.py``，
``api.py`` 从本模块再导出。步骤白名单与语义以 ``models/step_types.py``
的 ``STEP_TYPE_META`` 为准（全平台唯一权威注册表，旧名/废弃类型拒绝）。

职责：
  - ``get_case_digest``：跨四类型读回结构化用例（含解析后的 steps）
  - ``save_ai_definition``：AI 写用例入口 — 写侧校验后经各类型 save_* 落库，
    UI 步骤写 ``steps_json``（执行器消费 steps_data）、Web 写 ``steps_json``
  - ``validate_steps``：步骤类型/平台/必填字段校验
"""

from __future__ import annotations

import json

from typing import Any

from models.step_types import STEP_TYPE_META

from .api_lock import find_case_across_types

__all__ = ["get_case_digest", "save_ai_definition", "validate_steps"]

# case_type → 允许的步骤 target（common 通用 + 平台专属）
_TARGET_WHITELIST = {
    "ui_automation": ("common", "android"),
    "web_automation": ("common", "web"),
    "api_testing": ("common", "api"),
}

# 步骤类型 → 必填非空字段（未列出的类型无必填字段要求）
_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    # ── Android 元素操作 ──
    "click": ("xpath",),
    "long_click": ("xpath",),
    "wait": ("xpath",),
    "wait_disappear": ("xpath",),
    "verify_text": ("xpath", "expected_text"),
    "adb_poll_text": ("xpath", "expected_text"),
    "adb_wait_toast": ("expected_text",),
    "adb_perf_element_time": ("xpath",),
    "adb_if_appear": ("xpath",),
    "adb_if_disappear": ("xpath",),
    "adb_loop_elements": ("xpath",),
    "adb_loop_n": ("index",),
    # ── Android 应用控制 ──
    # adb_start_app / adb_kill_app 的 xpath 承载"包名"，允许为空——
    # 执行器（executors/ui/executor.py）在空值时回退到用例 package_name。
    # ── Web ──
    "web_navigate": ("url",),
    "web_click": ("selector",),
    "web_fill": ("selector",),
    "web_type": ("selector",),
    "web_assert": ("expected_text",),
}

# 步骤类型 → 至少一个非空字段（任一满足即可）
_ANY_OF_FIELDS: dict[str, tuple[str, ...]] = {
    "web_wait": ("selector", "index"),
}

_MAX_NESTING = 10


def _is_blank(val: Any) -> bool:
    """None / 空串 / 空白串 / 空容器视为空。"""
    if val is None:
        return True
    if isinstance(val, str):
        return not val.strip()
    if isinstance(val, (list, dict)):
        return not val
    return False


def _iso(value: Any) -> str:
    if value is None:
        return ""
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _parse_steps(raw: Any) -> list[dict]:
    """steps_json（JSON 字符串）→ 步骤 dict 列表（原样保留，仅滤非对象项）。"""
    if isinstance(raw, str):
        try:
            raw = json.loads(raw) if raw else []
        except json.JSONDecodeError:
            return []
    if not isinstance(raw, list):
        return []
    return [s for s in raw if isinstance(s, dict)]


def validate_steps(case_type: str, steps: Any) -> tuple[bool, str]:
    """写侧校验：非空、类型在白名单且与平台匹配、必填字段齐全、子步骤递归。

    返回 (ok, error_message)。storage / api_testing 不走本校验
    （storage 数据型不可执行；api 经 save_api_test_case 的 jsonschema 校验）。
    """
    if case_type not in ("ui_automation", "web_automation"):
        return True, ""
    allowed = _TARGET_WHITELIST.get(case_type, ("common",))
    return _validate_steps_impl(steps, allowed, depth=0)


def _validate_steps_impl(steps: Any, allowed: tuple[str, ...], depth: int) -> tuple[bool, str]:
    if not isinstance(steps, list) or not steps:
        return False, "steps 不能为空（至少 1 步）"
    for i, s in enumerate(steps):
        label = f"第 {i + 1} 步"
        if not isinstance(s, dict):
            return False, f"{label}不是对象"
        stype = str(s.get("type", "") or "").strip()
        meta = STEP_TYPE_META.get(stype)
        if meta is None:
            return False, f"{label}步骤类型无效: {stype or '(空)'}"
        if meta.get("target") not in allowed:
            return False, f"{label}步骤类型 {stype} 不适用于 {'/'.join(allowed)}"
        for field in _REQUIRED_FIELDS.get(stype, ()):
            if _is_blank(s.get(field)):
                return False, f"{label} [{stype}] 缺少必填字段: {field}"
        any_of = _ANY_OF_FIELDS.get(stype)
        if any_of and all(_is_blank(s.get(f)) for f in any_of):
            return False, f"{label} [{stype}] 至少需要 {' 或 '.join(any_of)} 之一"
        if stype == "adb_loop_n":
            idx = s.get("index")
            if isinstance(idx, bool) or not isinstance(idx, int) or idx < 1:
                return False, f"{label} [adb_loop_n] 的 index 必须是 ≥1 的整数"
        children = s.get("children")
        if isinstance(children, list) and children:
            if depth >= _MAX_NESTING:
                return False, f"{label} 子步骤嵌套超过 {_MAX_NESTING} 层"
            ok_child, err_child = _validate_steps_impl(children, allowed, depth + 1)
            if not ok_child:
                return False, f"{label} 子步骤错误: {err_child}"
    return True, ""


def get_case_digest(case_id: str) -> dict | None:
    """跨四类型读回结构化用例摘要（含解析后的步骤），供 AI 只读工具使用。"""
    obj, _model = find_case_across_types(case_id)
    if obj is None:
        return None
    case_type = getattr(obj, "case_type", "") or ""
    directory = getattr(obj, "directory", None)
    data: dict[str, Any] = {
        "case_id": obj.id,
        "title": obj.title,
        "case_type": case_type,
        "directory_id": directory.id if directory else None,
        "directory_name": directory.name if directory else "",
        "priority": getattr(obj, "priority", "") or "",
        "enabled": bool(getattr(obj, "enabled", True)),
        "description": getattr(obj, "description", "") or "",
        "precondition": getattr(obj, "precondition", "") or "",
        "expected_result": getattr(obj, "expected_result", "") or "",
        "created_at": _iso(getattr(obj, "created_at", None)),
        "updated_at": _iso(getattr(obj, "updated_at", None)),
    }
    if case_type == "ui_automation":
        data["package_name"] = getattr(obj, "package_name", "") or ""
        data["steps"] = _parse_steps(getattr(obj, "steps_json", ""))
    elif case_type == "web_automation":
        data["url"] = getattr(obj, "url", "") or ""
        data["steps"] = _parse_steps(getattr(obj, "steps_json", ""))
    elif case_type == "api_testing":
        data["config"] = getattr(obj, "config_json", {}) or {}
    else:  # storage
        data["rows"] = getattr(obj, "rows", []) or []
    return data


def save_ai_definition(
    *,
    case_id: str,
    title: str,
    case_type: str = "ui_automation",
    steps: list | None = None,
    directory_id: int | None = None,
    package_name: str = "",
    enabled: bool = True,
    priority: str = "P1",
    **extra: Any,
) -> tuple[bool, Any]:
    """AI 写用例入口：校验 steps 后经各类型 save_* 落库。

    UI/Web 的 steps 写入 ``steps_json``（执行器只消费 steps_data），
    不再落 legacy ``steps`` 文本字段。返回 (ok, payload|error)。
    """
    case_id = (case_id or "").strip()
    title = (title or "").strip()
    if not case_id:
        return False, "case_id 不能为空"
    if not title:
        return False, "title 不能为空"
    ct = case_type or "ui_automation"
    if ct not in ("ui_automation", "storage", "api_testing", "web_automation"):
        return (
            False,
            f"不支持的 case_type: {ct}（可选 ui_automation/storage/api_testing/web_automation）",
        )
    steps = steps or []

    if ct == "api_testing":
        return False, "API 测试用例请使用 save_api_test_case 工具，传入完整 config_json"

    if ct == "storage":
        from .api_storage import save_storage_definition

        try:
            obj = save_storage_definition(
                case_id=case_id,
                title=title,
                steps=steps,
                rows=extra.get("rows", []),
                directory_id=directory_id,
                priority=priority,
                enabled=enabled,
            )
        except ValueError as e:
            return False, str(e)
        return True, {"case_id": obj.id, "title": obj.title, "case_type": "storage"}

    ok, err = validate_steps(ct, steps)
    if not ok:
        return False, err

    try:
        if ct == "web_automation":
            from .api_web import save_web_definition

            obj = save_web_definition(
                case_id=case_id,
                title=title,
                directory_id=directory_id,
                steps_json=json.dumps(steps, ensure_ascii=False),
                priority=priority,
                enabled=enabled,
                url=extra.get("url", ""),
            )
        else:
            from .api_ui import save_definition

            obj = save_definition(
                case_id=case_id,
                title=title,
                case_type="ui_automation",
                steps_data=steps,
                directory_id=directory_id,
                package_name=package_name,
                priority=priority,
                enabled=enabled,
            )
    except ValueError as e:
        return False, str(e)
    return True, {
        "case_id": obj.id,
        "title": obj.title,
        "case_type": ct,
        "step_count": len(steps),
    }
