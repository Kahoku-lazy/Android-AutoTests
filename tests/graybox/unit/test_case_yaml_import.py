"""YAML 用例解析契约：执行提示保真、元数据映射、结构不合法时给可读原因。

只测纯逻辑（``api_yaml.parse_yaml_text`` 与引擎的 ``parse_step_hints``），不碰数据库。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from backend.apps.case_manager.api_yaml import parse_yaml_text
from backend.apps.case_manager.management.commands.import_case_yaml import _table_name
from engines.agents.workflow.case_file import parse_step_hints

pytestmark = [pytest.mark.unit, pytest.mark.case_manager]

STRUCTURED_YAML = """
- title: H6810 详情页开关与亮度功能测试
  steps:
    - action: 点击电源按钮
      assert: 设备日志返回开关成功
      anchor:
        page: H6810 详情页
        entry: 右上角电源按钮
        target: 电源按钮本体
      log:
        sku: H6810
        port: 7005
        keywords: [switch_on, switch_off]
    - action: 拖动亮度条
      assert: 设备日志返回亮度设置成功
"""


def test_steps_keep_anchor_and_log():
    rows, reason = parse_yaml_text(STRUCTURED_YAML)
    assert reason == ""
    assert len(rows) == 1
    steps = rows[0]["steps"]
    assert steps[0]["anchor"] == {
        "page": "H6810 详情页",
        "entry": "右上角电源按钮",
        "target": "电源按钮本体",
    }
    assert steps[0]["log"] == {
        "sku": "H6810",
        "port": 7005,
        "keywords": ["switch_on", "switch_off"],
    }
    # 没有执行提示的步骤不写空节点
    assert "anchor" not in steps[1]
    assert "log" not in steps[1]


def test_numeric_priority_maps_to_p0():
    text = """
- title: 甲
  priority: 1
  system: WEB/ANDROID/IOS
  type: 功能测试/自动化测试
  business: 家电/APP
  module: 设备管理
  case_id: 1
  steps:
    - action: a
      assert: b
"""
    rows, reason = parse_yaml_text(text)
    assert reason == ""
    row = rows[0]
    assert row["priority"] == "P0"
    assert row["system"] == "ANDROID"
    assert row["case_type"] == "AUTO"
    assert row["business_type"] == "appliance"
    assert row["module"] == "设备管理"
    assert row["source_case_id"] == "1"


def test_missing_metadata_uses_defaults():
    rows, reason = parse_yaml_text("- title: 甲\n  steps:\n    - action: a\n      assert: b\n")
    assert reason == ""
    row = rows[0]
    assert row["priority"] == "P1"
    assert row["system"] == "ANDROID"
    assert row["case_type"] == "AUTO"
    assert row["business_type"] == "appliance"
    assert row["module"] == ""
    assert row["source_case_id"] == ""


@pytest.mark.parametrize(
    "text, fragment",
    [
        ("just a string", "用例列表"),
        ("- title: 甲\n", "缺少 steps"),
        ("- title: 甲\n  steps:\n    - action: a\n", "缺少 action 或 assert"),
    ],
)
def test_invalid_structure_returns_readable_reason(text, fragment):
    rows, reason = parse_yaml_text(text)
    assert rows == []
    assert fragment in reason


def test_parse_step_hints_accepts_single_keyword():
    anchor, log, reason = parse_step_hints(None, {"sku": "H6810", "port": 7005, "keyword": "a"})
    assert reason == ""
    assert anchor == {}
    assert log == {"sku": "H6810", "port": 7005, "keywords": ["a"]}


def test_parse_step_hints_rejects_unknown_anchor_key():
    _anchor, _log, reason = parse_step_hints({"bad": "x"}, None)
    assert "anchor" in reason and "bad" in reason


def test_parse_step_hints_rejects_bad_port():
    _anchor, _log, reason = parse_step_hints(None, {"sku": "H6810", "port": 0, "keyword": "a"})
    assert "port" in reason


def test_table_name_uses_relative_path():
    root = Path("D:/data/H6810")
    assert _table_name(root, root / "01" / "h6810-short-card.yaml") == "01 / h6810-short-card"
    assert _table_name(root, root / "H6810_TEST_CASES.yml") == "H6810_TEST_CASES"
