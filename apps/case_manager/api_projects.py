"""Project CRUD — write path for cm_case_projects."""

from __future__ import annotations

from typing import Any

from django.db import IntegrityError, transaction

from .models import CaseProject, TestDefinition

__all__ = [
    "ConflictError",
    "create_project",
    "delete_project",
    "get_project",
    "get_project_tree",
    "list_projects",
    "serialize_project",
    "update_project",
]


class ConflictError(Exception):
    """Business conflict (duplicate name, illegal move, etc.)."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def serialize_project(obj: CaseProject) -> dict[str, Any]:
    return {
        "id": obj.id,
        "name": obj.name,
        "description": obj.description,
        "created_by": obj.created_by,
        "created_at": obj.created_at.isoformat() if obj.created_at else "",
        "updated_at": obj.updated_at.isoformat() if obj.updated_at else "",
        "case_count": TestDefinition.objects.filter(project_id=obj.id).count(),
    }


def list_projects(*, user_id: str) -> list[dict[str, Any]]:
    qs = CaseProject.objects.filter(created_by=user_id).order_by("-created_at")
    return [serialize_project(p) for p in qs]


def get_project(*, project_id: int, user_id: str) -> CaseProject | None:
    return CaseProject.objects.filter(id=project_id, created_by=user_id).first()


def create_project(*, name: str, description: str = "", user_id: str) -> dict[str, Any]:
    name = (name or "").strip()
    if not name:
        raise ValueError("项目名称不能为空")
    try:
        with transaction.atomic():
            obj = CaseProject.objects.create(
                name=name,
                description=(description or "").strip(),
                created_by=user_id,
            )
    except IntegrityError as exc:
        raise ConflictError("同名项目已存在") from exc
    return serialize_project(obj)


def update_project(
    *,
    project_id: int,
    user_id: str,
    name: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    obj = get_project(project_id=project_id, user_id=user_id)
    if obj is None:
        raise LookupError("项目不存在")
    if name is not None:
        name = name.strip()
        if not name:
            raise ValueError("项目名称不能为空")
        obj.name = name
    if description is not None:
        obj.description = description.strip()
    try:
        obj.save()
    except IntegrityError as exc:
        raise ConflictError("同名项目已存在") from exc
    return serialize_project(obj)


def delete_project(*, project_id: int, user_id: str) -> None:
    obj = get_project(project_id=project_id, user_id=user_id)
    if obj is None:
        raise LookupError("项目不存在")
    obj.delete()


def _serialize_file_node(case_file) -> dict[str, Any]:
    return {
        "type": "file",
        "id": case_file.id,
        "name": case_file.name,
        "sort_order": case_file.sort_order,
        "updated_at": case_file.updated_at.isoformat() if case_file.updated_at else "",
    }


def _build_dir_node(directory, children_map, files_by_dir) -> dict[str, Any]:
    child_dirs = children_map.get(directory.id, [])
    return {
        "type": "directory",
        "id": directory.id,
        "name": directory.name,
        "sort_order": directory.sort_order,
        "children": [
            *[_build_dir_node(c, children_map, files_by_dir) for c in child_dirs],
            *[_serialize_file_node(f) for f in files_by_dir.get(directory.id, [])],
        ],
    }


def get_project_tree(*, project_id: int, user_id: str) -> dict[str, Any]:
    from .models import CaseFile

    project = get_project(project_id=project_id, user_id=user_id)
    if project is None:
        raise LookupError("项目不存在")

    directories = list(project.directories.all().order_by("sort_order", "id"))
    files = list(CaseFile.objects.filter(project=project).order_by("sort_order", "id"))

    children_map: dict[int | None, list] = {}
    for d in directories:
        children_map.setdefault(d.parent_id, []).append(d)

    files_by_dir: dict[int | None, list] = {}
    for f in files:
        files_by_dir.setdefault(f.directory_id, []).append(f)

    root_dirs = children_map.get(None, [])
    root_files = files_by_dir.get(None, [])
    return {
        "project": serialize_project(project),
        "tree": [
            *[_build_dir_node(d, children_map, files_by_dir) for d in root_dirs],
            *[_serialize_file_node(f) for f in root_files],
        ],
    }
