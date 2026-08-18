"""resolve_admin_ids / claim_wireless_device 单元测试（PRD §2.5.1 管理员判定 + 默认锁定）。

纯逻辑零 I/O：通过 monkeypatch 替换 User 查询与 set_device_lock，不触碰数据库
（项目 migrations 含 MySQL 专用 RunSQL，SQLite 测试库迁移不可用）。
"""

from types import SimpleNamespace

import pytest

from apps.device_pool import service as service_module

pytestmark = [pytest.mark.unit, pytest.mark.device_pool]


# ═══════════════════════════════════════════════
# resolve_admin_ids — 混合白名单归一化
# ═══════════════════════════════════════════════


def _patch_user(monkeypatch, id_map: dict):
    """用 fake User.objects 替换真实查询，返回 (username -> id) 映射。"""

    class _FakeQuery:
        def __init__(self):
            self._names = set()

        def filter(self, **kwargs):
            self._names = kwargs.get("username__in", set())
            return self

        def values_list(self, field, flat=False):
            return [id_map[n] for n in self._names if n in id_map]

    monkeypatch.setattr(service_module, "User", SimpleNamespace(objects=_FakeQuery()))


def test_resolve_keeps_numeric_ids(monkeypatch):
    """纯数字项原样保留。"""
    _patch_user(monkeypatch, {})
    assert service_module.resolve_admin_ids({"1", "2"}) == {"1", "2"}


def test_resolve_maps_username_to_id(monkeypatch):
    """用户名项查 User 表转成数字 ID。"""
    _patch_user(monkeypatch, {"admin": 1})
    assert service_module.resolve_admin_ids({"admin"}) == {"1"}


def test_resolve_mixed_ids_and_usernames(monkeypatch):
    """数字 ID 与用户名混合时两者都保留。"""
    _patch_user(monkeypatch, {"admin": 1})
    assert service_module.resolve_admin_ids({"1", "admin"}) == {"1"}


def test_resolve_unknown_username_dropped(monkeypatch):
    """不存在的用户名查不到 ID，被丢弃。"""
    _patch_user(monkeypatch, {})
    assert service_module.resolve_admin_ids({"ghost"}) == set()


def test_resolve_empty(monkeypatch):
    """空白名单返回空集。"""
    _patch_user(monkeypatch, {})
    assert service_module.resolve_admin_ids(set()) == set()


# ═══════════════════════════════════════════════
# claim_wireless_device — 局域网主动连接默认锁定
# ═══════════════════════════════════════════════


def _dev(connection_type: str, locked_by: str = "", added_by: str = "") -> SimpleNamespace:
    """构造带 save 记录的轻量设备对象。"""
    dev = SimpleNamespace(
        connection_type=connection_type,
        locked_by=locked_by,
        added_by=added_by,
        save_calls=[],
    )

    def save(update_fields=None):
        dev.save_calls.append(update_fields)

    dev.save = save
    return dev


def _patch_set_lock(monkeypatch, should_raise: bool = False):
    """替换 set_device_lock 为 spy，返回记录调用与 set locked_by 的行为。"""
    calls = []

    def fake_set_device_lock(dev, locked, user_id):
        if should_raise:
            raise AssertionError("不应调用 set_device_lock")
        calls.append((locked, user_id))
        dev.locked_by = user_id

    monkeypatch.setattr(service_module, "set_device_lock", fake_set_device_lock)
    return calls


def test_claim_locks_and_records_configurer(monkeypatch):
    """WIFI 未锁定 → 默认锁定 + 补记配置者。"""
    calls = _patch_set_lock(monkeypatch)
    dev = _dev("WIFI")
    service_module.claim_wireless_device(dev, "1")
    assert calls == [(True, "1")]
    assert dev.locked_by == "1"
    assert dev.added_by == "1"
    assert dev.save_calls == [["added_by"]]


def test_claim_usb_noop(monkeypatch):
    """USB 设备恒公开，不锁定不记录。"""
    _patch_set_lock(monkeypatch, should_raise=True)
    dev = _dev("USB")
    service_module.claim_wireless_device(dev, "1")
    assert dev.locked_by == ""
    assert dev.added_by == ""
    assert dev.save_calls == []


def test_claim_locked_by_other_untouched(monkeypatch):
    """已被他人锁定的 WIFI 设备保持原状。"""
    _patch_set_lock(monkeypatch, should_raise=True)
    dev = _dev("WIFI", locked_by="2", added_by="2")
    service_module.claim_wireless_device(dev, "1")
    assert dev.locked_by == "2"
    assert dev.added_by == "2"
    assert dev.save_calls == []


def test_claim_anonymous_noop(monkeypatch):
    """匿名（空 user_id）不锁定。"""
    _patch_set_lock(monkeypatch, should_raise=True)
    dev = _dev("WIFI")
    service_module.claim_wireless_device(dev, "")
    assert dev.locked_by == ""
    assert dev.added_by == ""
    assert dev.save_calls == []


def test_claim_existing_public_device_records_configurer(monkeypatch):
    """后台自动发现的公开设备（added_by 空），主动连接后补记配置者并锁定。"""
    calls = _patch_set_lock(monkeypatch)
    dev = _dev("WIFI")
    service_module.claim_wireless_device(dev, "1")
    assert calls == [(True, "1")]
    assert dev.added_by == "1"
