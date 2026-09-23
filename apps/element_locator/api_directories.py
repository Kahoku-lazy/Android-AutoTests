"""Locator directory CRUD + move + batch-delete files."""

from __future__ import annotations

from typing import Any

from django.db import IntegrityError, transaction

from .api_projects import ConflictError, get_project_by_code
from .models import Element, LocatorDirectory, Page

__all__ = [
    "batch_delete_files",
    "batch_delete_items",
    "batch_move_items",
    "create_directory",
    "delete_directory",
    "move_item",
    "optional_directory_id",
    "serialize_directory",
    "update_directory",
]


def serialize_directory(obj: LocatorDirectory) -> dict[str, Any]:
    return {
        "id": obj.id,
        "project_id": obj.project_id,
        "project_code": obj.project.code if obj.project_id else "",
        "parent_id": obj.parent_id,
        "name": obj.name,
        "sort_order": obj.sort_order,
        "created_at": obj.created_at.isoformat() if obj.created_at else "",
        "updated_at": obj.updated_at.isoformat() if obj.updated_at else "",
    }


def optional_directory_id(data: dict, *, project_code: str) -> int | None:
    """从请求体解析可选的 directory_id，并校验它属于 project_code。

    返回 None 表示未提供（含 "" / 0 / "0"）；目录不存在或不属于该项目时抛 ValueError。
    （自 views.py 迁入：web 元素与 API 端点两处创建共用，故归目录域而非任一张视图片。）
    """
    raw = data.get("directory_id")
    if raw in (None, "", 0, "0"):
        return None
    try:
        dir_id = int(raw)
    except (TypeError, ValueError):
        return None
    if not LocatorDirectory.objects.filter(id=dir_id, project__code=project_code).exists():
        raise ValueError("目录不存在或不属于当前项目")
    return dir_id


def _get_directory(*, directory_id: int) -> LocatorDirectory:
    obj = LocatorDirectory.objects.select_related("project").filter(id=directory_id).first()
    if obj is None:
        raise LookupError("目录不存在")
    return obj


def create_directory(
    *,
    project_code: str,
    name: str,
    parent_id: int | None = None,
    sort_order: int = 0,
) -> dict[str, Any]:
    project = get_project_by_code(code=project_code)
    if project is None:
        raise LookupError("项目不存在")
    name = (name or "").strip()
    if not name:
        raise ValueError("目录名称不能为空")
    parent = None
    if parent_id is not None:
        parent = _get_directory(directory_id=parent_id)
        if parent.project_id != project.id:
            raise ConflictError("父目录不属于该项目")
    try:
        with transaction.atomic():
            obj = LocatorDirectory.objects.create(
                project=project,
                parent=parent,
                name=name,
                sort_order=sort_order,
            )
    except IntegrityError as exc:
        raise ConflictError("同级目录名称已存在") from exc
    return serialize_directory(obj)


def update_directory(
    *,
    directory_id: int,
    name: str | None = None,
    sort_order: int | None = None,
) -> dict[str, Any]:
    obj = _get_directory(directory_id=directory_id)
    if name is not None:
        name = name.strip()
        if not name:
            raise ValueError("目录名称不能为空")
        obj.name = name
    if sort_order is not None:
        obj.sort_order = sort_order
    try:
        obj.save()
    except IntegrityError as exc:
        raise ConflictError("同级目录名称已存在") from exc
    return serialize_directory(obj)


def delete_directory(*, directory_id: int) -> None:
    """删除目录及其整棵子树（子目录 + 其下页面 + 元素），原子。

    页面不会被目录外键带走（Page.directory 是 SET_NULL），故必须先显式删除页面，
    否则它们会浮回项目根；元素随 Element.page 的 CASCADE 一并删除。
    """
    obj = _get_directory(directory_id=directory_id)
    parent_map = _directory_parent_map(project_id=obj.project_id)
    subtree_ids = _directory_subtree_ids(
        root_id=obj.id, children_map=_children_by_parent(parent_map)
    )
    with transaction.atomic():
        Page.objects.filter(directory_id__in=subtree_ids, is_folder=False).delete()
        LocatorDirectory.objects.filter(id__in=subtree_ids).delete()


def _is_descendant(*, ancestor_id: int, candidate_id: int) -> bool:
    current_id: int | None = candidate_id
    seen: set[int] = set()
    while current_id is not None:
        if current_id == ancestor_id:
            return True
        if current_id in seen:
            return True
        seen.add(current_id)
        current_id = (
            LocatorDirectory.objects.filter(id=current_id)
            .values_list("parent_id", flat=True)
            .first()
        )
    return False


def _resolve_target_directory(
    *, project_id: int, target_directory_id: int | None
) -> LocatorDirectory | None:
    if target_directory_id is None:
        return None
    target = _get_directory(directory_id=target_directory_id)
    if target.project_id != project_id:
        raise ConflictError("不能跨项目移动")
    return target


def move_item(
    *,
    kind: str,
    item_id: int,
    parent_directory_id: int | None = None,
    sort_order: int = 0,
) -> dict[str, Any]:
    """Move directory or leaf file. kind: directory|page."""
    if kind == "directory":
        directory = _get_directory(directory_id=item_id)
        if parent_directory_id is not None:
            if parent_directory_id == directory.id:
                raise ConflictError("不能将目录移动到自身")
            target = _resolve_target_directory(
                project_id=directory.project_id, target_directory_id=parent_directory_id
            )
            if target and _is_descendant(ancestor_id=directory.id, candidate_id=target.id):
                raise ConflictError("不能将目录移动到其子目录下")
            directory.parent = target
        else:
            directory.parent = None
        directory.sort_order = sort_order
        try:
            directory.save()
        except IntegrityError as exc:
            raise ConflictError("同级目录名称已存在") from exc
        return serialize_directory(directory)

    if kind == "page":
        page = Page.objects.filter(id=item_id, is_folder=False).first()
        if page is None:
            raise LookupError("页面不存在")
        project = get_project_by_code(code="android")
        if project is None:
            raise LookupError("项目不存在")
        target = _resolve_target_directory(
            project_id=project.id, target_directory_id=parent_directory_id
        )
        # 页面没有数据库唯一约束兜底，移动前显式挡同级重名（根为 directory_id IS NULL）
        duplicated = (
            Page.objects.filter(
                label=page.label,
                directory_id=target.id if target else None,
                is_folder=False,
            )
            .exclude(id=page.id)
            .exists()
        )
        if duplicated:
            raise ConflictError(f"目标位置已存在同名页面「{page.label}」")
        page.directory = target
        page.save(update_fields=["directory"])
        return {"kind": "page", "id": page.id, "directory_id": page.directory_id}

    raise ValueError("kind 必须是 directory / page")


def _directory_parent_map(*, project_id: int) -> dict[int, int | None]:
    """项目内目录的 {id: parent_id}（一次查询，供祖先 / 子树计算复用）。"""
    return dict(
        LocatorDirectory.objects.filter(project_id=project_id).values_list("id", "parent_id")
    )


def _children_by_parent(parent_map: dict[int, int | None]) -> dict[int | None, list[int]]:
    """由 {id: parent_id} 反转为 {parent_id: [id, ...]}。"""
    children: dict[int | None, list[int]] = {}
    for dir_id, parent_id in parent_map.items():
        children.setdefault(parent_id, []).append(dir_id)
    return children


def _directory_chain(directory_id: int | None, parent_map: dict[int, int | None]) -> set[int]:
    """目录自身及其全部祖先 id（parent_map 为一次性查询构建的 {id: parent_id}）。"""
    chain: set[int] = set()
    current = directory_id
    while current is not None and current not in chain:
        chain.add(current)
        current = parent_map.get(current)
    return chain


def _directory_subtree_ids(*, root_id: int, children_map: dict[int | None, list[int]]) -> set[int]:
    """以 root_id 为根的目录子树 id（含自身）。"""
    result: set[int] = set()
    stack = [root_id]
    while stack:
        current = stack.pop()
        if current in result:
            continue
        result.add(current)
        stack.extend(children_map.get(current, []))
    return result


def batch_move_items(
    *,
    items: list[dict[str, Any]],
    parent_directory_id: int | None = None,
) -> dict[str, Any]:
    """批量移动目录/页面到目标目录（None = 项目根），全有或全无。

    items: [{"kind": "directory"|"page", "id": int}, ...]
    祖先已在本批集合中的后代不再单独落库（移动祖先已一并带走）。
    """
    if not items:
        raise ValueError("节点集合不能为空")
    project = get_project_by_code(code="android")
    if project is None:
        raise LookupError("项目不存在")
    _resolve_target_directory(project_id=project.id, target_directory_id=parent_directory_id)

    normalized: list[tuple[str, int]] = []
    seen: set[tuple[str, int]] = set()
    for raw in items:
        body = raw or {}
        kind = str(body.get("kind") or "")
        if kind not in ("directory", "page"):
            raise ValueError("kind 必须是 directory / page")
        try:
            item_id = int(body.get("id"))
        except (TypeError, ValueError):
            raise ValueError("节点 id 必须是整数") from None
        if (kind, item_id) not in seen:
            seen.add((kind, item_id))
            normalized.append((kind, item_id))

    parent_map = _directory_parent_map(project_id=project.id)
    selected_dir_ids = {item_id for kind, item_id in normalized if kind == "directory"}
    page_dir_map = dict(
        Page.objects.filter(
            id__in=[item_id for kind, item_id in normalized if kind == "page"],
            is_folder=False,
        ).values_list("id", "directory_id")
    )

    effective: list[tuple[str, int]] = []
    for kind, item_id in normalized:
        if kind == "directory":
            covered = bool((_directory_chain(item_id, parent_map) - {item_id}) & selected_dir_ids)
        else:
            directory_id = page_dir_map.get(item_id)
            covered = directory_id is not None and bool(
                _directory_chain(directory_id, parent_map) & selected_dir_ids
            )
        if not covered:
            effective.append((kind, item_id))

    with transaction.atomic():
        for kind, item_id in effective:
            move_item(kind=kind, item_id=item_id, parent_directory_id=parent_directory_id)
    return {"moved": len(effective), "skipped": len(normalized) - len(effective)}


def batch_delete_items(*, items: list[dict[str, Any]]) -> dict[str, Any]:
    """批量删除目录/页面（原子）；目录连同其子树内的目录、页面与元素一并删除。

    items: [{"kind": "directory"|"page", "id": int}, ...]
    祖先已在本批集合中的后代不再重复处理；
    返回顶层节点数（deleted）、实际删除的页面数（pages）与元素数（elements）。
    """
    if not items:
        raise ValueError("节点集合不能为空")
    project = get_project_by_code(code="android")
    if project is None:
        raise LookupError("项目不存在")

    normalized: list[tuple[str, int]] = []
    seen: set[tuple[str, int]] = set()
    for raw in items:
        body = raw or {}
        kind = str(body.get("kind") or "")
        if kind not in ("directory", "page"):
            raise ValueError("kind 必须是 directory / page")
        try:
            item_id = int(body.get("id"))
        except (TypeError, ValueError):
            raise ValueError("节点 id 必须是整数") from None
        if (kind, item_id) not in seen:
            seen.add((kind, item_id))
            normalized.append((kind, item_id))

    parent_map = _directory_parent_map(project_id=project.id)
    children_map = _children_by_parent(parent_map)
    requested_dir_ids = {item_id for kind, item_id in normalized if kind == "directory"}
    requested_page_ids = {item_id for kind, item_id in normalized if kind == "page"}
    if requested_dir_ids - set(parent_map):
        raise LookupError("目录不存在")
    page_dir_map = dict(
        Page.objects.filter(id__in=requested_page_ids, is_folder=False).values_list(
            "id", "directory_id"
        )
    )
    if requested_page_ids - set(page_dir_map):
        raise LookupError("页面不存在")

    directory_ids: set[int] = set()
    page_ids: set[int] = set()
    effective = 0
    for kind, item_id in normalized:
        if kind == "directory":
            covered = bool((_directory_chain(item_id, parent_map) - {item_id}) & requested_dir_ids)
            if covered:
                continue
            directory_ids |= _directory_subtree_ids(root_id=item_id, children_map=children_map)
        else:
            directory_id = page_dir_map.get(item_id)
            covered = directory_id is not None and bool(
                _directory_chain(directory_id, parent_map) & requested_dir_ids
            )
            if covered:
                continue
            page_ids.add(item_id)
        effective += 1

    affected_page_ids = page_ids | set(
        Page.objects.filter(directory_id__in=directory_ids, is_folder=False).values_list(
            "id", flat=True
        )
    )
    element_count = Element.objects.filter(page_id__in=affected_page_ids).count()
    page_count = len(affected_page_ids)
    with transaction.atomic():
        if affected_page_ids:
            Page.objects.filter(id__in=affected_page_ids).delete()
        if directory_ids:
            LocatorDirectory.objects.filter(id__in=directory_ids).delete()
    return {"deleted": effective, "pages": page_count, "elements": element_count}


def batch_delete_files(*, kind: str, ids: list[int]) -> dict[str, Any]:
    if not ids:
        raise ValueError("ids 不能为空")
    if kind == "page":
        deleted, _ = Page.objects.filter(id__in=ids, is_folder=False).delete()
    else:
        raise ValueError("kind 必须是 page")
    return {"kind": kind, "deleted": deleted}
