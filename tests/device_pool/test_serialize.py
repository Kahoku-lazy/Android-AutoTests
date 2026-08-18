"""usernames_by_ids / device_to_dict 用户名转换单元测试（PRD §5.2 展示层）。"""

from types import SimpleNamespace

import pytest

from apps.device_pool import service as service_module

pytestmark = [pytest.mark.unit, pytest.mark.device_pool]


# ═══════════════════════════════════════════════
# usernames_by_ids — ID → 用户名映射
# ═══════════════════════════════════════════════


def _patch_user_by_ids(monkeypatch, users: list[tuple]):
    """用 fake User.objects 替换，users 为 (id, username) 列表。"""

    class _FakeQuery:
        def filter(self, **kwargs):
            ids = {str(x) for x in kwargs.get("id__in", [])}
            return [
                SimpleNamespace(id=uid, username=uname) for uid, uname in users if str(uid) in ids
            ]

    monkeypatch.setattr(service_module, "User", SimpleNamespace(objects=_FakeQuery()))


def test_usernames_by_ids_maps_ids(monkeypatch):
    """数字 ID 映射为用户名。"""
    _patch_user_by_ids(monkeypatch, [(1, "admin"), (2, "kahoku")])
    assert service_module.usernames_by_ids({"1", "2"}) == {"1": "admin", "2": "kahoku"}


def test_usernames_by_ids_skips_non_digit(monkeypatch):
    """非数字项（历史遗留用户名）跳过，不参与查询。"""
    _patch_user_by_ids(monkeypatch, [(1, "admin")])
    assert service_module.usernames_by_ids({"1", "admin"}) == {"1": "admin"}


def test_usernames_by_ids_empty(monkeypatch):
    """空集合返回空映射。"""
    _patch_user_by_ids(monkeypatch, [])
    assert service_module.usernames_by_ids(set()) == {}


def test_usernames_by_ids_unknown_id_dropped(monkeypatch):
    """不存在的 ID 查不到，不在映射中。"""
    _patch_user_by_ids(monkeypatch, [(1, "admin")])
    assert service_module.usernames_by_ids({"999"}) == {}


# ═══════════════════════════════════════════════
# device_to_dict — 展示层用户名转换
# ═══════════════════════════════════════════════


def _dev(**overrides) -> SimpleNamespace:
    base = dict(
        id=1,
        serial="W1",
        name="",
        model="",
        brand="",
        screen_w=1080,
        screen_h=2400,
        status="ONLINE",
        connection_type="WIFI",
        connection_addr="",
        locked_by="",
        locked_at=None,
        occupied_by="",
        occupied_at=None,
        connected_at=None,
        added_by="",
        last_seen=None,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_device_to_dict_resolves_usernames():
    """传入映射时 locked_by/added_by 显示用户名。"""
    dev = _dev(locked_by="1", added_by="1")
    result = service_module.device_to_dict(dev, None, {"1": "admin"})
    assert result["locked_by"] == "admin"
    assert result["added_by"] == "admin"


def test_device_to_dict_falls_back_to_raw_id():
    """不传映射时回退原始数字 ID。"""
    dev = _dev(locked_by="1", added_by="1")
    result = service_module.device_to_dict(dev, None)
    assert result["locked_by"] == "1"
    assert result["added_by"] == "1"


def test_device_to_dict_usb_locked_by_always_empty():
    """USB 设备 locked_by 恒为空（即使映射存在）。"""
    dev = _dev(connection_type="USB", locked_by="1")
    result = service_module.device_to_dict(dev, None, {"1": "admin"})
    assert result["locked_by"] == ""
