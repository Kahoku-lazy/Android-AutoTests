"""
模块功能：➡️ 关键词维护写库口（create_keyword / update_keyword）集成测试 🏁
Python 调试：➡️ python -m pytest -c tests/pytest.ini tests/serial_log/integration/test_keyword_crud.py 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 覆盖 backend/apps/serial_log
🏁
"""

from __future__ import annotations

import pytest

from backend.apps.serial_log import api
from backend.apps.serial_log.models import LogKeyword

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def _create(keyword="switch_on", **kwargs):
    """新建一条通用条目（默认字段齐全）。"""
    defaults = {"module": "设备开关", "feature": "打开设备成功", "feature_id": 0}
    defaults.update(kwargs)
    return api.create_keyword(keyword, **defaults)


def test_create_defaults_general_and_continues_numbering():
    _create(feature_id=7)
    row = api.create_keyword("new_kw", module="新模块", feature="新功能")
    assert row.scope == "*"
    assert row.feature_id == 8
    first = LogKeyword.objects.order_by("sort_order").first()
    assert row.sort_order == first.sort_order + 10


def test_create_duplicate_unique_key_rejected():
    _create()
    with pytest.raises(ValueError, match="已登记"):
        _create()
    assert LogKeyword.objects.count() == 1


def test_create_same_keyword_different_scope_allowed():
    _create()
    row = _create(scope="H6601")
    assert row.scope == "H6601"
    assert LogKeyword.objects.count() == 2


@pytest.mark.parametrize(
    ("field", "value"),
    [("keyword", "  "), ("module", ""), ("feature", None)],
)
def test_create_requires_nonempty_texts(field, value):
    texts = {"keyword": "switch_on", "module": "m", "feature": "f"}
    texts[field] = value
    with pytest.raises(ValueError):
        api.create_keyword(texts["keyword"], module=texts["module"], feature=texts["feature"])


def test_update_partial_only_changes_given_fields():
    row = _create()
    updated = api.update_keyword(row.pk, feature="打开设备成功（改）")
    assert updated.feature == "打开设备成功（改）"
    assert (updated.keyword, updated.module, updated.scope, updated.sort_order) == (
        row.keyword,
        row.module,
        row.scope,
        row.sort_order,
    )


def test_update_collision_guard_keeps_both_rows():
    first = _create(keyword="a", feature_id=0)
    second = _create(keyword="b", feature_id=1)
    with pytest.raises(ValueError, match="已被其它条目登记"):
        api.update_keyword(second.pk, keyword="a", feature_id=0)
    assert LogKeyword.objects.get(pk=first.pk).keyword == "a"
    assert LogKeyword.objects.get(pk=second.pk).keyword == "b"


def test_update_same_key_on_self_is_allowed():
    row = _create()
    updated = api.update_keyword(
        row.pk, keyword=row.keyword, feature_id=row.feature_id, feature="改"
    )
    assert updated.feature == "改"


def test_update_unknown_row_rejected():
    with pytest.raises(ValueError, match="不存在"):
        api.update_keyword(999999, feature="x")


def test_update_without_fields_rejected():
    row = _create()
    with pytest.raises(ValueError, match="未提供任何更新字段"):
        api.update_keyword(row.pk)


def test_update_validates_scope_and_texts():
    row = _create()
    with pytest.raises(ValueError, match="范围"):
        api.update_keyword(row.pk, scope="H6601专用")
    with pytest.raises(ValueError, match="关键词"):
        api.update_keyword(row.pk, keyword="   ")


def test_delete_keyword_returns_bool():
    row = _create()
    assert api.delete_keyword(row.pk) is True
    assert api.delete_keyword(row.pk) is False
