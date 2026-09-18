"""element_locator「分组写」死代码清除后的双向门禁。

背景：「分组写」特性已在路由层停用（→ HTTP 410），但视图与 api 两层残留 12 个零调用函数。
本用例同时断言两件事，缺一不可：
1. 12 个符号确实已从模块与 `api.__all__` 消失（删干净）；
2. 4 个写路径**仍然** 410（没顺手把有意的产品决策也删掉）。
"""

from __future__ import annotations

import json

import pytest

from django.contrib.auth import get_user_model
from django.test import Client

from apps.element_locator import api as el_api
from apps.element_locator import views_api_assets, views_web_groups
from shared.auth.jwt_auth import create_access_token

pytestmark = [pytest.mark.django_db, pytest.mark.unit]

# (视图模块, 视图函数名, 对应 api 原语)
REMOVED_VIEWS = [
    (views_web_groups, "create_web_group", "create_web_group"),
    (views_web_groups, "batch_move_web_groups", "batch_move_web_groups"),
    (views_api_assets, "create_api_group", "create_api_group"),
    (views_api_assets, "batch_move_api_groups", "batch_move_api_groups"),
]
REMOVED_API_ONLY = ["rename_web_group", "delete_web_group", "rename_api_group", "delete_api_group"]

# 分组写已停用 → 410。路径用 router 形式：legacy 手写路由（无尾斜杠）已随尾斜杠约定统一
# 而删除，写路径现由 WebGroupViewSet / ApiGroupViewSet 的 perform_create 承接（同样 410）。
WRITE_PATHS = [
    "/api/elements/web-groups/",  # POST = create
    "/api/elements/web-groups/batch-move/",
    "/api/elements/api-groups/",  # POST = create
    "/api/elements/api-groups/batch-move/",
]


def _client() -> Client:
    user = get_user_model().objects.create_user(
        username="el-group-write-owner", password="x", email="el-gw@example.com"
    )
    return Client(HTTP_AUTHORIZATION=f"Bearer {create_access_token(str(user.pk))}")


@pytest.mark.parametrize(("module", "view_name", "api_name"), REMOVED_VIEWS)
def test_removed_view_and_its_api_primitive_are_gone(module, view_name, api_name):
    assert not hasattr(module, view_name), f"{module.__name__}.{view_name} 仍存在"
    assert api_name not in el_api.__all__, f"api.__all__ 仍含 {api_name}"
    assert not hasattr(el_api, api_name), f"api.{api_name} 仍存在"


@pytest.mark.parametrize("api_name", REMOVED_API_ONLY)
def test_removed_api_only_primitives_are_gone(api_name: str):
    assert api_name not in el_api.__all__, f"api.__all__ 仍含 {api_name}"
    assert not hasattr(el_api, api_name), f"api.{api_name} 仍存在"


@pytest.mark.parametrize("path", WRITE_PATHS)
def test_group_write_paths_still_return_410(path: str):
    """410 是有意的产品决策（分组树写接口停用），删死代码不得改变它。"""
    resp = _client().post(
        path,
        data=json.dumps({}),
        content_type="application/json",
    )
    assert resp.status_code == 410, resp.content[:200]
    assert resp.json()["status"] is False


def test_group_read_paths_still_work():
    """读路径（list）不受死代码清除影响。"""
    resp = _client().get("/api/elements/web-groups/")
    assert resp.status_code == 200, resp.content[:200]
    assert resp.json()["status"] is True
