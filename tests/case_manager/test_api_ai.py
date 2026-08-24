"""case-manager AI 数据出口（api_ai）单元测试 — 伪对象 + monkeypatch，零 DB。

覆盖：validate_steps 白名单/平台匹配/必填字段、get_case_digest 跨类型字段、
save_ai_definition 步骤落位（UI→steps_data、Web→steps_json 字符串）与错误透传。
"""

import json

from types import SimpleNamespace

import pytest

from apps.case_manager import api_ai

pytestmark = [pytest.mark.unit, pytest.mark.case_manager]


# ── validate_steps ──


def test_validate_steps_accepts_valid_ui():
    ok, err = api_ai.validate_steps(
        "ui_automation",
        [
            {"type": "adb_start_app", "xpath": "com.example.app"},
            {"type": "wait", "xpath": '//*[@text="登录"]', "timeout": 10},
            {"type": "click", "xpath": '//*[@text="登录"]'},
            {"type": "verify_text", "xpath": '//*[@text="首页"]', "expected_text": "首页"},
            {"type": "sleep", "index": 2},
        ],
    )
    assert ok is True
    assert err == ""


def test_validate_steps_accepts_valid_web():
    ok, err = api_ai.validate_steps(
        "web_automation",
        [
            {"type": "web_navigate", "url": "https://example.com"},
            {"type": "web_fill", "selector": "#username", "value": "admin"},
            {"type": "web_assert", "expected_text": "欢迎"},
        ],
    )
    assert ok is True


def test_validate_steps_rejects_empty():
    ok, err = api_ai.validate_steps("ui_automation", [])
    assert ok is False
    assert "不能为空" in err


def test_validate_steps_rejects_unknown_type():
    ok, err = api_ai.validate_steps("ui_automation", [{"type": "fly_to_moon"}])
    assert ok is False
    assert "步骤类型无效" in err


def test_validate_steps_rejects_deprecated_old_names():
    """旧名（start_app 等）不在 STEP_TYPE_META，AI 必须用 adb_ 新名。"""
    ok, err = api_ai.validate_steps("ui_automation", [{"type": "start_app", "xpath": "pkg"}])
    assert ok is False
    assert "步骤类型无效" in err


def test_validate_steps_rejects_cross_platform_type():
    ok, err = api_ai.validate_steps("ui_automation", [{"type": "web_navigate", "url": "http://x"}])
    assert ok is False
    assert "不适用于 common/android" in err


def test_validate_steps_rejects_missing_xpath():
    ok, err = api_ai.validate_steps("ui_automation", [{"type": "click"}])
    assert ok is False
    assert "缺少必填字段: xpath" in err


def test_validate_steps_rejects_missing_expected_text():
    ok, err = api_ai.validate_steps(
        "ui_automation", [{"type": "verify_text", "xpath": '//*[@text="x"]'}]
    )
    assert ok is False
    assert "缺少必填字段: expected_text" in err


def test_validate_steps_rejects_missing_selector():
    ok, err = api_ai.validate_steps("web_automation", [{"type": "web_click"}])
    assert ok is False
    assert "缺少必填字段: selector" in err


def test_validate_steps_non_list_and_non_dict():
    assert api_ai.validate_steps("ui_automation", None)[0] is False
    ok, err = api_ai.validate_steps("ui_automation", ["not-a-dict"])
    assert ok is False
    assert "不是对象" in err


def test_validate_steps_skips_storage_and_api():
    """storage / api_testing 不走本校验（各自链路）。"""
    for ct in ("storage", "api_testing"):
        ok, err = api_ai.validate_steps(ct, [{"type": "fly_to_moon"}])
        assert ok is True


# ── 审查修复回归（P1/P2）──


def test_validate_steps_rejects_bad_loop_index():
    """adb_loop_n 的 index 必须为 ≥1 的整数（防执行期 TypeError / 静默改写）。"""
    for bad in ("abc", "3", 0, -2, 1.5, True, None):
        ok, err = api_ai.validate_steps("ui_automation", [{"type": "adb_loop_n", "index": bad}])
        assert ok is False, f"index={bad!r} 应被拒绝"
        assert "index" in err
    ok, err = api_ai.validate_steps(
        "ui_automation", [{"type": "adb_loop_n", "index": 2, "children": [{"type": "sleep"}]}]
    )
    assert ok is True


def test_validate_steps_rejects_whitespace_required_field():
    ok, err = api_ai.validate_steps("ui_automation", [{"type": "click", "xpath": "   "}])
    assert ok is False
    assert "缺少必填字段: xpath" in err


def test_validate_steps_web_wait_any_of():
    ok, err = api_ai.validate_steps("web_automation", [{"type": "web_wait"}])
    assert ok is False
    assert "selector 或 index" in err
    assert (
        api_ai.validate_steps("web_automation", [{"type": "web_wait", "selector": "#x"}])[0] is True
    )
    assert api_ai.validate_steps("web_automation", [{"type": "web_wait", "index": 3}])[0] is True


def test_validate_steps_children_recursive():
    """容器步骤的 children 递归校验（缺 xpath 的子步骤被拦截）。"""
    ok, err = api_ai.validate_steps(
        "ui_automation",
        [{"type": "adb_if_appear", "xpath": "//*", "children": [{"type": "click"}]}],
    )
    assert ok is False
    assert "子步骤错误" in err and "缺少必填字段: xpath" in err
    ok, err = api_ai.validate_steps(
        "ui_automation",
        [
            {
                "type": "adb_if_appear",
                "xpath": "//*",
                "children": [{"type": "click", "xpath": "//*"}],
            }
        ],
    )
    assert ok is True


def test_save_ai_definition_rejects_unknown_case_type():
    ok, err = api_ai.save_ai_definition(
        case_id="TC-1", title="x", case_type="bogus", steps=[{"type": "click", "xpath": "//*"}]
    )
    assert ok is False
    assert "不支持的 case_type: bogus" in err


def test_save_ai_definition_storage_rows_passthrough(monkeypatch):
    from apps.case_manager import api_storage

    captured = {}
    monkeypatch.setattr(
        api_storage,
        "save_storage_definition",
        lambda **kw: captured.update(kw) or SimpleNamespace(id="ST-1", title="存储用例"),
    )
    rows = [{"title": "行1"}]
    ok, _ = api_ai.save_ai_definition(
        case_id="ST-1", title="存储用例", case_type="storage", steps=[], rows=rows
    )
    assert ok is True
    assert captured["rows"] == rows


# ── get_case_digest ──


def _ui_case(steps_json="[]"):
    return SimpleNamespace(
        id="TC-1",
        title="登录用例",
        case_type="ui_automation",
        priority="P0",
        enabled=True,
        description="desc",
        precondition="pre",
        expected_result="exp",
        package_name="com.example.app",
        steps_json=steps_json,
        directory=SimpleNamespace(id=3, name="登录模块"),
        created_at=None,
        updated_at=None,
    )


def test_get_case_digest_ui_with_steps(monkeypatch):
    monkeypatch.setattr(
        api_ai,
        "find_case_across_types",
        lambda cid: (_ui_case('[{"type": "click", "xpath": "//*[@text=\\"登录\\"]"}]'), None),
    )
    d = api_ai.get_case_digest("TC-1")
    assert d["case_id"] == "TC-1"
    assert d["case_type"] == "ui_automation"
    assert d["directory_name"] == "登录模块"
    assert d["package_name"] == "com.example.app"
    assert d["steps"] == [{"type": "click", "xpath": '//*[@text="登录"]'}]


def test_get_case_digest_api_config(monkeypatch):
    case = SimpleNamespace(
        id="API-1",
        title="接口用例",
        case_type="api_testing",
        priority="P1",
        enabled=True,
        description="",
        precondition="",
        expected_result="",
        config_json={"case_info": {"title": "接口用例"}, "steps": []},
        directory=None,
        created_at=None,
        updated_at=None,
    )
    monkeypatch.setattr(api_ai, "find_case_across_types", lambda cid: (case, None))
    d = api_ai.get_case_digest("API-1")
    assert d["config"]["case_info"]["title"] == "接口用例"
    assert "steps" not in d


def test_get_case_digest_bad_steps_json_returns_empty(monkeypatch):
    monkeypatch.setattr(api_ai, "find_case_across_types", lambda cid: (_ui_case("{broken"), None))
    d = api_ai.get_case_digest("TC-1")
    assert d["steps"] == []


def test_get_case_digest_missing_returns_none(monkeypatch):
    monkeypatch.setattr(api_ai, "find_case_across_types", lambda cid: (None, None))
    assert api_ai.get_case_digest("TC-X") is None


# ── save_ai_definition ──


def test_save_ai_definition_ui_writes_steps_data(monkeypatch):
    from apps.case_manager import api_ui

    captured = {}
    monkeypatch.setattr(
        api_ui,
        "save_definition",
        lambda **kw: captured.update(kw) or SimpleNamespace(id="TC-1", title="登录用例"),
    )
    steps = [{"type": "click", "xpath": '//*[@text="登录"]'}]
    ok, payload = api_ai.save_ai_definition(
        case_id="TC-1",
        title="登录用例",
        case_type="ui_automation",
        steps=steps,
        directory_id=3,
        package_name="com.example.app",
        priority="P0",
    )
    assert ok is True
    assert captured["steps_data"] == steps  # 步骤落 steps_data → 后端序列化进 steps_json
    assert captured["package_name"] == "com.example.app"
    assert captured["directory_id"] == 3
    assert payload["step_count"] == 1


def test_save_ai_definition_web_writes_steps_json_string(monkeypatch):
    from apps.case_manager import api_web

    captured = {}
    monkeypatch.setattr(
        api_web,
        "save_web_definition",
        lambda **kw: captured.update(kw) or SimpleNamespace(id="WEB-1", title="Web用例"),
    )
    steps = [{"type": "web_navigate", "url": "https://example.com"}]
    ok, payload = api_ai.save_ai_definition(
        case_id="WEB-1", title="Web用例", case_type="web_automation", steps=steps
    )
    assert ok is True
    assert json.loads(captured["steps_json"]) == steps


def test_save_ai_definition_rejects_invalid_steps_without_writing(monkeypatch):
    from apps.case_manager import api_ui

    called = []
    monkeypatch.setattr(api_ui, "save_definition", lambda **kw: called.append(kw))
    ok, err = api_ai.save_ai_definition(case_id="TC-1", title="x", steps=[{"type": "click"}])
    assert ok is False
    assert "缺少必填字段: xpath" in err
    assert called == []  # 校验失败不落库


def test_save_ai_definition_requires_id_and_title(monkeypatch):
    assert api_ai.save_ai_definition(case_id="", title="t", steps=[]) == (False, "case_id 不能为空")
    assert api_ai.save_ai_definition(case_id="TC-1", title="", steps=[]) == (
        False,
        "title 不能为空",
    )


def test_save_ai_definition_api_type_redirects():
    ok, err = api_ai.save_ai_definition(
        case_id="API-1", title="t", case_type="api_testing", steps=[]
    )
    assert ok is False
    assert "save_api_test_case" in err


def test_save_ai_definition_storage_passthrough(monkeypatch):
    from apps.case_manager import api_storage

    captured = {}
    monkeypatch.setattr(
        api_storage,
        "save_storage_definition",
        lambda **kw: captured.update(kw) or SimpleNamespace(id="ST-1", title="存储用例"),
    )
    ok, payload = api_ai.save_ai_definition(
        case_id="ST-1", title="存储用例", case_type="storage", steps=[]
    )
    assert ok is True
    assert payload["case_type"] == "storage"


def test_save_ai_definition_propagates_duplicate_title_error(monkeypatch):
    from apps.case_manager import api_ui

    def _dup(**kw):
        raise ValueError("目录「默认目录」下已存在同名用例「x」")

    monkeypatch.setattr(api_ui, "save_definition", _dup)
    ok, err = api_ai.save_ai_definition(
        case_id="TC-1", title="x", steps=[{"type": "click", "xpath": "//*"}]
    )
    assert ok is False
    assert "已存在同名用例" in err
