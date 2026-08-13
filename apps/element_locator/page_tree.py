"""页面目录树工具 — 嵌套层级校验（最多 5 层）。

All tree-traversal functions accept an optional parent_map / children_map
to avoid recursive DB queries (N+1). Callers that iterate many pages should
pre-build these maps via build_page_maps().
"""

from __future__ import annotations

from . import api
from .models import Page

MAX_PAGE_TREE_DEPTH = 5


def build_page_maps():
    """Load all pages in one query and return (parent_map, children_map).

    parent_map: {id: parent_id}     — O(1) parent lookup
    children_map: {parent_id: [child_id, ...]}  — O(1) children lookup
    """
    rows = list(Page.objects.values_list("id", "parent_id", "is_folder"))
    parent_map = {}
    children_map = {}
    for pid, parent_id, is_folder in rows:
        parent_map[pid] = parent_id
        children_map.setdefault(parent_id, []).append(pid)
    return parent_map, children_map


def compute_depth(page_id, parent_map):
    """Compute depth of a page using an in-memory parent_map (根节点=1)."""
    depth = 1
    current = parent_map.get(page_id)
    while current is not None:
        depth += 1
        current = parent_map.get(current)
    return depth


def page_depth(page: Page, parent_map: dict | None = None) -> int:
    """根节点深度为 1。"""
    if parent_map is not None:
        return compute_depth(page.id, parent_map)
    depth = 1
    current = page.parent
    while current is not None:
        depth += 1
        current = current.parent
    return depth


def depth_for_parent_id(parent_id: int | None) -> int:
    """新建节点在指定父级下的深度。"""
    if not parent_id:
        return 1
    try:
        parent = Page.objects.get(pk=parent_id)
    except Page.DoesNotExist:
        raise ValueError("父级目录不存在")
    return page_depth(parent) + 1


def validate_parent_and_depth(parent_id: int | None, *, is_folder: bool = False) -> None:
    """目录节点受 5 层限制；页面可作为叶子挂在任意目录下。"""
    if not is_folder:
        return
    if depth_for_parent_id(parent_id) > MAX_PAGE_TREE_DEPTH:
        raise ValueError(f"目录最多嵌套 {MAX_PAGE_TREE_DEPTH} 层")


def sibling_label_exists(label: str, parent_id: int | None, exclude_id: int | None = None) -> bool:
    qs = Page.objects.filter(label=label, parent_id=parent_id)
    if exclude_id:
        qs = qs.exclude(id=exclude_id)
    return qs.exists()


def get_descendant_ids(page_id: int, children_map: dict | None = None) -> set[int]:
    """包含自身在内的所有后代节点 ID。使用 children_map 避免递归 DB 查询。"""
    result = {page_id}
    if children_map is not None:
        stack = [page_id]
        while stack:
            pid = stack.pop()
            for child_id in children_map.get(pid, []):
                if child_id not in result:
                    result.add(child_id)
                    stack.append(child_id)
    else:
        for child_id in Page.objects.filter(parent_id=page_id).values_list("id", flat=True):
            result |= get_descendant_ids(child_id)
    return result


def subtree_max_depth(page_id: int, children_map: dict | None = None) -> int:
    """以 page_id 为根的子树最大相对深度（叶节点为 1）。"""
    if children_map is not None:
        child_ids = children_map.get(page_id, [])
        if not child_ids:
            return 1
        return 1 + max(subtree_max_depth(cid, children_map) for cid in child_ids)
    child_ids = list(Page.objects.filter(parent_id=page_id).values_list("id", flat=True))
    if not child_ids:
        return 1
    return 1 + max(subtree_max_depth(cid) for cid in child_ids)


def validate_move(
    page_id: int,
    new_parent_id: int | None,
    parent_map: dict | None = None,
    children_map: dict | None = None,
) -> None:
    try:
        page = Page.objects.get(pk=page_id)
    except Page.DoesNotExist:
        raise ValueError("页面不存在")

    if new_parent_id == page_id:
        raise ValueError("不能移动到自身")

    if new_parent_id:
        if new_parent_id in get_descendant_ids(page_id, children_map):
            raise ValueError("不能移动到子级目录内")
        try:
            parent = Page.objects.get(pk=new_parent_id)
        except Page.DoesNotExist:
            raise ValueError("父级目录不存在")
        if not parent.is_folder:
            raise ValueError("只能移动到目录下")

    if (page.parent_id or None) == (new_parent_id or None):
        raise ValueError("已在目标位置")

    if sibling_label_exists(page.label, new_parent_id, exclude_id=page_id):
        raise ValueError(f"同级名称「{page.label}」已存在")

    if page.is_folder:
        new_depth = depth_for_parent_id(new_parent_id)
        deepest = new_depth + subtree_max_depth(page_id, children_map) - 1
        if deepest > MAX_PAGE_TREE_DEPTH:
            raise ValueError(f"目录最多嵌套 {MAX_PAGE_TREE_DEPTH} 层")


def move_page(
    page_id: int,
    new_parent_id: int | None,
    parent_map: dict | None = None,
    children_map: dict | None = None,
) -> Page:
    validate_move(page_id, new_parent_id, parent_map, children_map)
    api.update_page_parent(page_id, new_parent_id)
    return Page.objects.get(pk=page_id)


def filter_top_level_page_ids(page_ids: list[int], parent_map: dict | None = None) -> list[int]:
    """批量移动时排除「祖先也在列表中」的节点，避免子项被重复移动脱钩。"""
    id_set = set(page_ids)
    top_level = []

    if parent_map is not None:
        for pid in page_ids:
            ancestor_in_set = False
            current = parent_map.get(pid)
            while current:
                if current in id_set:
                    ancestor_in_set = True
                    break
                current = parent_map.get(current)
            if not ancestor_in_set:
                top_level.append(pid)
        return top_level

    for pid in page_ids:
        page = Page.objects.filter(pk=pid).values("parent_id").first()
        if not page:
            continue
        ancestor_in_set = False
        current = page["parent_id"]
        while current:
            if current in id_set:
                ancestor_in_set = True
                break
            row = Page.objects.filter(pk=current).values("parent_id").first()
            current = row["parent_id"] if row else None
        if not ancestor_in_set:
            top_level.append(pid)
    return top_level


def batch_move_pages(page_ids: list[int], new_parent_id: int | None) -> dict:
    """批量移动页面/目录到目标父级（parent_id=None 表示根目录）。"""
    parent_map, children_map = build_page_maps()
    moved = 0
    errors: list[dict] = []
    for pid in filter_top_level_page_ids(page_ids, parent_map):
        try:
            move_page(pid, new_parent_id, parent_map, children_map)
            moved += 1
        except ValueError as e:
            errors.append({"id": pid, "reason": str(e)})
        except Page.DoesNotExist:
            errors.append({"id": pid, "reason": "页面不存在"})
    return {"moved": moved, "errors": errors}
