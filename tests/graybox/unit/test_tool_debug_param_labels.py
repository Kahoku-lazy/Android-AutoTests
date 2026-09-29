"""灰盒·单元测试 — 工具调试参数的「中文名 + 说明」（变更 localize-tool-debug-params）。

零数据库、零设备：
1. schema 每个参数都带 `label`（中文名）与 `hint`（中文说明）；
2. 未登记参数回退英文名、docstring 未写说明时 `hint` 为空串；
3. 已登记参数的中文名符合口径（以 read_device_log 为例）；
4. 既有字段与行为不变（type/required/default/候选清单、无 user_id）。
"""

from __future__ import annotations

import pytest

from apps.ai_assistant.tools import (
    PARAM_LABELS,
    TOOL_PARAM_LABELS,
    TOOLS,
    get_tool_debug_schema,
    param_hints,
    param_label,
    read_device_log,
)


def test_every_param_has_label_and_hint_keys() -> None:
    """所有工具的所有参数都下发 label / hint，且 label 非空。"""
    for name in TOOLS:
        schema = get_tool_debug_schema(name)
        for item in schema["parameters"]:
            assert item["name"] != "user_id"
            assert "label" in item and "hint" in item
            assert item["label"].strip(), f"{name}.{item['name']} 的中文名为空"


def test_read_device_log_labels_match_agreed_wording() -> None:
    """已登记参数的中文名符合约定口径（需求方示例）。"""
    schema = get_tool_debug_schema("read_device_log")
    labels = {item["name"]: item["label"] for item in schema["parameters"]}
    assert labels["keyword"] == "日志关键词搜索"
    assert labels["at"] == "日志时间点"
    assert labels["port"] == "日志端口"
    assert labels["seconds"] == "查询跨度（秒）"


def test_read_device_log_hints_come_from_docstring() -> None:
    """说明取自 docstring 的 Args 段（含续行合并），不是另写一份。"""
    hints = param_hints(read_device_log)
    assert hints["keyword"].startswith("可选，只看包含该关键词的日志行")
    assert "忽略大小写" in hints["keyword"]
    assert "该时刻之后" in hints["at"]  # 续行并入了首行说明
    schema = {
        item["name"]: item["hint"]
        for item in get_tool_debug_schema("read_device_log")["parameters"]
    }
    assert schema["keyword"] == hints["keyword"]


def test_unknown_param_falls_back_to_english_name() -> None:
    """未登记参数回退英文名本身，绝不返回空串。"""
    assert param_label("never_registered_param", "read_device_log") == "never_registered_param"


def test_tool_level_label_overrides_generic() -> None:
    """工具级覆盖优先于通用表（同名参数在不同工具下语义不同）。"""
    assert ("xpath_action", "action") in TOOL_PARAM_LABELS
    assert param_label("action", "xpath_action") == "元素动作类型"
    assert param_label("action", "app_control") == "应用动作类型"
    assert param_label("action", "read_device_log") == "action"  # 未登记工具仍回退英文名


def test_generic_labels_present_for_shared_params() -> None:
    """通用参数（serial / text 等）在通用表里有中文名。"""
    for name in ("serial", "text", "xpath", "index", "package"):
        assert name in PARAM_LABELS


def test_docstring_without_args_yields_no_hints() -> None:
    """docstring 没有 Args 段 → 空说明表（不编造）。"""

    def sample(serial: str = "") -> str:
        """只读示例工具。"""

    assert param_hints(sample) == {}


def test_existing_fields_and_options_unchanged() -> None:
    """既有字段与候选清单行为不变（本变更只加字段）。"""
    schema = get_tool_debug_schema("tap_screen")
    by_name = {item["name"]: item for item in schema["parameters"]}
    assert by_name["serial"]["type"] == "str"
    assert by_name["serial"]["required"] is True
    assert by_name["serial"]["options_source"] == "devices:available"
    assert by_name["mode"]["default"] == "click"
    assert schema["read_only"] is False
    assert "user_id" not in by_name


def test_unknown_tool_raises() -> None:
    from apps.ai_assistant.tools import ToolNotFoundError

    with pytest.raises(ToolNotFoundError):
        get_tool_debug_schema("no_such_tool")
