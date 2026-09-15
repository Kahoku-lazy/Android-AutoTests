"""element_locator legacy 视图拆分（原 `views.py` 1357 行 → 7 个域模块）后的回归门禁。

拆分最典型的失败是「路由悄悄失效」或「搬家漏名」，故本用例：
1. 逐条 `resolve()` 全部 legacy + router 路径，断言 `url_name` 未变（路由契约）；
   对纯函数视图**额外**断言 `func.__name__`，防「名字没变但指向了别的视图」；
2. 断言每个 `views*.py` 行数 ≤ calibration §4 上限（300），防巨石回涨；
3. 断言单文件 `views.py` 已不存在。
"""

from __future__ import annotations

import pathlib

import pytest

from django.urls import resolve

pytestmark = [pytest.mark.unit]

MOUNT = "/api/elements/"
APP_DIR = pathlib.Path(__file__).resolve().parents[3] / "apps" / "element_locator"

# (相对路径, url_name, 预期视图函数名 | None) —— 与 urls.py 逐条对齐。
# func_name 为 None 的条目其视图是 `@api_view` 装饰器产物（`__name__` 恒为 'view'，
# 且不在本次拆分之列，见 views_projects_drf.py），故只校验路由契约。
LEGACY_ROUTES = [
    ("pages", "pages_list", "list_pages"),
    ("pages/create", "page_create", "create_page"),
    ("pages/import-snapshot", "pages_import_snapshot", "import_snapshot"),
    ("pages/clear", "pages_clear", "clear_pages"),
    ("pages/batch-move", "pages_batch_move", "pages_batch_move"),
    ("pages/1", "page_detail", "page_detail"),
    ("pages/1/items", "page_items", "page_elements"),
    ("pages/1/elements", "page_add_element", "add_element_to_page"),
    ("pages/1/elements/batch", "page_batch_add_elements", "batch_add_elements"),
    ("items/1", "item_update", "update_element"),
    ("flows", "flows", "flows_handler"),
    ("flows/1", "flow_delete", "delete_flow"),
    ("web", "web_elements_list", "list_web_elements"),
    ("web/create", "web_element_create", "create_web_element"),
    ("web/batch", "web_elements_batch", "batch_import_web_elements"),
    ("web/1", "web_element_detail", "web_element_detail"),
    ("web-groups", "web_groups_list", "list_web_groups"),
    # group_write_gone 是 `@api_view` 产物（`__name__` 恒为 'view'），只校验路由契约
    ("web-groups/create", "web_group_create", None),
    ("web-groups/batch-move", "web_groups_batch_move", None),
    ("web-groups/1", "web_group_detail", "web_group_detail"),
    ("web-flows", "web_flows_list", "web_flows_handler"),
    ("web-flows/1", "web_flow_delete", "delete_web_flow"),
    ("api-groups", "api_groups_list", "list_api_groups"),
    ("api-groups/create", "api_group_create", None),
    ("api-groups/batch-move", "api_groups_batch_move", None),
    ("api-groups/1", "api_group_detail", "api_group_detail"),
    ("api-endpoints", "api_endpoints_list", "list_api_endpoints"),
    ("api-endpoints/create", "api_endpoint_create", "create_api_endpoint"),
    ("api-endpoints/1", "api_endpoint_detail", "api_endpoint_detail"),
    ("move/", "el_move", None),
    ("files/batch-delete/", "el_files_batch_delete", None),
]

ROUTER_ROUTES = [
    ("projects/", "LocatorProjectViewSet"),
    ("directories/", "LocatorDirectoryViewSet"),
    ("web-groups/", "WebGroupViewSet"),
    ("web/", "WebElementViewSet"),
    ("api-groups/", "ApiGroupViewSet"),
    ("api-endpoints/", "ApiEndpointViewSet"),
    ("flows/", "PageFlowViewSet"),
    ("web-flows/", "WebPageFlowViewSet"),
]

VIEWS_LINE_LIMIT = 300


@pytest.mark.parametrize(("path", "url_name", "func_name"), LEGACY_ROUTES)
def test_legacy_route_unchanged(path: str, url_name: str, func_name: str | None):
    """拆分后 legacy 路径的 `url_name`（必要时含视图函数名）必须不变。"""
    match = resolve(f"{MOUNT}{path}")
    assert match.url_name == url_name
    if func_name is not None:
        assert match.func.__name__ == func_name


@pytest.mark.parametrize(("path", "cls_name"), ROUTER_ROUTES)
def test_router_route_unchanged(path: str, cls_name: str):
    """拆分不得影响 DRF router 端点（它们来自 views_drf / views_projects_drf）。"""
    assert resolve(f"{MOUNT}{path}").func.cls.__name__ == cls_name


def test_every_views_module_is_within_line_budget():
    """calibration §4：`views*.py` 上限 300 行（拆分前 `views.py` 为 1357 行 = 4.5×）。"""
    files = sorted(APP_DIR.glob("views*.py"))
    assert files, "未找到任何 views 模块"

    over = {}
    for path in files:
        count = len(path.read_text(encoding="utf-8").splitlines())
        if count > VIEWS_LINE_LIMIT:
            over[path.name] = count
    assert over == {}, f"超过 {VIEWS_LINE_LIMIT} 行的视图模块: {over}"


def test_monolithic_views_module_is_gone():
    """单文件 `views.py` 应已拆分删除（无转发壳）。"""
    assert not (APP_DIR / "views.py").exists()
