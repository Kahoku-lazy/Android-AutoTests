from __future__ import annotations

from typing import Any

import yaml

from django.db import transaction

from .api_ids import allocate_case_id_on_create
from .api_projects import ConflictError, get_project, project_case_model
from .models import (
    BUSINESS_TYPE_CHOICES,
    CASE_ROW_LIMIT,
    LIBRARY_AUTOMATION,
    PRIORITY_CHOICES,
    SYSTEM_CHOICES,
    AutomationCase,
    AutomationStep,
    CaseProject,
    CaseSheetView,
    FunctionalStep,
)

__all__ = [
    "CASE_ROW_LIMIT",
    "compile_automation_cases",
    "create_row",
    "delete_row",
    "get_sheet",
    "import_yaml_text",
    "list_automation_projects",
    "save_sheet_view",
    "update_row",
]

_SYSTEMS = {item[0] for item in SYSTEM_CHOICES}
_PRIORITIES = {item[0] for item in PRIORITY_CHOICES}
_BUSINESS = {item[0] for item in BUSINESS_TYPE_CHOICES}
MAX_STEP_TEXT = 2000
_VIEW_COLUMNS = {
    "id",
    "priority",
    "system",
    "business_type",
    "module",
    "title",
    "precondition",
    "steps",
    "updated_at",
}
_GROUP_FIELDS = {"", "module", "priority", "system", "business_type"}


def _step_model(project: CaseProject):
    if project.library_kind == LIBRARY_AUTOMATION:
        return AutomationStep
    return FunctionalStep


def _serialize_steps(obj, project: CaseProject) -> list[dict[str, Any]]:
    rows = []
    for step in obj.steps.all():
        item = {
            "id": step.id,
            "action": step.action,
            "assertion": step.assertion,
        }
        if project.library_kind == LIBRARY_AUTOMATION:
            item["anchor"] = step.anchor or {}
            item["log"] = step.log or {}
        rows.append(item)
    return rows


def serialize_row(obj, project: CaseProject) -> dict[str, Any]:
    steps = _serialize_steps(obj, project)
    return {
        "id": obj.id,
        "project_id": obj.project_id,
        "title": obj.title,
        "priority": obj.priority,
        "system": obj.system,
        "business_type": obj.business_type,
        "module": obj.module,
        "precondition": obj.precondition,
        "source_case_id": obj.source_case_id,
        "source_task_id": obj.source_task_id,
        "steps": steps,
        "step_count": len(steps),
        "sort_order": obj.sort_order,
        "updated_at": obj.updated_at.isoformat() if obj.updated_at else "",
    }


def _owned_row(*, project: CaseProject, case_id: str):
    model = project_case_model(project)
    obj = model.objects.filter(id=case_id, project=project).first()
    if obj is None:
        raise LookupError("用例不存在")
    return obj


def _parse_hints(anchor: object, log: object, *, where: str) -> tuple[dict, dict]:
    if anchor in (None, "", {}):
        parsed_anchor: dict[str, str] = {}
    elif not isinstance(anchor, dict):
        raise ValueError(f"{where}：页面锚点必须是对象")
    else:
        unknown = set(anchor) - {"page", "entry", "target"}
        if unknown:
            raise ValueError(f"{where}：页面锚点含未知键")
        parsed_anchor = {}
        for key in ("page", "entry", "target"):
            if key in anchor and anchor[key] not in (None, ""):
                value = str(anchor[key]).strip()
                if len(value) > 120:
                    raise ValueError(f"{where}：页面锚点不能超过 120 字")
                parsed_anchor[key] = value
    if log in (None, "", {}):
        return parsed_anchor, {}
    if not isinstance(log, dict):
        raise ValueError(f"{where}：日志证据必须是对象")
    sku = str(log.get("sku") or "").strip()
    if not sku:
        raise ValueError(f"{where}：日志证据缺少 sku")
    port = log.get("port")
    if isinstance(port, bool) or not isinstance(port, int) or port < 1:
        raise ValueError(f"{where}：日志证据的 port 必须是正整数")
    keywords = log.get("keywords")
    if keywords is None and log.get("keyword"):
        keywords = [log.get("keyword")]
    if not isinstance(keywords, list) or not 1 <= len(keywords) <= 6:
        raise ValueError(f"{where}：日志关键词必须是 1 至 6 个")
    clean = []
    for word in keywords:
        text = str(word or "").strip()
        if not text or any(
            ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-"
            for ch in text
        ):
            raise ValueError(f"{where}：日志关键词字符非法")
        clean.append(text)
    return parsed_anchor, {"sku": sku, "port": port, "keywords": clean}


def _normalize_steps(steps: Any, *, allow_hints: bool) -> list[dict[str, Any]]:
    if not isinstance(steps, list) or not steps:
        raise ValueError("执行步骤不能为空")
    normalized = []
    for index, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            raise ValueError(f"第 {index} 步必须是对象")
        action = str(step.get("action") or "")
        assertion = str(step.get("assertion") or "")
        if not action.strip():
            raise ValueError(f"第 {index} 步：动作不能为空")
        if not assertion.strip():
            raise ValueError(f"第 {index} 步：断言不能为空")
        if len(action) > MAX_STEP_TEXT or len(assertion) > MAX_STEP_TEXT:
            raise ValueError(f"第 {index} 步：动作或断言不能超过 {MAX_STEP_TEXT} 字符")
        has_hint = "anchor" in step or "log" in step
        if has_hint and not allow_hints:
            raise ValueError(f"第 {index} 步：功能用例不接受执行提示")
        anchor, log = ({}, {})
        if allow_hints and has_hint:
            anchor, log = _parse_hints(step.get("anchor"), step.get("log"), where=f"第 {index} 步")
        item = {"action": action, "assertion": assertion}
        if allow_hints:
            item["anchor"] = anchor
            item["log"] = log
        normalized.append(item)
    return normalized


def _validate_enums(*, priority: str, system: str, business_type: str) -> None:
    if priority not in _PRIORITIES:
        raise ValueError("优先级无效，可选：P0 / P1 / P2")
    if system not in _SYSTEMS:
        raise ValueError("系统无效，可选：ANDROID / WEB / IOS / API")
    if business_type not in _BUSINESS:
        raise ValueError("业务类型无效，可选：家电 / 照明 / APP")


def _lock_count(project: CaseProject) -> int:
    CaseProject.objects.select_for_update().get(pk=project.pk)
    return project_case_model(project).objects.filter(project=project).count()


def _replace_steps(obj, project: CaseProject, steps: list[dict[str, Any]]) -> None:
    step_model = _step_model(project)
    obj.steps.all().delete()
    payload = []
    for index, step in enumerate(steps, start=1):
        fields = {
            "case": obj,
            "sort_order": index,
            "action": step["action"],
            "assertion": step["assertion"],
        }
        if project.library_kind == LIBRARY_AUTOMATION:
            fields["anchor"] = step.get("anchor") or {}
            fields["log"] = step.get("log") or {}
        payload.append(step_model(**fields))
    step_model.objects.bulk_create(payload)


def _visible_project(*, project_id: int, user_id: str) -> CaseProject:
    del user_id
    project = CaseProject.objects.filter(id=project_id).first()
    if project is None:
        raise LookupError("项目不存在")
    return project


def get_sheet(*, project_id: int, user_id: str) -> dict[str, Any]:
    project = _visible_project(project_id=project_id, user_id=user_id)
    model = project_case_model(project)
    rows = list(
        model.objects.filter(project=project).prefetch_related("steps").order_by("sort_order", "id")
    )
    view = CaseSheetView.objects.filter(project=project, user_id=user_id).first()
    return {
        "project": {
            "id": project.id,
            "name": project.name,
            "library_kind": project.library_kind,
            "case_count": len(rows),
            "case_limit": CASE_ROW_LIMIT,
        },
        "rows": [serialize_row(row, project) for row in rows],
        "view": view.payload if view else default_view(),
    }


def create_row(
    *,
    project_id: int,
    user_id: str,
    title: str,
    priority: str = "P1",
    system: str = "ANDROID",
    business_type: str = "appliance",
    module: str = "",
    precondition: str = "",
    steps: Any = None,
    source_case_id: str = "",
    source_task_id: str = "",
) -> dict[str, Any]:
    project = get_project(project_id=project_id, user_id=user_id)
    if project is None:
        raise LookupError("项目不存在")
    _validate_enums(priority=priority, system=system, business_type=business_type)
    normalized = _normalize_steps(steps, allow_hints=project.library_kind == LIBRARY_AUTOMATION)
    if not str(title or "").strip():
        raise ValueError("测试标题不能为空")
    model = project_case_model(project)

    def _create(case_id: str):
        with transaction.atomic():
            if _lock_count(project) >= CASE_ROW_LIMIT:
                raise ConflictError(f"一个项目最多 {CASE_ROW_LIMIT} 条")
            obj = model.objects.create(
                id=case_id,
                project=project,
                title=title.strip(),
                priority=priority,
                system=system,
                business_type=business_type,
                module=(module or "").strip(),
                precondition=precondition or "",
                source_case_id=(source_case_id or "").strip(),
                source_task_id=(source_task_id or "").strip(),
                sort_order=_lock_count(project),
                created_by=user_id,
                updated_by=user_id,
            )
            _replace_steps(obj, project, normalized)
            return obj

    return serialize_row(allocate_case_id_on_create(_create), project)


def update_row(*, project_id: int, case_id: str, user_id: str, **fields: Any) -> dict[str, Any]:
    project = get_project(project_id=project_id, user_id=user_id)
    if project is None:
        raise LookupError("项目不存在")
    obj = _owned_row(project=project, case_id=case_id)
    for key in ("title", "priority", "system", "business_type", "module", "precondition"):
        if key in fields and fields[key] is not None:
            setattr(obj, key, str(fields[key]).strip() if key != "precondition" else fields[key])
    _validate_enums(priority=obj.priority, system=obj.system, business_type=obj.business_type)
    steps = fields.get("steps")
    normalized = None
    if steps is not None:
        normalized = _normalize_steps(steps, allow_hints=project.library_kind == LIBRARY_AUTOMATION)
    if not obj.title.strip():
        raise ValueError("测试标题不能为空")
    with transaction.atomic():
        obj.updated_by = user_id
        obj.save()
        if normalized is not None:
            _replace_steps(obj, project, normalized)
    return serialize_row(obj, project)


def delete_row(*, project_id: int, case_id: str, user_id: str) -> None:
    project = get_project(project_id=project_id, user_id=user_id)
    if project is None:
        raise LookupError("项目不存在")
    _owned_row(project=project, case_id=case_id).delete()


def default_view() -> dict[str, Any]:
    return {
        "hidden_columns": [],
        "filters": {},
        "sort": {"field": "sort_order", "direction": "asc"},
        "group_by": "",
    }


def save_sheet_view(*, project_id: int, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    project = _visible_project(project_id=project_id, user_id=user_id)
    if not isinstance(payload, dict):
        raise ValueError("视图必须是对象")
    hidden = payload.get("hidden_columns") or []
    if not isinstance(hidden, list) or any(item not in _VIEW_COLUMNS for item in hidden):
        raise ValueError("隐藏列含未登记字段")
    filters = payload.get("filters") or {}
    if not isinstance(filters, dict) or any(key not in _VIEW_COLUMNS for key in filters):
        raise ValueError("筛选含未登记字段")
    group_by = str(payload.get("group_by") or "")
    if group_by not in _GROUP_FIELDS:
        raise ValueError("分组字段未登记")
    sort = payload.get("sort") or {"field": "sort_order", "direction": "asc"}
    if not isinstance(sort, dict) or sort.get("field") not in _VIEW_COLUMNS | {"sort_order"}:
        raise ValueError("排序字段未登记")
    if sort.get("direction") not in {"asc", "desc"}:
        raise ValueError("排序方向无效")
    clean = {
        "hidden_columns": hidden,
        "filters": {key: str(value) for key, value in filters.items()},
        "sort": {"field": sort["field"], "direction": sort["direction"]},
        "group_by": group_by,
    }
    view, _ = CaseSheetView.objects.update_or_create(
        project=project,
        user_id=user_id,
        defaults={"payload": clean},
    )
    return view.payload


def _parse_case_yaml(text: str) -> list[dict[str, Any]]:
    try:
        raw = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ValueError(f"不是合法 YAML：{exc}") from exc
    if isinstance(raw, dict) and "name" in raw and "steps" in raw and "title" not in raw:
        raise ValueError("这是里程碑格式，请到任务里上传，不能导入用例表")
    rows = raw if isinstance(raw, list) else [raw]
    if not rows or not all(isinstance(item, dict) for item in rows):
        raise ValueError("YAML 根节点必须是用例列表或单条用例")
    return rows


def import_yaml_text(*, project_id: int, user_id: str, text: str) -> dict[str, Any]:
    project = get_project(project_id=project_id, user_id=user_id)
    if project is None:
        raise LookupError("项目不存在")
    parsed = _parse_case_yaml(text)
    prepared = []
    for index, row in enumerate(parsed, start=1):
        try:
            title = str(row.get("title") or "").strip()
            if not title:
                raise ValueError("测试标题不能为空")
            priority = str(row.get("priority") or "P1")
            system = str(row.get("system") or "ANDROID")
            business = str(row.get("business_type") or row.get("business") or "appliance")
            _validate_enums(priority=priority, system=system, business_type=business)
            steps = _normalize_steps(
                row.get("steps"),
                allow_hints=project.library_kind == LIBRARY_AUTOMATION,
            )
        except ValueError as exc:
            raise ValueError(f"第 {index} 行：{exc}") from exc
        prepared.append(
            {
                "title": title,
                "priority": priority,
                "system": system,
                "business_type": business,
                "module": str(row.get("module") or ""),
                "precondition": str(row.get("precondition") or ""),
                "steps": steps,
            }
        )
    model = project_case_model(project)
    with transaction.atomic():
        current = _lock_count(project)
        remaining = CASE_ROW_LIMIT - current
        if len(prepared) > remaining:
            raise ConflictError(
                f"还可追加 {max(remaining, 0)} 条，本次 {len(prepared)} 条已整份拒绝"
            )
        created = []
        for offset, row in enumerate(prepared):

            def _keep(case_id: str, _offset=offset) -> str:
                return case_id

            case_id = allocate_case_id_on_create(_keep)
            obj = model.objects.create(
                id=case_id,
                project=project,
                title=row["title"],
                priority=row["priority"],
                system=row["system"],
                business_type=row["business_type"],
                module=row["module"],
                precondition=row["precondition"],
                sort_order=current + offset,
                created_by=user_id,
                updated_by=user_id,
            )
            _replace_steps(obj, project, row["steps"])
            created.append(obj.id)
    return {"imported": len(created), "ids": created}


def list_automation_projects(*, user_id: str) -> list[dict[str, Any]]:
    projects = CaseProject.objects.filter(
        created_by=user_id,
        library_kind=LIBRARY_AUTOMATION,
    ).order_by("name")
    result = []
    for project in projects:
        rows = AutomationCase.objects.filter(project=project).order_by("sort_order", "id")
        result.append(
            {
                "id": project.id,
                "name": project.name,
                "rows": [{"id": row.id, "title": row.title} for row in rows],
            }
        )
    return result


def automation_case_identity(*, case_ids: list[str], user_id: str) -> list[dict[str, str]]:
    return [
        {
            "project": " ".join(str(row.project.name or "").split())[:200],
            "id": str(row.id),
            "title": " ".join(str(row.title or "").split())[:500],
        }
        for row in _automation_rows(case_ids, user_id)
    ]


def compile_automation_cases(*, case_ids: list[str], user_id: str) -> str:
    steps = []
    for row in _automation_rows(case_ids, user_id):
        for index, step in enumerate(row.steps.all(), start=1):
            subject = " ".join(str(step.action or "").split()) or f"第 {index} 步"
            description = f"用例：{row.title}\n动作：{step.action}\n断言：{step.assertion}"
            if step.anchor:
                description += f"\n页面锚点：{step.anchor}"
            if step.log:
                description += f"\n日志证据：{step.log}"
            steps.append(
                {
                    "subject": subject,
                    "description": description,
                    "max_attempts": 3,
                }
            )
    if not steps:
        raise ValueError("所选用例没有可执行步骤")
    return yaml.safe_dump(
        {"name": "platform-cases", "description": "由平台自动化用例编译", "steps": steps},
        allow_unicode=True,
        sort_keys=False,
    )


def _automation_rows(case_ids: list[str], user_id: str) -> list[AutomationCase]:
    if not case_ids:
        raise ValueError("请至少选择 1 条自动化用例")
    rows = []
    for case_id in case_ids:
        row = (
            AutomationCase.objects.select_related("project")
            .filter(id=case_id, project__created_by=user_id)
            .first()
        )
        if row is None:
            if _functional_case_exists(case_id):
                raise LookupError("只能选择自动化用例")
            raise LookupError("用例不存在或无权限")
        rows.append(row)
    return rows


def _functional_case_exists(case_id: str) -> bool:
    from .models import FunctionalCase

    return FunctionalCase.objects.filter(id=case_id).exists()
