"""device_inspector v1.7 capture 服务单元测试（纯逻辑，无 DB / 无设备 IO）。"""

from types import SimpleNamespace

import pytest

from apps.device_inspector import api as api_module
from apps.device_inspector import service as service_module

pytestmark = [pytest.mark.unit, pytest.mark.device_pool]


def _fake_device(status="ONLINE", occupied_by=""):
    return SimpleNamespace(status=status, occupied_by=occupied_by)


class _FakeDeviceQuery:
    def __init__(self, rows):
        self.rows = rows

    def get(self, **kwargs):
        serial = kwargs.get("serial")
        for r in self.rows:
            if r.serial == serial:
                return r
        raise service_module.CaptureError("设备未注册")  # pragma: no cover


def _patch_device_model(monkeypatch, rows):
    from apps.device_pool import models as dp_models

    monkeypatch.setattr(dp_models, "Device", SimpleNamespace(objects=_FakeDeviceQuery(rows)))


def test_check_device_available_serial_empty():
    with pytest.raises(service_module.CaptureError) as ei:
        service_module._check_device_available("")
    assert "未选择设备" in str(ei.value)


def test_check_device_available_not_registered(monkeypatch):
    from apps.device_pool import models as dp_models

    class _FakeDeviceModel:
        DoesNotExist = Exception

        class objects:  # noqa: N801
            @staticmethod
            def get(**kwargs):
                raise _FakeDeviceModel.DoesNotExist

    monkeypatch.setattr(dp_models, "Device", _FakeDeviceModel)
    with pytest.raises(service_module.CaptureError):
        service_module._check_device_available("NOPE")


def test_ensure_current_device_blocks_execution_occupation(monkeypatch):
    from apps.device_pool import models as dp_models

    dev = _fake_device(status="BUSY", occupied_by="runner-abc")
    dev.serial = "A"

    class _Query:
        def get(self, **kwargs):
            return dev

    monkeypatch.setattr(dp_models, "Device", SimpleNamespace(objects=_Query()))
    with pytest.raises(service_module.CaptureError) as ei:
        service_module.ensure_current_device("A")
    assert "执行引擎" in str(ei.value)


def test_ensure_current_device_switches_when_needed(monkeypatch):
    from apps.device_pool import api as dp_api
    from apps.device_pool import models as dp_models

    dev = _fake_device()
    dev.serial = "B"
    dev.connection_type = "USB"
    dev.connection_addr = ""

    class _Query:
        def get(self, **kwargs):
            return dev

    monkeypatch.setattr(dp_models, "Device", SimpleNamespace(objects=_Query()))
    pool = SimpleNamespace(current_serial="A", switched=None)

    def _switch_to(serial, ct, addr):
        pool.switched = (serial, ct, addr)

    pool.switch_to = _switch_to
    monkeypatch.setattr(dp_api, "device", pool)
    service_module.ensure_current_device("B")
    assert pool.switched == ("B", "USB", "")


def test_snapshot_meta_and_full_dicts():
    snap = SimpleNamespace(
        id=3,
        serial="A",
        method="both",
        package="com.demo",
        activity="Main",
        screen_w=1080,
        screen_h=2340,
        element_count=10,
        actionable_count=8,
        ocr_count=2,
        screenshot_path="inspector/shots/c.png",
        created_by="1",
        created_at=None,
        dump_json={
            "element_count": 10,
            "actionable_count": 8,
            "elements": [{"a": 1}],
            "actionable": [],
        },
        ocr_json={"ocr_count": 2, "texts": []},
    )
    meta = api_module.snapshot_meta_dict(snap)
    assert meta["id"] == 3 and meta["method"] == "both"
    full = api_module.snapshot_to_dict(snap)
    assert full["snapshot_id"] == 3
    assert full["elements"] == [{"a": 1}]
    assert full["texts"] == []
    assert full["ocr_count"] == 2


def test_capture_method_invalid(monkeypatch):
    from apps.device_pool import models as dp_models

    monkeypatch.setattr(dp_models, "Device", SimpleNamespace(objects=_FakeDeviceQuery([])))
    with pytest.raises(service_module.CaptureError) as ei:
        api_module.capture_snapshot("1", "A", method="bogus")
    assert ei.value.status_code == 400
