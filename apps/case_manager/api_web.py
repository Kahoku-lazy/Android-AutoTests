"""case-manager web automation test case API — CRUD, batch."""

__all__ = [
    "batch_save_web_definitions",
    "get_web_definition",
    "get_web_definitions",
    "save_web_definition",
]

import json
import logging

from .api_ui import ConflictError, _parse_datetime
from .models import CaseDirectory
from .models_web import WebTestCase

logger = logging.getLogger(__name__)


def get_web_definitions(case_ids):
    return list(WebTestCase.objects.filter(id__in=case_ids, enabled=True))


def get_web_definition(case_id):
    try:
        return WebTestCase.objects.get(id=case_id)
    except WebTestCase.DoesNotExist:
        return None


def save_web_definition(case_id, **fields):
    client_updated_at = fields.pop("client_updated_at", None)
    directory_id = fields.get("directory_id")
    directory = None
    if directory_id is not None:
        try:
            directory = CaseDirectory.objects.get(id=directory_id)
        except CaseDirectory.DoesNotExist:
            logger.warning(
                "Directory %s not found when saving web case, saving without directory",
                directory_id,
            )

    title = fields.get("title", "")

    existing = WebTestCase.objects.filter(id=case_id).only("id", "updated_at").first()
    if existing and client_updated_at:
        client_ts = _parse_datetime(client_updated_at)
        if client_ts and existing.updated_at:
            if client_ts != existing.updated_at.replace(microsecond=0):
                raise ConflictError(f"Web 用例「{title or case_id}」已被他人修改，请刷新后重试")

    dup = WebTestCase.objects.filter(directory=directory, title=title).exclude(id=case_id).first()
    if dup:
        dir_label = directory.name if directory else "根级（未分类）"
        raise ValueError(f"目录「{dir_label}」下已存在同名 Web 用例「{title}」")

    defaults = {
        "title": title,
        "category": fields.get("category", ""),
        "description": fields.get("description", ""),
        "enabled": fields.get("enabled", True),
        "directory": directory,
        "priority": fields.get("priority", "P1"),
        "url": fields.get("url", ""),
        "precondition": fields.get("precondition", ""),
        "steps": fields.get("steps", ""),
        "expected_result": fields.get("expected_result", ""),
        "custom_columns": fields.get("custom_columns", []),
        "rows": fields.get("rows", []),
        "design_method": fields.get("design_method", ""),
        "metrics": fields.get("metrics", ""),
        "visibility": fields.get("visibility", "public"),
        "permitted_users": json.dumps(fields.get("permitted_users", []), ensure_ascii=False),
        "permission": fields.get("permission", "edit"),
        "permitted_editors": json.dumps(fields.get("permitted_editors", []), ensure_ascii=False),
        "case_type": "web_automation",
    }
    obj, _ = WebTestCase.objects.update_or_create(id=case_id, defaults=defaults)
    return obj


def batch_save_web_definitions(cases: list[dict], overwrite: bool = False) -> dict:
    imported, skipped, failed = [], [], []
    for case in cases:
        cid = case.get("case_id") or case.get("id", "")
        if not cid:
            failed.append({"reason": "missing id", "case": case})
            continue
        if not overwrite and WebTestCase.objects.filter(id=cid).exists():
            skipped.append({"id": cid, "reason": "already exists"})
            continue
        try:
            obj = save_web_definition(case_id=cid, **case)
            imported.append({"id": obj.id, "title": obj.title})
        except Exception as e:
            failed.append({"id": cid, "reason": str(e)})
    return {"imported": imported, "skipped": skipped, "failed": failed}
