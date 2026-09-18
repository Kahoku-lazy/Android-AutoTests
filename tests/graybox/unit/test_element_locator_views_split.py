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
# 只覆盖**没有 router 对应**的手写路径：pages / items / move / files。
# web、web-groups、api-groups、api-endpoints、flows、web-flows 的 legacy 手写实现
# 已随尾斜杠约定统一而删除（原先靠"无斜杠→legacy / 带斜杠→router"并存），
# 那些路径改由下方的 ROUTER_ROUTES 守护。
# func_name 为 None 的条目其视图是 `@api_view` 装饰器产物（`__name__` 恒为 'view'），
# 故只校验路由契约。
LEGACY_ROUTES = [
    ("pages/", "pages_list", "list_pages"),
    ("pages/create/", "page_create", "create_page"),
    ("pages/import-snapshot/", "pages_import_snapshot", "import_snapshot"),
    ("pages/clear/", "pages_clear", "clear_pages"),
    ("pages/batch-move/", "pages_batch_move", "pages_batch_move"),
    ("pages/1/", "page_detail", "page_detail"),
    ("pages/1/items/", "page_items", "page_elements"),
    ("pages/1/elements/", "page_add_element", "add_element_to_page"),
    ("pages/1/elements/batch/", "page_batch_add_elements", "batch_add_elements"),
    ("items/1/", "item_update", "update_element"),
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
    # 以下路径原先由 legacy 手写实现服务（与 router 靠尾斜杠差异并存），现收敛到 router：
    # 它们必须仍然可达，且由对应 ViewSet 处理 —— 这是"删 legacy 没删掉能力"的护栏。
    ("web/batch/", "WebElementViewSet"),
    ("web/1/", "WebElementViewSet"),
    ("web-groups/batch-move/", "WebGroupViewSet"),
    ("web-groups/1/", "WebGroupViewSet"),
    ("api-groups/batch-move/", "ApiGroupViewSet"),
    ("api-groups/1/", "ApiGroupViewSet"),
    ("api-endpoints/1/", "ApiEndpointViewSet"),
    ("flows/1/", "PageFlowViewSet"),
    ("web-flows/1/", "WebPageFlowViewSet"),
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
