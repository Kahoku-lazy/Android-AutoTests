"""关键词对照表写库口（api.py）集成测试：并集口径、upsert 唯一键、续编与行序。

覆盖规格 serial-log-module「串口日志拥有关键词对照表数据」：
通用对所有型号生效、专用是增量不覆盖通用、重复登记不产生第二行、
mapping 可注入 engines 的 KeywordIndex。
"""

from __future__ import annotations

import pytest

from backend.apps.serial_log import api
from backend.apps.serial_log.models import LogKeyword
from engines.device.logbus import KeywordIndex

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def _seed_general(keyword="switch_on", feature_id=0, feature="打开设备成功"):
    """登记一条通用条目。"""
    return api.upsert_keyword(
        keyword, module="设备开关", feature=feature, feature_id=feature_id, scope="*"
    )


def test_general_applies_to_every_sku():
    _seed_general()
    for sku in ["H6601", "H2234", "", "*"]:
        mapping = api.keyword_mapping_for_sku(sku)
        assert mapping["switch_on"] == [{"id": 0, "module": "设备开关", "feature": "打开设备成功"}]


def test_sku_specific_is_additive_union():
    _seed_general()
    api.upsert_keyword(
        "h6601_boot", module="设备开关", feature="H6601开机完成", feature_id=56, scope="H6601"
    )
    h6601 = api.keyword_mapping_for_sku("H6601")
    assert set(h6601) == {"switch_on", "h6601_boot"}
    assert set(api.keyword_mapping_for_sku("H2234")) == {"switch_on"}
    assert set(api.keyword_mapping_for_sku("")) == {"switch_on"}


def test_specific_does_not_override_general():
    _seed_general()
    api.upsert_keyword(
        "switch_on", module="设备开关", feature="H6601打开设备成功", feature_id=0, scope="H6601"
    )
    mapping = api.keyword_mapping_for_sku("H6601")
    features = [item["feature"] for item in mapping["switch_on"]]
    assert features == ["打开设备成功", "H6601打开设备成功"]  # 通用仍在，专用追加
    assert len(mapping["switch_on"]) == 2


def test_upsert_same_unique_key_updates_not_duplicates():
    _seed_general()
    api.upsert_keyword(
        "switch_on", module="设备开关", feature="打开设备成功（改）", feature_id=0, scope="*"
    )
    assert LogKeyword.objects.count() == 1
    assert LogKeyword.objects.get().feature == "打开设备成功（改）"


def test_feature_id_auto_continues_and_sort_order_appends():
    _seed_general(feature_id=7)
    row = api.upsert_keyword("new_kw", module="新模块", feature="新功能")
    assert row.feature_id == 8
    assert row.scope == "*"
    first = LogKeyword.objects.order_by("sort_order").first()
    assert row.sort_order == first.sort_order + 10


def test_list_keyword_rows_keeps_registration_order():
    _seed_general(keyword="a_first", feature_id=0)
    api.upsert_keyword("b_second", module="m", feature="f", feature_id=1)
    rows = api.list_keyword_rows()
    assert [row.keyword for row in rows] == ["a_first", "b_second"]


def test_delete_keyword():
    row = _seed_general()
    assert api.delete_keyword(row.pk) is True
    assert api.delete_keyword(row.pk) is False
    assert LogKeyword.objects.count() == 0


def test_mapping_injectable_into_keyword_index():
    _seed_general()
    api.upsert_keyword(
        "h6601_boot", module="设备开关", feature="H6601开机完成", feature_id=56, scope="H6601"
    )
    index = KeywordIndex(api.keyword_mapping_for_sku("H6601"))
    hits = index.match("[light_switch][I]: h6601_boot done")
    assert [keyword for keyword, _ in hits] == ["h6601_boot"]
    assert hits[0][1][0]["id"] == 56
    # 其它型号看不到专用词
    other = KeywordIndex(api.keyword_mapping_for_sku("H2234"))
    assert other.match("h6601_boot") == []
