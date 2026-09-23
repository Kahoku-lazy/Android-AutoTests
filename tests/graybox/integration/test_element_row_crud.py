"""元素行增删改 — 集成测试。

钉住三件事：收敛后的可编辑四项可更新（越界字段一律被拒）；新增是 create-only（缺必填 400 /
撞唯一约束 409，坐标仍作为去重键解析入库）；批量删除原子（空集合 400 / 不存在 404）。
"""

import pytest

from apps.element_locator import api as el_api
from apps.element_locator.api_projects import ConflictError
from apps.element_locator.models import Element, Page

pytestmark = [pytest.mark.integration, pytest.mark.element_locator, pytest.mark.django_db]


@pytest.fixture
def page():
    return Page.objects.create(label="页面A", is_folder=False)


def _make_element(page, resource_id="com.demo:id/title", bounds="[0,0][10,10]") -> Element:
    return Element.objects.create(page=page, resource_id=resource_id, bounds=bounds)


def test_update_persists_editable_fields(page):
    """呈现列里可编辑的四项更新后持久化；人工主定位标记为不稳定。"""
    element = _make_element(page)

    el_api.update_element(
        element.id,
        {
            "alias": "标题",
            "text_val": "登录",
            "primary_xpath": "//android.widget.TextView[@text='登录']",
            "is_test_point": True,
        },
    )

    element.refresh_from_db()
    assert element.alias == "标题"
    assert element.text_val == "登录"
    assert element.primary_xpath == "//android.widget.TextView[@text='登录']"
    assert element.primary_stable is False
    assert element.is_test_point is True


def test_update_rejects_out_of_scope_fields(page):
    """收敛后不再可写的字段逐个被拒，且库中值不变。"""
    element = _make_element(page)

    for field, value in (
        ("bounds", "[10,20][110,220]"),
        ("class_name", "android.widget.Button"),
        ("content_desc", "描述"),
        ("resource_id", "com.demo:id/new"),
        ("xpath_candidates", "[]"),
        ("depth", 3),
    ):
        with pytest.raises(ValueError):
            el_api.update_element(element.id, {field: value})

    element.refresh_from_db()
    assert element.bounds == "[0,0][10,10]"
    assert element.class_name == ""
    assert element.content_desc == ""
    assert element.resource_id == "com.demo:id/title"
    assert element.xpath_candidates == "[]"


def test_update_rejects_empty_primary_xpath(page):
    """空的主定位表达式 → ValueError，库中保持原值。"""
    element = _make_element(page)

    with pytest.raises(ValueError):
        el_api.update_element(element.id, {"primary_xpath": "   "})

    element.refresh_from_db()
    assert element.primary_xpath == ""


def test_update_rejects_unknown_field(page):
    """白名单外字段 → ValueError（不静默丢弃）。"""
    element = _make_element(page)

    with pytest.raises(ValueError):
        el_api.update_element(element.id, {"page_id": 1})


def test_update_missing_element_raises_lookup(page):
    """元素不存在 → LookupError（视图映射 404）。"""
    with pytest.raises(LookupError):
        el_api.update_element(999999, {"alias": "x"})


def test_create_element_success(page):
    """新增一行：元素名称 + resource-id 即可，元素计数同步。"""
    element = el_api.create_element(
        page,
        {"alias": "新元素", "resource_id": "com.demo:id/new", "text_val": "文本"},
    )

    assert element.id is not None
    page.refresh_from_db()
    assert page.element_count == 1


def test_create_element_parses_bounds_into_coordinates(page):
    """新增仍接受坐标作为去重键，并按 [x1,y1][x2,y2] 解析坐标分量。"""
    element = el_api.create_element(page, {"alias": "带坐标", "bounds": "[10,20][110,220]"})

    assert (element.bounds, element.x, element.y, element.width, element.height) == (
        "[10,20][110,220]",
        10,
        20,
        100,
        200,
    )


def test_create_element_rejects_invalid_bounds(page):
    """坐标格式非法 → ValueError。"""
    with pytest.raises(ValueError):
        el_api.create_element(page, {"alias": "坏坐标", "bounds": "abc"})


def test_create_element_rejects_out_of_scope_field(page):
    """新增也不再接受类名一类已收敛字段。"""
    with pytest.raises(ValueError):
        el_api.create_element(
            page,
            {"alias": "x", "resource_id": "id/x", "class_name": "android.widget.Button"},
        )


def test_create_element_rejects_missing_alias(page):
    """元素名称必填。"""
    with pytest.raises(ValueError):
        el_api.create_element(page, {"resource_id": "com.demo:id/new"})


def test_create_element_requires_identity(page):
    """resource-id 与 bounds 至少填一个。"""
    with pytest.raises(ValueError):
        el_api.create_element(page, {"alias": "新元素"})


def test_create_element_rejects_duplicate(page):
    """同页相同 (resource_id, bounds) → ConflictError，不覆盖既有行。"""
    existing = _make_element(page, resource_id="com.demo:id/dup", bounds="[0,0][10,10]")

    with pytest.raises(ConflictError):
        el_api.create_element(
            page,
            {"alias": "重复", "resource_id": "com.demo:id/dup", "bounds": "[0,0][10,10]"},
        )

    assert Element.objects.filter(page=page).count() == 1
    existing.refresh_from_db()
    assert existing.alias == ""


def test_delete_elements_removes_rows_and_updates_count(page):
    """批量删除：返回条数并回写页面元素计数。"""
    first = _make_element(page, resource_id="a", bounds="[0,0][1,1]")
    second = _make_element(page, resource_id="b", bounds="[0,0][2,2]")
    keep = _make_element(page, resource_id="c", bounds="[0,0][3,3]")

    result = el_api.delete_elements([first.id, second.id])

    assert result == {"deleted": 2}
    assert list(Element.objects.filter(page=page).values_list("id", flat=True)) == [keep.id]
    page.refresh_from_db()
    assert page.element_count == 1


def test_delete_elements_rejects_empty(page):
    """空集合 → ValueError（视图映射 400）。"""
    with pytest.raises(ValueError):
        el_api.delete_elements([])


def test_delete_elements_missing_id_keeps_everything(page):
    """含不存在的 id → LookupError，整批不落库。"""
    element = _make_element(page)

    with pytest.raises(LookupError):
        el_api.delete_elements([element.id, 999999])

    assert Element.objects.filter(id=element.id).exists()
