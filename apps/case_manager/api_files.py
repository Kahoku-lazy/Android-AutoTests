"""Case file (sheet) CRUD — tree leaf that owns Excel rows."""

from __future__ import annotations

from typing import Any

from django.db import IntegrityError, transaction

from .api_projects import ConflictError, get_project
from .models import CaseDirectory, CaseFile, TestDefinition

__all__ = [
    "create_file",
    "delete_file",
    "get_file",
    "get_file_sheet",
    "list_file_cases",
    "serialize_file",
    "update_file",
]


def serialize_file(obj: CaseFile) -> dict[str, Any]:
    return {
        "id": obj.id,
        "project_id": obj.project_id,
        "directory_id": obj.directory_id,
        "name": obj.name,
        "sort_order": obj.sort_order,
        "created_by": obj.created_by,
        "created_at": obj.created_at.isoformat() if obj.created_at else "",
        "updated_at": obj.updated_at.isoformat() if obj.updated_at else "",
        "case_count": TestDefinition.objects.filter(file_id=obj.id).count(),
    }


def get_file(*, file_id: int, user_id: str) -> CaseFile | None:
    return (
        CaseFile.objects.select_related("project", "directory")
        .filter(id=file_id, project__created_by=user_id)
        .first()
    )


def create_file(
    *,
    project_id: int,
    name: str,
    user_id: str,
    directory_id: int | None = None,
    sort_order: int = 0,
) -> dict[str, Any]:
    project = get_project(project_id=project_id, user_id=user_id)
    if project is None:
        raise LookupError("项目不存在")
    name = (name or "").strip()
    if not name:
        raise ValueError("文件名称不能为空")
    directory = None
    if directory_id is not None:
        directory = CaseDirectory.objects.filter(
            id=directory_id,
            project_id=project.id,
            project__created_by=user_id,
        ).first()
        if directory is None:
            raise LookupError("目录不存在")
    try:
        with transaction.atomic():
            obj = CaseFile.objects.create(
                project=project,
                directory=directory,
                name=name,
                sort_order=sort_order,
                created_by=user_id,
            )
    except IntegrityError as exc:
        raise ConflictError("同目录下文件名已存在") from exc
    return serialize_file(obj)


def update_file(
    *,
    file_id: int,
    user_id: str,
    name: str | None = None,
    sort_order: int | None = None,
) -> dict[str, Any]:
    obj = get_file(file_id=file_id, user_id=user_id)
    if obj is None:
        raise LookupError("文件不存在")
    if name is not None:
        name = name.strip()
        if not name:
            raise ValueError("文件名称不能为空")
        obj.name = name
    if sort_order is not None:
        obj.sort_order = sort_order
    try:
        obj.save()
    except IntegrityError as exc:
        raise ConflictError("同目录下文件名已存在") from exc
    return serialize_file(obj)


def delete_file(*, file_id: int, user_id: str) -> None:
    obj = get_file(file_id=file_id, user_id=user_id)
    if obj is None:
        raise LookupError("文件不存在")
    obj.delete()


def list_file_cases(*, file_id: int, user_id: str) -> list:
    from .api_definitions import serialize_definition

    obj = get_file(file_id=file_id, user_id=user_id)
    if obj is None:
        raise LookupError("文件不存在")
    rows = obj.cases.all().order_by("sort_order", "id")
    return [serialize_definition(c) for c in rows]


def get_file_sheet(*, file_id: int, user_id: str) -> dict[str, Any]:
    obj = get_file(file_id=file_id, user_id=user_id)
    if obj is None:
        raise LookupError("文件不存在")
    return {
        "file": serialize_file(obj),
        "rows": list_file_cases(file_id=file_id, user_id=user_id),
    }
