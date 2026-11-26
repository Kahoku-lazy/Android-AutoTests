from __future__ import annotations

import re

from typing import Any

from django.db import transaction

from utils.logs import backend_log

from .api_projects import create_project, get_project
from .api_rows import CASE_ROW_LIMIT, create_row
from .models import LIBRARY_FUNCTIONAL, CaseProject, FunctionalCase

PROJECT_NAME = "AI 生成用例"
PROJECT_DESCRIPTION = "Agent-02 验收通过的用例自动写入"

__all__ = ["PROJECT_NAME", "import_case_rows"]


def _clip(value: object, limit: int) -> str:
    return str(value or "").strip()[:limit]


def _plain_text(value: object) -> str:
    return re.sub(r"<br\s*/?>", "\n", str(value or ""), flags=re.IGNORECASE).strip()


def _priority(value: object) -> str:
    text = str(value or "").strip().upper()
    for key in ("P0", "P1", "P2"):
        if text.startswith(key):
            return key
    return "P1"


def _normalize_rows(
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    valid: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    for row in rows or []:
        title = _clip(row.get("title"), 500)
        steps = [
            {
                "action": _plain_text(step.get("action")),
                "assertion": _plain_text(step.get("assertion") or step.get("expect_state")),
            }
            for step in (row.get("steps") or [])
            if isinstance(step, dict)
        ]
        reason = ""
        if not title:
            reason = "测试标题为空"
        elif not steps:
            reason = "测试步骤为空"
        elif any(not step["action"] or not step["assertion"] for step in steps):
            reason = "存在空动作或空断言"
        if reason:
            skipped.append({"title": title, "reason": reason})
            continue
        valid.append(
            {
                "title": title,
                "priority": _priority(row.get("priority")),
                "module": _clip(row.get("module"), 200),
                "precondition": _plain_text(row.get("precondition")),
                "steps": steps,
                "source_case_id": _clip(row.get("source_case_id"), 200),
            }
        )
    return valid, skipped


def _result(**kwargs: Any) -> dict[str, Any]:
    base = {
        "status": "skipped",
        "project_id": None,
        "path": "",
        "case_count": 0,
        "skipped_count": 0,
        "skipped": [],
        "message": "",
    }
    base.update(kwargs)
    base["skipped_count"] = len(base["skipped"])
    return base


def _project_row_count(project: CaseProject) -> int:
    return FunctionalCase.objects.filter(project=project).count()


def _functional_project(user_id: str) -> CaseProject:
    project = CaseProject.objects.filter(created_by=user_id, name=PROJECT_NAME).first()
    if project is None:
        created = create_project(
            name=PROJECT_NAME,
            description=PROJECT_DESCRIPTION,
            library_kind=LIBRARY_FUNCTIONAL,
            user_id=user_id,
        )
        project = get_project(project_id=created["id"], user_id=user_id)
    if project is None or project.library_kind != LIBRARY_FUNCTIONAL:
        raise RuntimeError("AI 生成用例项目不是功能库")
    return project


def import_case_rows(
    *,
    user_id: str,
    task_id: int,
    task_title: str,
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    owner = str(user_id or "").strip()
    if not owner:
        raise ValueError("缺少任务发起人，无法写入用例库")
    if not task_id:
        raise ValueError("缺少来源任务编号，无法写入用例库")
    valid, skipped = _normalize_rows(rows)
    if not valid:
        return _result(status="skipped", skipped=skipped, message="没有可写入的用例")
    existing = FunctionalCase.objects.filter(source_task_id=str(task_id), project__created_by=owner)
    if existing.exists():
        first = existing.first()
        return _result(
            status="imported",
            project_id=first.project_id,
            path=f"/cases/projects/{first.project_id}",
            case_count=existing.count(),
            skipped=skipped,
        )
    try:
        with transaction.atomic():
            project = _functional_project(owner)
            CaseProject.objects.select_for_update().get(pk=project.pk)
            current = _project_row_count(project)
            remaining = CASE_ROW_LIMIT - current
            if len(valid) > remaining:
                return _result(
                    status="failed",
                    project_id=project.id,
                    path=f"/cases/projects/{project.id}",
                    skipped=skipped,
                    message=f"还可追加 {max(remaining, 0)} 条",
                )
            for row in valid:
                create_row(
                    project_id=project.id,
                    user_id=owner,
                    title=row["title"],
                    priority=row["priority"],
                    module=row["module"],
                    precondition=row["precondition"],
                    steps=row["steps"],
                    source_case_id=row["source_case_id"],
                    source_task_id=str(task_id),
                )
    except Exception as exc:  # noqa: BLE001 - 导入失败转为任务结果，不改任务状态
        backend_log.exception("import case rows failed task=%s user=%s", task_id, owner)
        return _result(status="failed", skipped=skipped, message=f"写入用例库失败：{exc}")
    return _result(
        status="imported",
        project_id=project.id,
        path=f"/cases/projects/{project.id}",
        case_count=len(valid),
        skipped=skipped,
        message=f"已追加 {len(valid)} 条",
    )
