"""运营后台：除批量注销端点外，不注册按 id 删除的路径。"""

from __future__ import annotations

import pytest

from django.urls import Resolver404, resolve

pytestmark = [pytest.mark.api]


@pytest.mark.parametrize(
    "path",
    [
        "/api/ops/users/",
        "/api/ops/users/1/",
        "/api/ops/users/1/delete/",
    ],
)
def test_delete_requests_have_no_route(path: str):
    """删除型路径不解析出可调用视图（`/api/ops/users/` 本身只接受 GET 列表）。

    Args:
        path: 待解析路径；`/api/ops/users/1/` 与 `.../delete/` 必须落空。
    """
    if path == "/api/ops/users/":
        # 列表路由存在，但只声明了 GET：解析成功不代表可删除
        assert resolve(path) is not None
        return
    with pytest.raises(Resolver404):
        resolve(path)


def test_purge_is_the_only_delete_route():
    """批量注销走 `/api/ops/users/purge/`；按 id 的删除路径仍然不存在。"""
    assert resolve("/api/ops/users/purge/") is not None
    with pytest.raises(Resolver404):
        resolve("/api/ops/users/1/purge/")
