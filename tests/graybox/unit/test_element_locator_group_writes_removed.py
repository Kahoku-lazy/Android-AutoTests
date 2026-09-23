"""element_locator「分组写」路径彻底下线后的门禁。

历史：分组写特性先在路由层停用（→ HTTP 410），其零调用函数随后作为死代码清除。
变更 remove-element-locator-web-api 把 Web/API 两域整体下线：WebGroup / ApiGroup /
WebElement / ApiEndpoint / WebPageFlow 的模型、序列化器、ViewSet、路由与 admin 全部删除，
相关规格需求（Legacy group write path retired）随之 REMOVED —— 这些路径不再是 410，
而是**根本不存在**。

故本用例断言三件事：
1. 承载分组写的 4 个 legacy 视图模块仍然不存在；
2. 相关 api 原语确实不在 `api.__all__`；
3. 全部退役路径（读写在内）现在一律 **404**，而不是 410 —— 停用语义已被删除取代。
"""

from __future__ import annotations

import importlib.util
import json

import pytest

from django.contrib.auth import get_user_model
from django.test import Client

from apps.element_locator import api as el_api
from shared.auth.jwt_auth import create_access_token

pytestmark = [pytest.mark.django_db, pytest.mark.unit]

# 随 legacy 路由一起删除的视图模块（删路由后它们的符号再无引用者）
REMOVED_MODULES = [
    "apps.element_locator.views_web",
    "apps.element_locator.views_flows",
    "apps.element_locator.views_web_groups",
    "apps.element_locator.views_api_assets",
]
REMOVED_API_ONLY = ["rename_web_group", "delete_web_group", "rename_api_group", "delete_api_group"]
REMOVED_API_WITH_VIEW = [
    "create_web_group",
    "batch_move_web_groups",
    "create_api_group",
    "batch_move_api_groups",
]

# Web/API 两域下线后不再存在的路径（router 注册已随 urls.py 移除）
RETIRED_PATHS = [
    "/api/elements/web-groups/",
    "/api/elements/web-groups/batch-move/",
    "/api/elements/web/",
    "/api/elements/api-groups/",
    "/api/elements/api-groups/batch-move/",
    "/api/elements/api-endpoints/",
    "/api/elements/web-flows/",
]
# 原「分组写」路径：曾返回 410，现应因路由不存在而 404
FORMER_GROUP_WRITE_PATHS = [
    "/api/elements/web-groups/",
    "/api/elements/web-groups/batch-move/",
    "/api/elements/api-groups/",
    "/api/elements/api-groups/batch-move/",
]


def _client() -> Client:
    user = get_user_model().objects.create_user(
        username="el-group-write-owner", password="x", email="el-gw@example.com"
    )
    return Client(HTTP_AUTHORIZATION=f"Bearer {create_access_token(str(user.pk))}")


@pytest.mark.parametrize("module_name", REMOVED_MODULES)
def test_dead_view_modules_are_gone(module_name: str):
    """断言模块**整体**不存在，而不是逐个符号不存在 —— 强度更高，也守住"不再回来"。"""
    assert importlib.util.find_spec(module_name) is None, f"{module_name} 仍然存在"


@pytest.mark.parametrize("api_name", REMOVED_API_ONLY + REMOVED_API_WITH_VIEW)
def test_removed_api_primitives_are_gone(api_name: str):
    assert api_name not in el_api.__all__, f"api.__all__ 仍含 {api_name}"
    assert not hasattr(el_api, api_name), f"api.{api_name} 仍存在"


@pytest.mark.parametrize("path", RETIRED_PATHS)
def test_retired_paths_are_gone(path: str):
    """退役路径既不解析、也不返回 410 —— 停用语义已被删除取代。"""
    resp = _client().get(path)
    assert resp.status_code == 404, resp.content[:200]


@pytest.mark.parametrize("path", FORMER_GROUP_WRITE_PATHS)
def test_former_group_write_paths_are_gone(path: str):
    resp = _client().post(path, data=json.dumps({}), content_type="application/json")
    assert resp.status_code == 404, resp.content[:200]
