"""Document case CRUD for cm_test_definitions."""

from __future__ import annotations

from typing import Any

from django.db import transaction
from django.utils import timezone

from .api_files import get_file
from .api_ids import allocate_case_id_on_create
from .api_projects import ConflictError, get_project
from .models import BUSINESS_TYPE_CHOICES, TEST_TYPE_CHOICES, TestDefinition

__all__ = [
    "batch_delete_definitions",
    "create_definition",
    "delete_definition",
    "get_definition",
    "serialize_definition",
    "update_definition",
]

_TEST_TYPES = {c[0] for c in TEST_TYPE_CHOICES}
_BUSINESS_TYPES = {c[0] for c in BUSINESS_TYPE_CHOICES}

DISPLAY_TS = "%Y-%m-%d-%H:%M:%S"


def format_display_time(value) -> str:
    if value is None:
        return ""
    if timezone.is_aware(value):
        value = timezone.localtime(value)
    return value.strftime(DISPLAY_TS)


def serialize_definition(obj: TestDefinition) -> dict[str, Any]:
    return {
        "id": obj.id,
        "project_id": obj.project_id,
        "file_id": obj.file_id,
        "directory_id": obj.directory_id,
        "title": obj.title,
        "test_type": obj.test_type,
        "business_type": obj.business_type,
        "module": obj.module,
        "precondition": obj.precondition,
        "steps": obj.steps,
        "expected_result": obj.expected_result,
        "sort_order": obj.sort_order,
        "created_by": obj.created_by,
        "updated_by": obj.updated_by,
        "created_at": format_display_time(obj.created_at),
        "updated_at": format_display_time(obj.updated_at),
        "created_at_iso": obj.created_at.isoformat() if obj.created_at else "",
        "updated_at_iso": obj.updated_at.isoformat() if obj.updated_at else "",
    }


def _owned_case(*, case_id: str, user_id: str) -> TestDefinition:
    obj = (
        TestDefinition.objects.select_related("project", "directory", "file")
        .filter(id=case_id, project__created_by=user_id)
        .first()
    )
    if obj is None:
        raise LookupError("用例不存在")
    return obj


def _validate_enums(test_type: str, business_type: str) -> None:
    if test_type not in _TEST_TYPES:
        raise ValueError("测试类型无效，可选：APP / WEB / API / FUNC")
    if business_type not in _BUSINESS_TYPES:
        raise ValueError("业务类型无效，可选：家电 / 照明 / APP")


def _validate_required(*, title: str, steps: str, expected_result: str) -> None:
    if not (title or "").strip():
        raise ValueError("测试标题不能为空")
    if not (steps or "").strip():
        raise ValueError("执行步骤不能为空")
    if not (expected_result or "").strip():
        raise ValueError("预期结果不能为空")


def create_definition(
    *,
    project_id: int,
    file_id: int,
    user_id: str,
    title: str = "",
    test_type: str = "app",
    business_type: str = "appliance",
    module: str = "",
    precondition: str = "",
    steps: str = "",
    expected_result: str = "",
    sort_order: int = 0,
    require_fields: bool = False,
) -> dict[str, Any]:
    project = get_project(project_id=project_id, user_id=user_id)
    if project is None:
        raise LookupError("项目不存在")
    case_file = get_file(file_id=file_id, user_id=user_id)
    if case_file is None or case_file.project_id != project.id:
        raise LookupError("文件不存在")
    _validate_enums(test_type, business_type)
    if require_fields:
        _validate_required(title=title, steps=steps, expected_result=expected_result)

    def _create(case_id: str) -> TestDefinition:
        return TestDefinition.objects.create(
            id=case_id,
            project=project,
            file=case_file,
            directory_id=case_file.directory_id,
            title=(title or "").strip() or "未命名用例",
            test_type=test_type,
            business_type=business_type,
            module=(module or "").strip(),
            precondition=precondition or "",
            steps=steps or "",
            expected_result=expected_result or "",
            sort_order=sort_order,
            created_by=user_id,
            updated_by=user_id,
        )

    obj = allocate_case_id_on_create(_create)
    return serialize_definition(obj)


def get_definition(*, case_id: str, user_id: str) -> dict[str, Any]:
    return serialize_definition(_owned_case(case_id=case_id, user_id=user_id))


def update_definition(
    *,
    case_id: str,
    user_id: str,
    title: str | None = None,
    test_type: str | None = None,
    business_type: str | None = None,
    module: str | None = None,
    precondition: str | None = None,
    steps: str | None = None,
    expected_result: str | None = None,
    sort_order: int | None = None,
    require_fields: bool = True,
) -> dict[str, Any]:
    obj = _owned_case(case_id=case_id, user_id=user_id)
    if title is not None:
        obj.title = title.strip()
    if test_type is not None:
        obj.test_type = test_type
    if business_type is not None:
        obj.business_type = business_type
    if module is not None:
        obj.module = module.strip()
    if precondition is not None:
        obj.precondition = precondition
    if steps is not None:
        obj.steps = steps
    if expected_result is not None:
        obj.expected_result = expected_result
    if sort_order is not None:
        obj.sort_order = sort_order

    _validate_enums(obj.test_type, obj.business_type)
    if require_fields:
        _validate_required(title=obj.title, steps=obj.steps, expected_result=obj.expected_result)
    obj.updated_by = user_id
    obj.save()
    return serialize_definition(obj)


def delete_definition(*, case_id: str, user_id: str) -> None:
    obj = _owned_case(case_id=case_id, user_id=user_id)
    obj.delete()


def batch_delete_definitions(*, case_ids: list[str], user_id: str) -> dict[str, Any]:
    ids = [str(i) for i in (case_ids or []) if i]
    if not ids:
        raise ValueError("请选择要删除的用例")
    with transaction.atomic():
        qs = TestDefinition.objects.filter(id__in=ids, project__created_by=user_id)
        found = set(qs.values_list("id", flat=True))
        missing = [i for i in ids if i not in found]
        if missing:
            raise ConflictError("部分用例不存在或无权删除")
        deleted, _ = qs.delete()
    return {"deleted": deleted}
