"""Document case CRUD — rows in ``cm_test_definitions``, steps in ``cm_case_steps``."""

from __future__ import annotations

from typing import Any

from django.db import transaction
from django.utils import timezone

from .api_files import get_file
from .api_ids import allocate_case_id_on_create
from .api_projects import ConflictError, get_project
from .models import (
    BUSINESS_TYPE_CHOICES,
    CASE_TYPE_CHOICES,
    PRIORITY_CHOICES,
    SYSTEM_CHOICES,
    CaseStep,
    TestDefinition,
)

__all__ = [
    "MAX_STEP_TEXT",
    "STEPS_PLACEHOLDER_ASSERTION",
    "batch_delete_definitions",
    "create_definition",
    "delete_definition",
    "get_definition",
    "serialize_definition",
    "update_definition",
]

_SYSTEMS = {c[0] for c in SYSTEM_CHOICES}
_CASE_TYPES = {c[0] for c in CASE_TYPE_CHOICES}
_PRIORITIES = {c[0] for c in PRIORITY_CHOICES}
_BUSINESS_TYPES = {c[0] for c in BUSINESS_TYPE_CHOICES}

DISPLAY_TS = "%Y-%m-%d-%H:%M:%S"

#: 单段动作 / 断言的字符上限（服务端校验，前后端同口径）
MAX_STEP_TEXT = 2000

#: 迁移时给旧用例补的断言占位文案 —— 固定不变，供检索「待补断言」的用例
STEPS_PLACEHOLDER_ASSERTION = "（待补充断言）"


def format_display_time(value) -> str:
    if value is None:
        return ""
    if timezone.is_aware(value):
        value = timezone.localtime(value)
    return value.strftime(DISPLAY_TS)


def serialize_steps(obj: TestDefinition) -> list[dict[str, Any]]:
    """Return the ordered step list of one case（预取命中时不再查库）。"""
    return [
        {"id": step.id, "action": step.action, "assertion": step.assertion}
        for step in obj.steps.all()
    ]


def serialize_definition(obj: TestDefinition) -> dict[str, Any]:
    steps = serialize_steps(obj)
    return {
        "id": obj.id,
        "project_id": obj.project_id,
        "file_id": obj.file_id,
        "directory_id": obj.directory_id,
        "title": obj.title,
        "priority": obj.priority,
        "system": obj.system,
        "case_type": obj.case_type,
        "business_type": obj.business_type,
        "module": obj.module,
        "precondition": obj.precondition,
        "source_case_id": obj.source_case_id,
        "source_task_id": obj.source_task_id,
        "steps": steps,
        "step_count": len(steps),
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


def _normalize_steps(steps: Any) -> list[dict[str, str]]:
    """把入参收敛为 ``[{"action", "assertion"}]``，保持提交顺序。

    Raises:
        ValueError: 入参不是数组，或某一项不是对象。
    """
    if steps is None:
        return []
    if not isinstance(steps, (list, tuple)):
        raise ValueError("执行步骤必须是数组")
    normalized: list[dict[str, str]] = []
    for index, item in enumerate(steps, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"第 {index} 步格式无效")
        normalized.append(
            {
                "action": str(item.get("action") or ""),
                "assertion": str(item.get("assertion") or ""),
            }
        )
    return normalized


def _validate_enums(
    *,
    priority: str,
    system: str,
    case_type: str,
    business_type: str,
) -> None:
    if priority not in _PRIORITIES:
        raise ValueError("优先级无效，可选：P0 / P1 / P2")
    if system not in _SYSTEMS:
        raise ValueError("系统无效，可选：ANDROID / WEB / IOS / API")
    if case_type not in _CASE_TYPES:
        raise ValueError("类型无效，可选：FUNC / AUTO")
    if business_type not in _BUSINESS_TYPES:
        raise ValueError("业务类型无效，可选：家电 / 照明 / APP")


def _validate_required(*, title: str, steps: list[dict[str, Any]]) -> None:
    """校验标题与步骤序列；错误信息带步骤序号，供前端拼「第几行」。

    Raises:
        ValueError: 标题为空、步骤为空、某步动作或断言为空、单段超长。
    """
    if not (title or "").strip():
        raise ValueError("测试标题不能为空")
    if not steps:
        raise ValueError("执行步骤不能为空")
    for index, step in enumerate(steps, start=1):
        action = str(step.get("action") or "")
        assertion = str(step.get("assertion") or "")
        if not action.strip():
            raise ValueError(f"第 {index} 步：动作不能为空")
        if not assertion.strip():
            raise ValueError(f"第 {index} 步：断言不能为空")
        if len(action) > MAX_STEP_TEXT:
            raise ValueError(f"第 {index} 步：动作不能超过 {MAX_STEP_TEXT} 字符")
        if len(assertion) > MAX_STEP_TEXT:
            raise ValueError(f"第 {index} 步：断言不能超过 {MAX_STEP_TEXT} 字符")


def _replace_steps(obj: TestDefinition, steps: list[dict[str, str]]) -> None:
    """整段替换步骤：先清空再按顺序重建，序号由服务端重编号。"""
    obj.steps.all().delete()
    CaseStep.objects.bulk_create(
        [
            CaseStep(
                case=obj,
                sort_order=index,
                action=step["action"],
                assertion=step["assertion"],
            )
            for index, step in enumerate(steps, start=1)
        ]
    )


def create_definition(
    *,
    project_id: int,
    file_id: int,
    user_id: str,
    title: str = "",
    priority: str = "P1",
    system: str = "ANDROID",
    case_type: str = "AUTO",
    business_type: str = "appliance",
    module: str = "",
    precondition: str = "",
    steps: Any = None,
    sort_order: int = 0,
    source_case_id: str = "",
    source_task_id: str = "",
) -> dict[str, Any]:
    project = get_project(project_id=project_id, user_id=user_id)
    if project is None:
        raise LookupError("项目不存在")
    case_file = get_file(file_id=file_id, user_id=user_id)
    if case_file is None or case_file.project_id != project.id:
        raise LookupError("文件不存在")

    normalized = _normalize_steps(steps)
    _validate_enums(
        priority=priority,
        system=system,
        case_type=case_type,
        business_type=business_type,
    )
    _validate_required(title=title, steps=normalized)

    def _create(case_id: str) -> TestDefinition:
        with transaction.atomic():
            obj = TestDefinition.objects.create(
                id=case_id,
                project=project,
                file=case_file,
                directory_id=case_file.directory_id,
                title=(title or "").strip(),
                priority=priority,
                system=system,
                case_type=case_type,
                business_type=business_type,
                module=(module or "").strip(),
                precondition=precondition or "",
                source_case_id=(source_case_id or "").strip(),
                source_task_id=(source_task_id or "").strip(),
                sort_order=sort_order,
                created_by=user_id,
                updated_by=user_id,
            )
            _replace_steps(obj, normalized)
        return obj

    obj = allocate_case_id_on_create(_create)
    return serialize_definition(obj)


def get_definition(*, case_id: str, user_id: str) -> dict[str, Any]:
    return serialize_definition(_owned_case(case_id=case_id, user_id=user_id))


def update_definition(
    *,
    case_id: str,
    user_id: str,
    title: str | None = None,
    priority: str | None = None,
    system: str | None = None,
    case_type: str | None = None,
    business_type: str | None = None,
    module: str | None = None,
    precondition: str | None = None,
    steps: Any = None,
    sort_order: int | None = None,
) -> dict[str, Any]:
    obj = _owned_case(case_id=case_id, user_id=user_id)
    if title is not None:
        obj.title = title.strip()
    if priority is not None:
        obj.priority = priority
    if system is not None:
        obj.system = system
    if case_type is not None:
        obj.case_type = case_type
    if business_type is not None:
        obj.business_type = business_type
    if module is not None:
        obj.module = module.strip()
    if precondition is not None:
        obj.precondition = precondition
    if sort_order is not None:
        obj.sort_order = sort_order

    normalized = _normalize_steps(steps) if steps is not None else None
    _validate_enums(
        priority=obj.priority,
        system=obj.system,
        case_type=obj.case_type,
        business_type=obj.business_type,
    )
    _validate_required(
        title=obj.title,
        steps=normalized if normalized is not None else serialize_steps(obj),
    )

    with transaction.atomic():
        obj.updated_by = user_id
        obj.save()
        if normalized is not None:
            _replace_steps(obj, normalized)
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
