"""元素定位批量删除与目录级联删除 — 集成测试。

钉住两件事：删目录必须连同子树内的页面与元素一起删（页面不得浮回项目根）；
批量删除的顶层节点 / 页面 / 元素计数与祖先去重口径。
"""

import pytest

from apps.element_locator import api as el_api
from apps.element_locator.api_projects import ensure_system_projects
from apps.element_locator.models import Element, LocatorDirectory, Page

pytestmark = [pytest.mark.integration, pytest.mark.element_locator, pytest.mark.django_db]


@pytest.fixture
def project():
    return ensure_system_projects()[0]


def _make_dir(project, name, parent=None) -> LocatorDirectory:
    return LocatorDirectory.objects.create(project=project, name=name, parent=parent)


def _make_page(directory, label) -> Page:
    return Page.objects.create(label=label, directory=directory, is_folder=False)


def _make_element(page, index: int) -> Element:
    return Element.objects.create(
        page=page,
        resource_id=f"com.demo:id/row{index}",
        bounds=f"[0,{index}][10,{index + 10}]",
    )


def test_delete_directory_removes_whole_subtree(project):
    """删目录：子目录与其下页面、元素一并删除，页面不得浮回项目根。"""
    root_dir = _make_dir(project, "测试目录")
    child_dir = _make_dir(project, "子目录", parent=root_dir)
    page_in_root = _make_page(root_dir, "根页面")
    page_in_child = _make_page(child_dir, "子页面")
    _make_element(page_in_root, 1)
    _make_element(page_in_child, 2)

    el_api.delete_directory(directory_id=root_dir.id)

    assert not LocatorDirectory.objects.filter(id__in=[root_dir.id, child_dir.id]).exists()
    assert not Page.objects.filter(id__in=[page_in_root.id, page_in_child.id]).exists()
    assert Element.objects.count() == 0
    # 关键断言：不得出现「目录没了、页面浮回项目根」
    assert not Page.objects.filter(label__in=["根页面", "子页面"]).exists()


def test_batch_delete_counts_pages_and_elements(project):
    """批量删除：返回顶层节点数、页面数与元素数。"""
    first = _make_page(None, "页面A")
    second = _make_page(None, "页面B")
    for index in range(3):
        _make_element(second, index)

    result = el_api.batch_delete_items(
        items=[
            {"kind": "page", "id": first.id},
            {"kind": "page", "id": second.id},
        ]
    )

    assert result == {"deleted": 2, "pages": 2, "elements": 3}
    assert Page.objects.count() == 0
    assert Element.objects.count() == 0


def test_batch_delete_directory_counts_subtree(project):
    """批量删除目录：页面与元素计数覆盖整棵子树。"""
    directory = _make_dir(project, "待删目录")
    child = _make_dir(project, "子目录", parent=directory)
    page_a = _make_page(directory, "页面A")
    page_b = _make_page(child, "页面B")
    _make_element(page_a, 1)
    _make_element(page_b, 2)
    _make_element(page_b, 3)

    result = el_api.batch_delete_items(items=[{"kind": "directory", "id": directory.id}])

    assert result == {"deleted": 1, "pages": 2, "elements": 3}
    assert Page.objects.count() == 0
    assert LocatorDirectory.objects.count() == 0


def test_batch_delete_dedupes_descendant_of_selected_directory(project):
    """目录与其后代同批：只按目录删一次，计数不重复。"""
    directory = _make_dir(project, "目录A")
    child_page = _make_page(directory, "子页面")

    result = el_api.batch_delete_items(
        items=[
            {"kind": "page", "id": child_page.id},
            {"kind": "directory", "id": directory.id},
        ]
    )

    assert result == {"deleted": 1, "pages": 1, "elements": 0}
    assert Page.objects.count() == 0
    assert LocatorDirectory.objects.count() == 0


def test_batch_delete_rejects_unknown_page_without_deleting(project):
    """任一项非法（页面不存在）→ 整批不落库。"""
    page = _make_page(None, "保留页面")

    with pytest.raises(LookupError):
        el_api.batch_delete_items(
            items=[
                {"kind": "page", "id": page.id},
                {"kind": "page", "id": 999999},
            ]
        )

    assert Page.objects.filter(id=page.id).exists()


def test_batch_delete_rejects_unknown_directory(project):
    """目录不存在 → LookupError，且不改动任何数据。"""
    page = _make_page(None, "保留页面")

    with pytest.raises(LookupError):
        el_api.batch_delete_items(
            items=[
                {"kind": "page", "id": page.id},
                {"kind": "directory", "id": 999999},
            ]
        )

    assert Page.objects.filter(id=page.id).exists()


def test_batch_delete_rejects_empty_items():
    """空集合 → ValueError（视图映射 400）。"""
    with pytest.raises(ValueError):
        el_api.batch_delete_items(items=[])


def test_batch_delete_rejects_invalid_kind(project):
    """未知 kind → ValueError，且不改动任何数据。"""
    page = _make_page(None, "保留页面")

    with pytest.raises(ValueError):
        el_api.batch_delete_items(items=[{"kind": "folder", "id": page.id}])

    assert Page.objects.filter(id=page.id).exists()
