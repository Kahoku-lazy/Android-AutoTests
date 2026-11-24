"""
模块功能：➡️ 冻结快照一致性与迁移行为（集成）：DB 条目 == JSON 原表、幂等、reverse 可回退 🏁
Python 调试：➡️ python -m pytest -c tests/pytest.ini tests/serial_log/integration/test_keyword_snapshot.py 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 覆盖 backend/apps/serial_log
🏁
"""

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
    """JSON 原表顺序的 (keyword, feature_id, module, feature) 期望序列。"""
    data = json.loads(JSON_CATALOG.read_text(encoding="utf-8"))
    return [
        (keyword, item["id"], item["module"], item["feature"])
        for keyword, features in data["keywords"].items()
        for item in features
    ]


def test_snapshot_matches_json_catalog_row_by_row():
    """迁入后 DB 与 JSON 原表逐行一致：67 关键词 / 70 行 / 56 功能点 / 全通用。"""
    snapshot_migration.forwards(django_apps, None)
    rows = api.list_keyword_rows()
    actual = [(row.keyword, row.feature_id, row.module, row.feature) for row in rows]
    assert actual == _expected_from_json()
    assert all(row.scope == LogKeyword.SCOPE_GENERAL for row in rows)
    assert len({row.keyword for row in rows}) == 67
    assert len({(row.module, row.feature_id, row.feature) for row in rows}) == 56
    # 行序以 10 为步长，保持原表先后
    assert [row.sort_order for row in rows] == [(i + 1) * 10 for i in range(len(rows))]


def test_forwards_is_idempotent_and_keeps_existing_edits():
    """重复执行不产生第二行，也不覆盖已有行的维护改动。"""
    snapshot_migration.forwards(django_apps, None)
    row = LogKeyword.objects.get(keyword="switch_on", feature_id=0, scope="*")
    row.feature = "打开设备成功（维护改）"
    row.save(update_fields=["feature", "updated_at"])
    snapshot_migration.forwards(django_apps, None)
    assert LogKeyword.objects.count() == 70
    assert LogKeyword.objects.get(pk=row.pk).feature == "打开设备成功（维护改）"


def test_forwards_does_not_need_data_file(monkeypatch):
    """全新安装不依赖数据文件：禁止任何 Path 文本读取后仍能迁入（冻结字面量）。"""

    def _no_read(*args, **kwargs):
        raise AssertionError("迁移不得读取数据文件")

    monkeypatch.setattr(Path, "read_text", _no_read)
    monkeypatch.setattr(Path, "read_bytes", _no_read)
    snapshot_migration.forwards(django_apps, None)
    assert LogKeyword.objects.count() == 70


def test_reverse_empties_table():
    """reverse 清空本表行（表本身由 0004 的 reverse 删除）。"""
    snapshot_migration.forwards(django_apps, None)
    snapshot_migration.backwards(django_apps, None)
    assert LogKeyword.objects.count() == 0
