"""
python -m 调试路径: backend.apps.case_manager.api_import

本模块的业务功能如下：
1. import_case_rows: 把 Agent-02 已通过验收的用例行写入「AI 生成用例」项目。
"""

from __future__ import annotations

import re

from typing import Any

from django.db import IntegrityError, transaction

from utils.logs import backend_log

from .api_definitions import create_definition
from .models import CaseFile, CaseProject, TestDefinition

PROJECT_NAME = "AI 生成用例"
PROJECT_DESCRIPTION = "Agent-02 验收通过的用例自动写入"
FILE_NAME_LIMIT = 200

__all__ = ["PROJECT_NAME", "import_case_rows"]


def _clip(value: object, limit: int) -> str:
    """去掉首尾空白并按字符上限截断。"""
    return str(value or "").strip()[:limit]


def _plain_text(value: object) -> str:
    """把 Markdown 单元格里的 ``<br>`` 还原成换行，避免界面显示原始标签。"""
    return re.sub(r"<br\s*/?>", "\n", str(value or ""), flags=re.IGNORECASE).strip()


def _priority(value: object) -> str:
    """只接受 P0 / P1 / P2；无法识别时回退 P1。"""
    text = str(value or "").strip().upper()
    for key in ("P0", "P1", "P2"):
        if text.startswith(key):
            return key
    return "P1"


def _file_name(task_title: str, task_id: int) -> str:
    """生成与任务一一对应的用例文件名，并保证不超过模型上限。"""
    suffix = f"（任务 {task_id}）"
    base = _clip(task_title, FILE_NAME_LIMIT - len(suffix)) or f"任务 {task_id}"
    return f"{base}{suffix}"[:FILE_NAME_LIMIT]


def _normalize_rows(
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """过滤不可写入的行，返回（合法行, 跳过明细）。"""
    valid: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    for row in rows or []:
        source_id = _clip(row.get("source_case_id"), 200)
        title = _clip(row.get("title"), 500)
        steps = [
            {
                "action": str(step.get("action") or "").strip(),
                "assertion": str(step.get("assertion") or "").strip(),
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
        elif any(len(step["action"]) > 2000 or len(step["assertion"]) > 2000 for step in steps):
            reason = "单段动作或断言超过 2000 字符"
        if reason:
            skipped.append({"source_case_id": source_id, "reason": reason})
            continue
        valid.append(
            {
                "source_case_id": source_id,
                "title": title,
                "priority": _priority(row.get("priority")),
                "module": _clip(row.get("module"), 200),
                "precondition": _plain_text(row.get("precondition")),
                "steps": steps,
            }
        )
    return valid, skipped


def _get_or_create_project(user_id: str) -> CaseProject:
    """按用户取「AI 生成用例」项目；并发创建冲突时重查一次。"""
    try:
        obj, _ = CaseProject.objects.get_or_create(
            created_by=user_id,
            name=PROJECT_NAME,
            defaults={"description": PROJECT_DESCRIPTION},
        )
    except IntegrityError:
        obj = CaseProject.objects.get(created_by=user_id, name=PROJECT_NAME)
    return obj


def _get_or_create_file(*, project: CaseProject, name: str, user_id: str) -> CaseFile:
    """按项目取任务用例文件；同名冲突时重查一次。

    Raises:
        IntegrityError: 同名文件并发创建且重查仍失败时抛出。
    """
    try:
        obj, _ = CaseFile.objects.get_or_create(
            project=project,
            directory=None,
            name=name,
            defaults={"created_by": user_id},
        )
    except IntegrityError:
        obj = CaseFile.objects.filter(project=project, directory=None, name=name).first()
        if obj is None:
            raise
    return obj


def _path(project_id: int, file_id: int) -> str:
    """用例文件页地址；前端用 router-link 直接跳转。"""
    return f"/cases/projects/{project_id}/files/{file_id}"


def _result(
    *,
    status: str,
    project_id: int | None = None,
    file_id: int | None = None,
    case_count: int = 0,
    skipped: list[dict[str, str]] | None = None,
    message: str = "",
) -> dict[str, Any]:
    """统一导入结论结构。"""
    skipped = skipped or []
    return {
        "status": status,
        "project_id": project_id,
        "file_id": file_id,
        "path": _path(project_id, file_id) if project_id and file_id else "",
        "case_count": case_count,
        "skipped_count": len(skipped),
        "skipped": skipped,
        "message": message,
    }


def import_case_rows(
    *,
    user_id: str,
    task_id: int,
    task_title: str,
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    把一次 Agent-02 任务的用例行写入用例库，并按来源任务保证幂等。

    Args:
        user_id: 任务发起人编号，用例项目归属该用户。
        task_id: 来源任务编号，用于幂等与追溯。
        task_title: 任务标题，用于生成用例文件名。
        rows: 中性用例行，含 title / priority / module / precondition / steps / source_case_id。

    Returns:
        `{status, project_id, file_id, path, case_count, skipped_count, skipped, message}`。

    Raises:
        RuntimeError: 数据库写入失败且无法恢复时抛出，由调用方降级为任务结果。
        ValueError: 入参缺少用户或任务编号时抛出。
    """
    owner = str(user_id or "").strip()
    if not owner:
        raise ValueError("缺少任务发起人，无法写入用例库")
    if not task_id:
        raise ValueError("缺少来源任务编号，无法写入用例库")

    valid, skipped = _normalize_rows(rows)
    if not valid:
        return _result(status="skipped", skipped=skipped, message="没有可写入的用例")

    existing = (
        TestDefinition.objects.filter(source_task_id=str(task_id))
        .order_by("sort_order", "id")
        .first()
    )
    if existing is not None:
        count = TestDefinition.objects.filter(source_task_id=str(task_id)).count()
        return _result(
            status="imported",
            project_id=existing.project_id,
            file_id=existing.file_id,
            case_count=count,
            skipped=skipped,
        )

    try:
        with transaction.atomic():
            project = _get_or_create_project(owner)
            case_file = _get_or_create_file(
                project=project,
                name=_file_name(task_title, task_id),
                user_id=owner,
            )
            created = 0
            for index, row in enumerate(valid):
                create_definition(
                    project_id=project.id,
                    file_id=case_file.id,
                    user_id=owner,
                    title=row["title"],
                    priority=row["priority"],
                    system="ANDROID",
                    case_type="FUNC",
                    business_type="appliance",
                    module=row["module"],
                    precondition=row["precondition"],
                    steps=row["steps"],
                    sort_order=index,
                    source_case_id=row["source_case_id"],
                    source_task_id=str(task_id),
                )
                created += 1
    except Exception as exc:  # noqa: BLE001 - 导入失败要转为可读结论，不能拖垮任务
        backend_log.exception("import case rows failed task=%s user=%s", task_id, owner)
        return _result(
            status="failed",
            skipped=skipped,
            message=f"写入用例库失败：{exc}",
        )

    return _result(
        status="imported",
        project_id=project.id,
        file_id=case_file.id,
        case_count=created,
        skipped=skipped,
    )
