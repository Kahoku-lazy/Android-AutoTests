"""关键词范围与入参校验（纯逻辑，零 DB）：非法范围 / 空关键词在查库前拒绝。"""

from __future__ import annotations

import pytest

from backend.apps.serial_log import api

pytestmark = [pytest.mark.unit]


@pytest.mark.parametrize("scope", ["H6601专用", "../x", "a b", "通用", "H6601;DROP"])
def test_upsert_rejects_illegal_scope(scope):
    """范围只接受 '*' 或 SKU 名白名单；中文展示值 / 路径 / 空格一律拒绝。"""
    with pytest.raises(ValueError, match="范围"):
        api.upsert_keyword("switch_on", module="设备开关", feature="打开设备成功", scope=scope)


def test_upsert_rejects_empty_keyword():
    """关键词去空白后为空时拒绝。"""
    with pytest.raises(ValueError, match="关键词"):
        api.upsert_keyword("   ", module="设备开关", feature="打开设备成功")


@pytest.mark.parametrize("scope", ["H6601专用", "../x", "a b"])
def test_create_rejects_illegal_scope_before_db(scope):
    """新建接口的范围校验在查库前发生（零 DB）。"""
    with pytest.raises(ValueError, match="范围"):
        api.create_keyword("switch_on", module="m", feature="f", scope=scope)


def test_create_rejects_empty_texts_before_db():
    """新建接口的必填文本校验在查库前发生（零 DB）。"""
    with pytest.raises(ValueError, match="关键词"):
        api.create_keyword("  ", module="m", feature="f")
    with pytest.raises(ValueError, match="功能模块"):
        api.create_keyword("kw", module="", feature="f")
    with pytest.raises(ValueError, match="功能点"):
        api.create_keyword("kw", module="m", feature="")
