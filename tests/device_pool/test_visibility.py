"""is_device_visible 单元测试 — 设备列表可见性过滤（PRD §2.5.1）。

覆盖 5 分支：管理员全局 / USB 恒公开 / 公开 WIFI 全见 / 锁定 WIFI 对锁定者+配置者可见 /
锁定 WIFI 对他人隐藏。
"""

from types import SimpleNamespace

import pytest

from apps.device_pool.service import is_device_visible

pytestmark = [pytest.mark.unit, pytest.mark.device_pool]


def _dev(connection_type: str, locked_by: str = "", added_by: str = "") -> SimpleNamespace:
    """构造轻量设备对象（仅含可见性判定所需字段）。"""
    return SimpleNamespace(connection_type=connection_type, locked_by=locked_by, added_by=added_by)


def test_admin_sees_locked_device():
    """管理员命中数字 ID 白名单，无论锁定/公开/连接类型均可见。"""
    dev = _dev("WIFI", locked_by="2", added_by="2")
    assert is_device_visible(dev, "1", {"1"}) is True


def test_usb_always_visible():
    """USB 设备恒公开，即使 locked_by 被他人占用（历史脏数据）也不受锁定影响。"""
    dev = _dev("USB", locked_by="bob", added_by="bob")
    assert is_device_visible(dev, "alice", set()) is True


def test_public_wifi_visible_to_anyone():
    """公开 WIFI（locked_by 空）对所有用户可见。"""
    dev = _dev("WIFI", locked_by="", added_by="bob")
    assert is_device_visible(dev, "alice", set()) is True


def test_locked_wifi_visible_to_locker():
    """锁定 WIFI 对锁定者（locked_by）可见。"""
    dev = _dev("WIFI", locked_by="alice", added_by="alice")
    assert is_device_visible(dev, "alice", set()) is True


def test_locked_wifi_visible_to_configurer():
    """锁定 WIFI 对配置者（added_by）可见，即使锁定者是他人。"""
    dev = _dev("WIFI", locked_by="bob", added_by="alice")
    assert is_device_visible(dev, "alice", set()) is True


def test_locked_wifi_hidden_from_others():
    """锁定 WIFI 对既非锁定者也非配置者的用户隐藏。"""
    dev = _dev("WIFI", locked_by="bob", added_by="bob")
    assert is_device_visible(dev, "carol", set()) is False


def test_anonymous_sees_only_public():
    """匿名（空 user_id）只能看到公开设备，锁定设备隐藏。"""
    assert is_device_visible(_dev("WIFI", locked_by="", added_by="bob"), "", set()) is True
    assert is_device_visible(_dev("WIFI", locked_by="bob", added_by="bob"), "", set()) is False
    assert is_device_visible(_dev("USB"), "", set()) is True
