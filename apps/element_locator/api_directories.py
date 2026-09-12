"""Locator directory CRUD + move + batch-delete files."""

from __future__ import annotations

from typing import Any

from django.db import IntegrityError, transaction

from .api_projects import ConflictError, get_project_by_code
from .models import ApiEndpoint, LocatorDirectory, Page, WebElement

__all__ = [
    "batch_delete_files",
    "create_directory",
    "delete_directory",
    "move_item",
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
    obj = _get_directory(directory_id=directory_id)
    obj.delete()


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
            LocatorDirectory.objects.filter(id=current_id).values_list("parent_id", flat=True).first()
        )
    return False


def _resolve_target_directory(*, project_id: int, target_directory_id: int | None) -> LocatorDirectory | None:
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
    """Move directory or leaf file. kind: directory|page|web_element|api_endpoint."""
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
        page.directory = _resolve_target_directory(
            project_id=project.id, target_directory_id=parent_directory_id
        )
        page.save(update_fields=["directory"])
        return {"kind": "page", "id": page.id, "directory_id": page.directory_id}

    if kind == "web_element":
        el = WebElement.objects.filter(id=item_id).first()
        if el is None:
            raise LookupError("Web 元素不存在")
        project = get_project_by_code(code="web")
        if project is None:
            raise LookupError("项目不存在")
        el.directory = _resolve_target_directory(
            project_id=project.id, target_directory_id=parent_directory_id
        )
        el.save(update_fields=["directory"])
        return {"kind": "web_element", "id": el.id, "directory_id": el.directory_id}

    if kind == "api_endpoint":
        ep = ApiEndpoint.objects.filter(id=item_id).first()
        if ep is None:
            raise LookupError("API 端点不存在")
        project = get_project_by_code(code="api")
        if project is None:
            raise LookupError("项目不存在")
        ep.directory = _resolve_target_directory(
            project_id=project.id, target_directory_id=parent_directory_id
        )
        ep.save(update_fields=["directory"])
        return {"kind": "api_endpoint", "id": ep.id, "directory_id": ep.directory_id}

    raise ValueError("kind 必须是 directory / page / web_element / api_endpoint")


def batch_delete_files(*, kind: str, ids: list[int]) -> dict[str, Any]:
    if not ids:
        raise ValueError("ids 不能为空")
    if kind == "page":
        deleted, _ = Page.objects.filter(id__in=ids, is_folder=False).delete()
    elif kind == "web_element":
        deleted, _ = WebElement.objects.filter(id__in=ids).delete()
    elif kind == "api_endpoint":
        deleted, _ = ApiEndpoint.objects.filter(id__in=ids).delete()
    else:
        raise ValueError("kind 必须是 page / web_element / api_endpoint")
    return {"kind": kind, "deleted": deleted}
