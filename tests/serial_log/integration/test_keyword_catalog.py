"""
模块功能：➡️ 关键词目录组装（keywords.collect_keywords）集成测试：行序、计数口径、空态 🏁
Python 调试：➡️ python -m pytest -c tests/pytest.ini tests/serial_log/integration/test_keyword_catalog.py 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 覆盖 backend/apps/serial_log
🏁
"""

from __future__ import annotations

import pytest

from backend.apps.serial_log import api, keywords

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def test_empty_table_gives_readable_none():
    payload = keywords.collect_keywords()
    assert payload["origin"] == "none"
    assert payload["keywords"] == []
    assert payload["keyword_count"] == 0
    assert payload["feature_count"] == 0
    assert payload["note"]
    assert payload["updated_at"] == ""


def test_rows_keep_registration_order_and_scope():
    api.upsert_keyword("b_second", module="m", feature="f2", feature_id=1, scope="*")
    api.upsert_keyword("a_first", module="m", feature="f1", feature_id=0, scope="H6601")
    payload = keywords.collect_keywords()
    assert payload["origin"] == "db"
    assert [row["keyword"] for row in payload["keywords"]] == ["b_second", "a_first"]
    assert payload["keywords"][1]["features"][0]["scope"] == "H6601"
    assert payload["updated_at"]


def test_counts_dedupe_by_keyword_and_feature_not_scope():
    # 同关键词同功能点跨两个范围：关键词计 1、功能点计 1
    api.upsert_keyword(
        "switch_on", module="设备开关", feature="打开设备成功", feature_id=0, scope="*"
    )
    api.upsert_keyword(
        "switch_on", module="设备开关", feature="打开设备成功", feature_id=0, scope="H6601"
    )
    # 同关键词挂第二个功能点：关键词仍计 1、功能点计 2
    api.upsert_keyword(
        "switch_on", module="设备开关", feature="打开设备成功（分段）", feature_id=17, scope="*"
    )
    payload = keywords.collect_keywords()
    assert payload["keyword_count"] == 1
    assert payload["feature_count"] == 2
    assert len(payload["keywords"][0]["features"]) == 3


def test_collect_is_read_only():
    api.upsert_keyword("switch_on", module="设备开关", feature="打开设备成功", feature_id=0)
    before = [(row.pk, row.updated_at) for row in api.list_keyword_rows()]
    keywords.collect_keywords()
    keywords.collect_keywords()
    after = [(row.pk, row.updated_at) for row in api.list_keyword_rows()]
    assert before == after
