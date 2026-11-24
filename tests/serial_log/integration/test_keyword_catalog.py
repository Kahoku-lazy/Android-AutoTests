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
    api.upsert_keyword(
        "switch_on", module="设备开关", feature="打开设备成功", feature_id=0, scope="*"
    )
    api.upsert_keyword(
        "switch_on", module="设备开关", feature="打开设备成功", feature_id=0, scope="H6601"
    )
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
