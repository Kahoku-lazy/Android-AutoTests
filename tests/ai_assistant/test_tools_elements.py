"""元素定位 AI 工具 — schema / registry / 查询 handler 单元测试。

覆盖 Android 三工具（search_elements / list_pages / fetch_page_elements）与
Web / API 新增四工具（list_web_groups / search_web_elements /
list_api_groups / search_api_endpoints）。handler 走 ORM 查询，用伪 Manager /
QuerySet 记录 filter/order_by 调用并返回受控数据，不依赖数据库。
"""

import pytest

from apps.ai_assistant.agent_scope import tool_registry

pytestmark = [pytest.mark.unit, pytest.mark.ai_assistant]


# ── 伪 ORM 设施 ──


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


# ── schema 注册 ──

NEW_ELEMENT_TOOLS = {
    "list_web_groups": ("elements", "list_web_groups"),
    "search_web_elements": ("elements", "search_web"),
    "list_api_groups": ("elements", "list_api_groups"),
    "search_api_endpoints": ("elements", "search_endpoints"),
}


def test_new_element_tool_schemas_registered():
    """4 个新工具均在 TOOL_SCHEMAS：元素定位分类、只读、module=elements。"""
    schemas = {t["name"]: t for t in tool_registry.TOOL_SCHEMAS}
    for name, (module, action) in NEW_ELEMENT_TOOLS.items():
        s = schemas.get(name)
        assert s is not None, f"{name} 未注册"
        assert s["module"] == module
        assert s["action"] == action
        assert s["read_only"] is True
        assert s["category"] == "元素定位"


def test_resolve_new_element_handlers():
    """4 个新工具的 handler 均注册可解析。"""
    for module, action in NEW_ELEMENT_TOOLS.values():
        assert tool_registry.resolve(module, action) is not None


# ── Web 元素 handler ──


def test_search_web_handler_filters_and_orders(monkeypatch):
    """search_web：Q 组合覆盖 name/locator_value/page_url/description/tags，按 name 排序。"""
    from apps.element_locator import models as el_models

    log = []
    monkeypatch.setattr(el_models.WebElement, "objects", _FakeManager([1, 2, 3], log))

    handler = tool_registry.resolve("elements", "search_web")
    out = handler("7", query="登录", limit=2)
    assert out == [1, 2]

    filter_calls = [c for c in log if c[0] == "filter"]
    assert len(filter_calls) == 1
    q = filter_calls[0][1][0]
    for field in (
        "name__icontains",
        "locator_value__icontains",
        "page_url__icontains",
        "description__icontains",
        "tags__icontains",
    ):
        assert field in str(q), f"Q 组合缺少 {field}"
    assert any(c[0] == "order_by" and c[1] == ("name",) for c in log)


def test_search_web_handler_empty_query_skips_filter(monkeypatch):
    """search_web：query 为空时不调用 filter，返回全部。"""
    from apps.element_locator import models as el_models

    log = []
    monkeypatch.setattr(el_models.WebElement, "objects", _FakeManager([1, 2], log))

    out = tool_registry.resolve("elements", "search_web")("7")
    assert out == [1, 2]
    assert not any(c[0] == "filter" for c in log)


def test_list_web_groups_handler_orders(monkeypatch):
    """list_web_groups：按 sort_order、name 排序返回。"""
    from apps.element_locator import models as el_models

    log = []
    monkeypatch.setattr(el_models.WebGroup, "objects", _FakeManager(["a", "b"], log))

    out = tool_registry.resolve("elements", "list_web_groups")("7", limit=5)
    assert out == ["a", "b"]
    assert any(c[0] == "order_by" and c[1] == ("sort_order", "name") for c in log)


# ── API 接口 handler ──


def test_search_endpoints_handler_filters_and_orders(monkeypatch):
    """search_endpoints：query 走 Q（name/url/description/tags），method 走 iexact，按 name 排序。"""
    from apps.element_locator import models as el_models

    log = []
    monkeypatch.setattr(el_models.ApiEndpoint, "objects", _FakeManager([1, 2], log))

    handler = tool_registry.resolve("elements", "search_endpoints")
    out = handler("7", query="登录", method="POST", limit=1)
    assert out == [1]

    filter_calls = [c for c in log if c[0] == "filter"]
    assert len(filter_calls) == 2
    q = filter_calls[0][1][0]
    for field in ("name__icontains", "url__icontains", "description__icontains", "tags__icontains"):
        assert field in str(q), f"Q 组合缺少 {field}"
    assert filter_calls[1][2] == {"method__iexact": "POST"}
    assert any(c[0] == "order_by" and c[1] == ("name",) for c in log)


def test_search_endpoints_handler_without_filters(monkeypatch):
    """search_endpoints：query/method 均为空时不调用 filter。"""
    from apps.element_locator import models as el_models

    log = []
    monkeypatch.setattr(el_models.ApiEndpoint, "objects", _FakeManager([1], log))

    out = tool_registry.resolve("elements", "search_endpoints")("7")
    assert out == [1]
    assert not any(c[0] == "filter" for c in log)


def test_list_api_groups_handler_orders(monkeypatch):
    """list_api_groups：按 sort_order、name 排序返回。"""
    from apps.element_locator import models as el_models

    log = []
    monkeypatch.setattr(el_models.ApiGroup, "objects", _FakeManager(["x"], log))

    out = tool_registry.resolve("elements", "list_api_groups")("7")
    assert out == ["x"]
    assert any(c[0] == "order_by" and c[1] == ("sort_order", "name") for c in log)


# ── Android list_pages 排序修复回归 ──


def test_list_pages_orders_by_created_at(monkeypatch):
    """list_pages：el_pages 无 updated_at 字段，须按 -created_at 排序（回归）。"""
    from apps.element_locator import models as el_models

    log = []
    monkeypatch.setattr(el_models.Page, "objects", _FakeManager([1], log))

    out = tool_registry.resolve("elements", "list_pages")("7")
    assert out == [1]
    order_calls = [c for c in log if c[0] == "order_by"]
    assert order_calls and order_calls[0][1] == ("-created_at",)
