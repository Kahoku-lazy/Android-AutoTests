"""Directory CRUD + move helpers for project trees."""

from __future__ import annotations

from typing import Any

from django.db import IntegrityError, transaction

from .api_projects import ConflictError, get_project
from .models import CaseDirectory, TestDefinition

__all__ = [
    "create_directory",
    "delete_directory",
    "move_item",
    "serialize_directory",
    "update_directory",
]


def serialize_directory(obj: CaseDirectory) -> dict[str, Any]:
    return {
        "id": obj.id,
        "project_id": obj.project_id,
        "parent_id": obj.parent_id,
        "name": obj.name,
        "sort_order": obj.sort_order,
        "created_by": obj.created_by,
        "created_at": obj.created_at.isoformat() if obj.created_at else "",
        "updated_at": obj.updated_at.isoformat() if obj.updated_at else "",
    }


def _owned_directory(*, directory_id: int, user_id: str) -> CaseDirectory:
    obj = (
        CaseDirectory.objects.select_related("project")
        .filter(id=directory_id, project__created_by=user_id)
        .first()
    )
    if obj is None:
        raise LookupError("目录不存在")
    return obj


def create_directory(
    *,
    project_id: int,
    name: str,
    user_id: str,
    parent_id: int | None = None,
    sort_order: int = 0,
) -> dict[str, Any]:
    project = get_project(project_id=project_id, user_id=user_id)
    if project is None:
        raise LookupError("项目不存在")
    name = (name or "").strip()
    if not name:
        raise ValueError("目录名称不能为空")
    parent = None
    if parent_id is not None:
        parent = _owned_directory(directory_id=parent_id, user_id=user_id)
        if parent.project_id != project.id:
            raise ConflictError("父目录不属于该项目")
    try:
        with transaction.atomic():
            obj = CaseDirectory.objects.create(
                project=project,
                parent=parent,
                name=name,
                sort_order=sort_order,
                created_by=user_id,
            )
    except IntegrityError as exc:
        raise ConflictError("同级目录名称已存在") from exc
    return serialize_directory(obj)


def update_directory(
    *,
    directory_id: int,
    user_id: str,
    name: str | None = None,
    sort_order: int | None = None,
) -> dict[str, Any]:
    obj = _owned_directory(directory_id=directory_id, user_id=user_id)
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


def delete_directory(*, directory_id: int, user_id: str) -> None:
    obj = _owned_directory(directory_id=directory_id, user_id=user_id)
    obj.delete()


def _is_descendant(*, ancestor_id: int, candidate_id: int) -> bool:
    """True if candidate_id is ancestor_id or under it."""
    current_id: int | None = candidate_id
    seen: set[int] = set()
    while current_id is not None:
        if current_id == ancestor_id:
            return True
        if current_id in seen:
            return True
        seen.add(current_id)
        current_id = (
            CaseDirectory.objects.filter(id=current_id).values_list("parent_id", flat=True).first()
        )
    return False


def move_item(
    *,
    user_id: str,
    item_type: str,
    item_id: str | int,
    target_directory_id: int | None,
    sort_order: int = 0,
    project_id: int | None = None,
) -> dict[str, Any]:
    """Move a directory or case under ``target_directory_id`` (None = project root)."""
    if item_type == "directory":
        directory = _owned_directory(directory_id=int(item_id), user_id=user_id)
        project = directory.project
        if target_directory_id is not None:
            if target_directory_id == directory.id:
                raise ConflictError("不能将目录移动到自身")
            target = _owned_directory(directory_id=target_directory_id, user_id=user_id)
            if target.project_id != project.id:
                raise ConflictError("不能跨项目移动")
            if _is_descendant(ancestor_id=directory.id, candidate_id=target.id):
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

    if item_type == "file":
        from .api_files import serialize_file
        from .models import CaseFile

        case_file = (
            CaseFile.objects.select_related("project")
            .filter(id=int(item_id), project__created_by=user_id)
            .first()
        )
        if case_file is None:
            raise LookupError("文件不存在")
        if target_directory_id is not None:
            target = _owned_directory(directory_id=target_directory_id, user_id=user_id)
            if target.project_id != case_file.project_id:
                raise ConflictError("不能跨项目移动")
            case_file.directory = target
        else:
            case_file.directory = None
        case_file.sort_order = sort_order
        try:
            case_file.save()
        except IntegrityError as exc:
            raise ConflictError("同目录下文件名已存在") from exc
        TestDefinition.objects.filter(file_id=case_file.id).update(
            directory_id=case_file.directory_id
        )
        return serialize_file(case_file)

    raise ValueError("item_type 必须是 directory 或 file")
