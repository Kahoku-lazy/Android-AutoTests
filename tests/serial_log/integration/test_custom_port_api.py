from __future__ import annotations

import pytest

from backend.apps.serial_log import api
from backend.apps.serial_log.models import LogPort
from engines.device.logbus import LogSourceSpec

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def test_ensure_creates_config_rows_with_origin():
    rows = api.ensure_log_ports([LogSourceSpec(port=7005, sku="H6810", baud=921600)])
    assert [row.port for row in rows] == [7005]
    assert rows[0].origin == LogPort.ORIGIN_CONFIG
    assert rows[0].enabled is True


def test_ensure_refreshes_three_cols_but_not_switch():
    api.ensure_log_ports([LogSourceSpec(port=7005, sku="H6810", baud=921600)])
    api.set_log_port_enabled(7005, False)
    api.ensure_log_ports([LogSourceSpec(port=7005, sku="H6810-V2", baud=115200)])
    row = LogPort.objects.get(port=7005)
    assert (row.sku, row.baud, row.enabled) == ("H6810-V2", 115200, False)


def test_ensure_does_not_touch_custom_rows():
    api.create_custom_port(7008, "H717D", 115200)
    api.set_log_port_enabled(7008, False)
    rows = api.ensure_log_ports([LogSourceSpec(port=7008, sku="OTHER", baud=9600)])
    assert rows == []
    row = LogPort.objects.get(port=7008)
    assert (row.sku, row.baud, row.enabled, row.origin) == (
        "H717D",
        115200,
        False,
        LogPort.ORIGIN_CUSTOM,
    )


def test_ensure_skips_config_port_owned_by_custom_and_warns(monkeypatch):
    api.create_custom_port(7008, "H717D", 115200)
    warnings: list[str] = []
    monkeypatch.setattr(
        api.backend_log, "warning", lambda msg, *args: warnings.append(msg % args if args else msg)
    )
    api.ensure_log_ports([LogSourceSpec(port=7008, sku="OTHER", baud=9600)])
    assert any("7008" in item and "custom" in item for item in warnings)
    assert LogPort.objects.get(port=7008).sku == "H717D"


def test_create_custom_port_defaults_and_duplicate_guard():
    row = api.create_custom_port(7008, "H717D", 115200)
    assert (row.origin, row.enabled) == (LogPort.ORIGIN_CUSTOM, True)
    with pytest.raises(ValueError, match="7008"):
        api.create_custom_port(7008, "X", 9600)
    api.ensure_log_ports([LogSourceSpec(port=7005, sku="H6810", baud=921600)])
    with pytest.raises(ValueError, match="7005"):
        api.create_custom_port(7005, "X", 9600)


def test_update_custom_port_rejects_config_row():
    api.ensure_log_ports([LogSourceSpec(port=7005, sku="H6810", baud=921600)])
    with pytest.raises(ValueError, match="7005"):
        api.update_custom_port(7005, sku="X")
    api.create_custom_port(7008, "H717D", 115200)
    row = api.update_custom_port(7008, sku="H717D-V2", baud=460800)
    assert (row.sku, row.baud) == ("H717D-V2", 460800)


def test_delete_custom_port_keeps_config_row():
    api.ensure_log_ports([LogSourceSpec(port=7005, sku="H6810", baud=921600)])
    api.create_custom_port(7008, "H717D", 115200)
    assert api.delete_custom_port(7005) is False
    assert LogPort.objects.filter(port=7005).exists()
    assert api.delete_custom_port(7008) is True
    assert not LogPort.objects.filter(port=7008).exists()


def test_list_custom_port_specs_sorted():
    api.create_custom_port(7009, "B", 9600)
    api.create_custom_port(7008, "A", 115200)
    api.ensure_log_ports([LogSourceSpec(port=7005, sku="H6810", baud=921600)])
    specs = api.list_custom_port_specs()
    assert [(s.port, s.sku) for s in specs] == [(7008, "A"), (7009, "B")]


def test_set_enabled_preserves_custom_origin_and_cols():
    api.create_custom_port(7008, "H717D", 115200)
    api.set_log_port_enabled(7008, False)
    row = LogPort.objects.get(port=7008)
    assert (row.origin, row.sku, row.baud, row.enabled) == (
        LogPort.ORIGIN_CUSTOM,
        "H717D",
        115200,
        False,
    )
