from __future__ import annotations

from typing import Any

from django.db import IntegrityError, transaction
from django.db.models import Count

from utils.logs import backend_log

from .models import LIBRARY_AUTOMATION, LIBRARY_FUNCTIONAL, LIBRARY_KIND_CHOICES, CaseProject

__all__ = [
    "ConflictError",
    "create_project",
    "delete_project",
    "get_project",
    "list_projects",
    "serialize_project",
    "update_project",
]

_KINDS = {item[0] for item in LIBRARY_KIND_CHOICES}


class ConflictError(Exception):
    def __init__(self, message: str):
        self.log = backend_log
        self.message = message
        super().__init__(message)


def _case_count(obj: CaseProject) -> int:
    annotated = getattr(obj, "case_count", None)
    if annotated is not None:
        return int(annotated)
    if obj.library_kind == LIBRARY_AUTOMATION:
        return obj.automation_cases.count()
    return obj.functional_cases.count()


def serialize_project(obj: CaseProject) -> dict[str, Any]:
    return {
        "id": obj.id,
        "name": obj.name,
        "description": obj.description,
        "library_kind": obj.library_kind,
        "created_by": obj.created_by,
        "created_at": obj.created_at.isoformat() if obj.created_at else "",
        "updated_at": obj.updated_at.isoformat() if obj.updated_at else "",
        "case_count": _case_count(obj),
        "case_limit": 999,
    }


def list_projects(*, user_id: str) -> list[dict[str, Any]]:
    qs = (
        CaseProject.objects.filter(created_by=user_id)
        .annotate(case_count=Count("automation_cases") + Count("functional_cases"))
        .order_by("-created_at")
    )
    return [serialize_project(obj) for obj in qs]


def get_project(*, project_id: int, user_id: str) -> CaseProject | None:
    return CaseProject.objects.filter(id=project_id, created_by=user_id).first()


def create_project(
    *,
    name: str,
    library_kind: str,
    description: str = "",
    user_id: str,
) -> dict[str, Any]:
    name = (name or "").strip()
    if not name:
        raise ValueError("项目名称不能为空")
    if library_kind not in _KINDS:
        raise ValueError("库类型无效，可选：automation / functional")
    try:
        with transaction.atomic():
            obj = CaseProject.objects.create(
                name=name,
                description=(description or "").strip(),
                library_kind=library_kind,
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
    library_kind: str | None = None,
) -> dict[str, Any]:
    obj = get_project(project_id=project_id, user_id=user_id)
    if obj is None:
        raise LookupError("项目不存在")
    if library_kind is not None and library_kind != obj.library_kind:
        raise ConflictError("库类型创建后不可修改")
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


def project_case_model(project: CaseProject):
    from .models import AutomationCase, FunctionalCase

    if project.library_kind == LIBRARY_AUTOMATION:
        return AutomationCase
    if project.library_kind == LIBRARY_FUNCTIONAL:
        return FunctionalCase
    raise ValueError("库类型无效")
