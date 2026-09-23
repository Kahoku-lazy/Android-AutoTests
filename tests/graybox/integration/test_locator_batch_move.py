"""元素定位批量移动 — 集成测试。

覆盖范围：单件移动的页面同级重名拦截（`move_item`）与批量移动的
去重 / 原子性 / 目标目录校验（`batch_move_items`）。
"""

import pytest

from apps.element_locator import api as el_api
from apps.element_locator.api_projects import ConflictError, ensure_system_projects
from apps.element_locator.models import LocatorDirectory, Page

pytestmark = [pytest.mark.integration, pytest.mark.element_locator, pytest.mark.django_db]


@pytest.fixture
def project():
    return ensure_system_projects()[0]


def _make_dir(project, name, parent=None) -> LocatorDirectory:
    return LocatorDirectory.objects.create(project=project, name=name, parent=parent)


def _make_page(directory, label) -> Page:
    return Page.objects.create(label=label, directory=directory, is_folder=False)


def test_single_page_move_rejects_duplicate_label(project):
    """单件移动：目标目录已有同名页面 → ConflictError，原页面不动。"""
    target = _make_dir(project, "测试目录")
    other = _make_dir(project, "别的目录")
    _make_page(target, "同名页面")
    moving = _make_page(other, "同名页面")

    with pytest.raises(ConflictError):
        el_api.move_item(kind="page", item_id=moving.id, parent_directory_id=target.id)

    moving.refresh_from_db()
    assert moving.directory_id == other.id


def test_batch_move_moves_all_and_reports_count(project):
    """批量移动：全部合法 → 全部落库并返回 moved 数。"""
    target = _make_dir(project, "测试目录")
    first = _make_page(None, "页面A")
    second = _make_page(None, "页面B")

    result = el_api.batch_move_items(
        items=[
            {"kind": "page", "id": first.id},
            {"kind": "page", "id": second.id},
        ],
        parent_directory_id=target.id,
    )

    assert result == {"moved": 2, "skipped": 0}
    first.refresh_from_db()
    second.refresh_from_db()
    assert first.directory_id == target.id
    assert second.directory_id == target.id


def test_batch_move_dedupes_descendant_of_selected_directory(project):
    """目录与其后代同批：后代被去重，随目录一起到达目标目录。"""
    source = _make_dir(project, "来源目录")
    child = _make_page(source, "子页面")
    target = _make_dir(project, "目标目录")

    result = el_api.batch_move_items(
        items=[
            {"kind": "page", "id": child.id},
            {"kind": "directory", "id": source.id},
        ],
        parent_directory_id=target.id,
    )

    assert result == {"moved": 1, "skipped": 1}
    source.refresh_from_db()
    child.refresh_from_db()
    assert source.parent_id == target.id
    assert child.directory_id == source.id


def test_batch_move_is_atomic_when_one_node_is_illegal(project):
    """任一项非法 → 整批回滚，合法项也不落库。"""
    parent = _make_dir(project, "父目录")
    child_dir = _make_dir(project, "子目录", parent=parent)
    moving = _make_page(None, "待移动页面")

    with pytest.raises(ConflictError):
        el_api.batch_move_items(
            items=[
                {"kind": "page", "id": moving.id},
                # 把父目录移入自己的子目录 → 非法，应使整批回滚
                {"kind": "directory", "id": parent.id},
            ],
            parent_directory_id=child_dir.id,
        )

    moving.refresh_from_db()
    parent.refresh_from_db()
    assert moving.directory_id is None
    assert parent.parent_id is None


def test_batch_move_rolls_back_on_duplicate_label(project):
    """批量中的重名同样使整批回滚（不覆盖目标目录既有页面）。"""
    target = _make_dir(project, "目标目录")
    _make_page(target, "同名页面")
    duplicated = _make_page(None, "同名页面")
    innocent = _make_page(None, "无关页面")

    with pytest.raises(ConflictError):
        el_api.batch_move_items(
            items=[
                {"kind": "page", "id": innocent.id},
                {"kind": "page", "id": duplicated.id},
            ],
            parent_directory_id=target.id,
        )

    innocent.refresh_from_db()
    duplicated.refresh_from_db()
    assert innocent.directory_id is None
    assert duplicated.directory_id is None


def test_batch_move_rejects_unknown_target_directory(project):
    """目标目录不存在 → LookupError（视图映射 404）。"""
    page = _make_page(None, "页面")

    with pytest.raises(LookupError):
        el_api.batch_move_items(
            items=[{"kind": "page", "id": page.id}],
            parent_directory_id=999999,
        )

    page.refresh_from_db()
    assert page.directory_id is None


def test_batch_move_rejects_empty_items():
    """空集合 → ValueError（视图映射 400）。"""
    with pytest.raises(ValueError):
        el_api.batch_move_items(items=[], parent_directory_id=None)


def test_batch_move_rejects_invalid_kind(project):
    """未知 kind → ValueError，且不落库。"""
    page = _make_page(None, "页面")

    with pytest.raises(ValueError):
        el_api.batch_move_items(
            items=[{"kind": "folder", "id": page.id}],
            parent_directory_id=None,
        )
