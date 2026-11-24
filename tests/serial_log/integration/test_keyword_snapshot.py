from __future__ import annotations

import importlib
import json

from pathlib import Path

import pytest

from django.apps import apps as django_apps

from backend.apps.serial_log import api
from backend.apps.serial_log.models import LogKeyword

pytestmark = [pytest.mark.django_db, pytest.mark.integration]

REPO_ROOT = Path(__file__).resolve().parents[3]
JSON_CATALOG = REPO_ROOT / "backend" / "config" / "device_log_keywords.json"

snapshot_migration = importlib.import_module(
    "backend.apps.serial_log.migrations.0005_keyword_snapshot"
)


def _expected_from_json() -> list[tuple]:
    data = json.loads(JSON_CATALOG.read_text(encoding="utf-8"))
    return [
        (keyword, item["id"], item["module"], item["feature"])
        for keyword, features in data["keywords"].items()
        for item in features
    ]


def test_snapshot_matches_json_catalog_row_by_row():
    snapshot_migration.forwards(django_apps, None)
    rows = api.list_keyword_rows()
    actual = [(row.keyword, row.feature_id, row.module, row.feature) for row in rows]
    assert actual == _expected_from_json()
    assert all(row.scope == LogKeyword.SCOPE_GENERAL for row in rows)
    assert len({row.keyword for row in rows}) == 67
    assert len({(row.module, row.feature_id, row.feature) for row in rows}) == 56
    assert [row.sort_order for row in rows] == [(i + 1) * 10 for i in range(len(rows))]


def test_forwards_is_idempotent_and_keeps_existing_edits():
    snapshot_migration.forwards(django_apps, None)
    row = LogKeyword.objects.get(keyword="switch_on", feature_id=0, scope="*")
    row.feature = "打开设备成功（维护改）"
    row.save(update_fields=["feature", "updated_at"])
    snapshot_migration.forwards(django_apps, None)
    assert LogKeyword.objects.count() == 70
    assert LogKeyword.objects.get(pk=row.pk).feature == "打开设备成功（维护改）"


def test_forwards_does_not_need_data_file(monkeypatch):
    def _no_read(*args, **kwargs):
        raise AssertionError("迁移不得读取数据文件")

    monkeypatch.setattr(Path, "read_text", _no_read)
    monkeypatch.setattr(Path, "read_bytes", _no_read)
    snapshot_migration.forwards(django_apps, None)
    assert LogKeyword.objects.count() == 70


def test_reverse_empties_table():
    snapshot_migration.forwards(django_apps, None)
    snapshot_migration.backwards(django_apps, None)
    assert LogKeyword.objects.count() == 0
