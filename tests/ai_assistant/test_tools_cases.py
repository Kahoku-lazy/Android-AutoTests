"""用例管理 AI 工具 — schema / registry / 查询 handler 单元测试。

覆盖新增只读工具 list_case_directories / search_cases：
伪 Manager / QuerySet 记录 filter/order_by 调用并返回受控记录
（SimpleNamespace 模拟四类用例模型实例），不依赖数据库。
"""

import datetime

from types import SimpleNamespace

import pytest

from apps.ai_assistant.agent_scope import tool_registry

pytestmark = [pytest.mark.unit, pytest.mark.ai_assistant]


class _FakeQS(list):
    """伪 QuerySet：记录 filter/order_by 调用，支持切片返回自身。"""

    def __init__(self, items, log):
        super().__init__(items)
        self._log = log

    def filter(self, *args, **kwargs):
        self._log.append(("filter", args, kwargs))
        return self

    def select_related(self, *args):
        return self

    def order_by(self, *fields):
        self._log.append(("order_by", fields))
        return self

    def __getitem__(self, key):
        result = list.__getitem__(self, key)
        if isinstance(key, slice):
            return _FakeQS(result, self._log)
        return result


class _FakeManager:
    """伪 Manager：select_related/filter/order_by 均返回 _FakeQS。"""

    def __init__(self, items, log):
        self._items = list(items)
        self._log = log

    def select_related(self, *args):
        return _FakeQS(self._items, self._log)

    def filter(self, *args, **kwargs):
        return _FakeQS(self._items, self._log).filter(*args, **kwargs)

    def order_by(self, *fields):
        return _FakeQS(self._items, self._log).order_by(*fields)


def _rec(title, cid="CASE-1", priority="P1", directory="登录模块", dt=None):
    """SimpleNamespace 模拟用例模型实例（含 directory 外键对象）。"""
    return SimpleNamespace(
        id=cid,
        title=title,
        priority=priority,
        directory=SimpleNamespace(name=directory),
        updated_at=dt or datetime.datetime(2026, 8, 19, 12, 0, 0),
    )


# ── schema 注册 ──


def test_case_search_tool_schemas_registered():
    """list_case_directories / search_cases：用例管理分类、只读、module=cases。"""
    schemas = {t["name"]: t for t in tool_registry.TOOL_SCHEMAS}
    for name, action in (("list_case_directories", "list_directories"), ("search_cases", "search")):
        s = schemas.get(name)
        assert s is not None, f"{name} 未注册"
        assert s["module"] == "cases"
        assert s["action"] == action
        assert s["read_only"] is True
        assert s["category"] == "用例管理"


def test_resolve_case_search_handlers():
    """cases/list_directories 与 cases/search 均注册可解析。"""
    assert tool_registry.resolve("cases", "list_directories") is not None
    assert tool_registry.resolve("cases", "search") is not None


# ── list_case_directories handler ──


def test_list_directories_handler_orders_and_filters(monkeypatch):
    """list_directories：按 sort_order/name 排序；case_type 传参时加过滤。"""
    from apps.case_manager import models as cm_models

    log = []
    monkeypatch.setattr(cm_models.CaseDirectory, "objects", _FakeManager(["d1", "d2"], log))

    handler = tool_registry.resolve("cases", "list_directories")
    out = handler("7")
    assert out == ["d1", "d2"]
    assert any(c[0] == "order_by" and c[1] == ("sort_order", "name") for c in log)

    handler("7", case_type="api_testing")
    assert any(c[0] == "filter" and c[2] == {"case_type": "api_testing"} for c in log)


def test_list_directories_handler_without_type_skips_filter(monkeypatch):
    """list_directories：case_type 为空时不调用 filter。"""
    from apps.case_manager import models as cm_models

    log = []
    monkeypatch.setattr(cm_models.CaseDirectory, "objects", _FakeManager(["d1"], log))

    tool_registry.resolve("cases", "list_directories")("7")
    assert not any(c[0] == "filter" for c in log)


# ── search_cases handler ──


def _patch_case_models(monkeypatch, ui=None, storage=None, api=None, web=None):
    """给四类用例模型挂伪 Manager，返回各模型的调用日志。"""
    from apps.case_manager import models as cm_models
    from apps.case_manager import models_api, models_storage, models_web

    logs = {}
    targets = (
        (cm_models.TestDefinition, "ui_automation", ui),
        (models_storage.StorageTestCase, "storage", storage),
        (models_api.ApiTestCase, "api_testing", api),
        (models_web.WebTestCase, "web_automation", web),
    )
    for model, key, records in targets:
        logs[key] = []
        monkeypatch.setattr(model, "objects", _FakeManager(records or [], logs[key]))
    return logs


def test_search_cases_merges_all_types_without_filter(monkeypatch):
    """search_cases：不带 case_type 时跨四类型合并，输出统一 dict 形状。"""
    _patch_case_models(
        monkeypatch,
        ui=[_rec("UI登录用例", cid="UI-1")],
        storage=[_rec("存储冒烟", cid="ST-1", priority="")],
        api=[_rec("列表接口", cid="API-1")],
        web=[_rec("Web下单", cid="WEB-1")],
    )

    out = tool_registry.resolve("cases", "search")("7")
    assert len(out) == 4
    titles = {r["title"] for r in out}
    assert titles == {"UI登录用例", "存储冒烟", "列表接口", "Web下单"}
    assert out[0].keys() == {"id", "title", "case_type", "directory", "priority", "updated_at"}
    assert {r["case_type"] for r in out} == {
        "ui_automation",
        "storage",
        "api_testing",
        "web_automation",
    }
    by_title = {r["title"]: r for r in out}
    assert by_title["UI登录用例"]["directory"] == "登录模块"
    assert by_title["UI登录用例"]["priority"] == "P1"
    assert by_title["存储冒烟"]["priority"] == ""


def test_search_cases_filters_by_type_and_query_and_directory(monkeypatch):
    """search_cases：case_type 只查对应模型；query 走 title/id Q 组合；directory_id 过滤。"""
    logs = _patch_case_models(monkeypatch, ui=[_rec("UI登录用例")], api=[_rec("列表接口")])

    out = tool_registry.resolve("cases", "search")(
        "7", case_type="api_testing", query="接口", directory_id=9, limit=5
    )
    assert [r["title"] for r in out] == ["列表接口"]

    # ui 模型不应被查询到（无记录），api 模型的调用链包含 Q 过滤 + directory 过滤
    api_log = logs["api_testing"]
    filter_calls = [c for c in api_log if c[0] == "filter"]
    assert len(filter_calls) == 2
    q = filter_calls[0][1][0]
    assert "title__icontains" in str(q) and "id__icontains" in str(q)
    assert filter_calls[1][2] == {"directory_id": 9}


def test_search_cases_empty_query_skips_filters(monkeypatch):
    """search_cases：query/directory_id 均为空时不调用 filter。"""
    logs = _patch_case_models(monkeypatch, ui=[_rec("UI登录用例")])

    out = tool_registry.resolve("cases", "search")("7")
    assert [r["title"] for r in out] == ["UI登录用例"]
    assert not any(c[0] == "filter" for c in logs["ui_automation"])


def test_search_cases_caps_merged_rows(monkeypatch):
    """search_cases：合并后按 updated_at 降序截断 limit。"""
    _patch_case_models(
        monkeypatch,
        ui=[_rec("旧用例", cid="UI-1", dt=datetime.datetime(2026, 8, 1))],
        api=[_rec("新接口", cid="API-1", dt=datetime.datetime(2026, 8, 19))],
    )

    out = tool_registry.resolve("cases", "search")("7", limit=1)
    assert [r["title"] for r in out] == ["新接口"]


# ── get_case handler（digest 化）──


def test_get_definition_handler_returns_digest(monkeypatch):
    """get_case：返回结构化 digest dict（不再漏模型实例被 str 化）。"""
    from apps.case_manager import api as cm_api

    digest = {"case_id": "TC-1", "title": "登录", "steps": [{"type": "click"}]}
    monkeypatch.setattr(cm_api, "get_case_digest", lambda cid: digest)
    out = tool_registry.resolve("cases", "get_definition")("7", case_id="TC-1")
    assert out == digest


def test_get_definition_handler_requires_case_id():
    with pytest.raises(ValueError, match="case_id"):
        tool_registry.resolve("cases", "get_definition")("7")


def test_get_definition_handler_missing_case_raises(monkeypatch):
    from apps.case_manager import api as cm_api

    monkeypatch.setattr(cm_api, "get_case_digest", lambda cid: None)
    with pytest.raises(ValueError, match="用例不存在"):
        tool_registry.resolve("cases", "get_definition")("7", case_id="TC-X")


# ── save_case handler（api_ai 校验写入）──


def test_save_definition_handler_passes_to_api_ai(monkeypatch):
    """save_case：参数透传 api.save_ai_definition；成功返回 payload。"""
    from apps.case_manager import api as cm_api

    captured = {}
    monkeypatch.setattr(
        cm_api,
        "save_ai_definition",
        lambda **kw: captured.update(kw) or (True, {"case_id": "TC-1", "step_count": 1}),
    )
    steps = [{"type": "click", "xpath": "//*"}]
    out = tool_registry.resolve("cases", "save_definition")(
        "7",
        case_id="TC-1",
        title="登录",
        case_type="ui_automation",
        steps=steps,
        directory_id=3,
        package_name="com.example.app",
        enabled=True,
        priority="P0",
    )
    assert out == {"case_id": "TC-1", "step_count": 1}
    assert captured["steps"] == steps
    assert captured["directory_id"] == 3
    assert captured["package_name"] == "com.example.app"
    assert captured["priority"] == "P0"


def test_save_definition_handler_validation_error_raises(monkeypatch):
    """save_case：写侧校验失败 → ValueError（网关 400），不落库。"""
    from apps.case_manager import api as cm_api

    monkeypatch.setattr(
        cm_api,
        "save_ai_definition",
        lambda **kw: (False, "第 1 步 [click] 缺少必填字段: xpath"),
    )
    with pytest.raises(ValueError, match="缺少必填字段: xpath"):
        tool_registry.resolve("cases", "save_definition")(
            "7", case_id="TC-1", title="登录", steps=[{"type": "click"}]
        )


def test_save_definition_handler_requires_id_and_title():
    handler = tool_registry.resolve("cases", "save_definition")
    with pytest.raises(ValueError, match="case_id"):
        handler("7", title="登录", steps=[])
    with pytest.raises(ValueError, match="title"):
        handler("7", case_id="TC-1", steps=[])


def test_save_definition_handler_normalizes_string_enabled(monkeypatch):
    """HTTP 直调传 enabled='false' 时不得被 bool('false')→True 误启用。"""
    from apps.case_manager import api as cm_api

    captured = {}
    monkeypatch.setattr(
        cm_api,
        "save_ai_definition",
        lambda **kw: captured.update(kw) or (True, {"case_id": "TC-1"}),
    )
    handler = tool_registry.resolve("cases", "save_definition")
    handler(
        "7", case_id="TC-1", title="x", steps=[{"type": "click", "xpath": "//*"}], enabled="false"
    )
    assert captured["enabled"] is False
    handler("7", case_id="TC-2", title="x", steps=[{"type": "click", "xpath": "//*"}], enabled=True)
    assert captured["enabled"] is True
