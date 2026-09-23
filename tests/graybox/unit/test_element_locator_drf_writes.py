"""element_locator DRF 视图的写库收敛断言。

Web/API 两域（WebElement / WebGroup / WebPageFlow / ApiGroup / ApiEndpoint）随变更
remove-element-locator-web-api 整体下线，其序列化器与 ViewSet 已删除；本文件原先针对
WebPageFlow / WebElement 的 4 条写路径用例随对象消失而移除。

保留的这条收敛断言仍然有效：views_drf 里不得出现 `serializer.save()`。
"""

from __future__ import annotations

import inspect

import pytest

from apps.element_locator import views_drf

pytestmark = [pytest.mark.unit]


def test_drf_views_have_no_serializer_save():
    """收敛断言：DRF 视图不得再出现 `serializer.save()`。"""
    assert "serializer.save()" not in inspect.getsource(views_drf)
