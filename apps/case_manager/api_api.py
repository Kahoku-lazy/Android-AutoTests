"""case-manager API interface test case API — CRUD, batch."""

__all__ = [
    "batch_save_api_definitions",
    "get_api_definition",
    "get_api_definitions",
    "save_api_definition",
]

import json
import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .api_ui import ConflictError, _parse_datetime
from .models import CaseDirectory
from .models_api import ApiTestCase
from .schema_config import validate_any_api_config

logger = logging.getLogger(__name__)


def get_api_definitions(case_ids):
    """Get enabled API test cases by ID list."""
    return list(ApiTestCase.objects.filter(id__in=case_ids, enabled=True))


def get_api_definition(case_id):
    """Get a single API test case by ID, or None."""
    try:
        return ApiTestCase.objects.get(id=case_id)
    except ApiTestCase.DoesNotExist:
        return None


def save_api_definition(case_id, config_json=None, **fields):
    """Create or update an API test case.

    Args:
        case_id: API test case ID (auto-generated if new).
        config_json: Unified JSON config (case_info/steps/test_data/validation).
            Validated via jsonschema before save.
        **fields: Metadata fields (title, category, priority, visibility, etc.).

    Raises ValueError on duplicate title / invalid config_json,
    ConflictError on optimistic lock failure.
    """
    # ── Validate config_json (auto-detect single/multi format) ──
    if config_json is not None:
        validate_any_api_config(config_json)
        # Sync denormalized title from config_json
        from .schema_config import is_single_format

        if is_single_format(config_json):
            fields.setdefault("title", config_json["meta"]["title"])
        else:
            fields.setdefault("title", config_json["case_info"]["title"])

    client_updated_at = fields.pop("client_updated_at", None)
    directory_id = fields.get("directory_id")
    directory = None
    if directory_id is not None:
        try:
            directory = CaseDirectory.objects.get(id=directory_id)
        except CaseDirectory.DoesNotExist:
            logger.warning(
                "Directory %s not found when saving API case, saving without directory",
                directory_id,
            )

    title = fields.get("title", "")

    # Optimistic lock
    existing = ApiTestCase.objects.filter(id=case_id).only("id", "updated_at").first()
    if existing and client_updated_at:
        client_ts = _parse_datetime(client_updated_at)
        if client_ts and existing.updated_at:
            db_ts = existing.updated_at.replace(microsecond=0)
            if client_ts != db_ts:
                raise ConflictError(f"API 用例「{title or case_id}」已被他人修改，请刷新后重试")

    # Check duplicate title
    dup = ApiTestCase.objects.filter(directory=directory, title=title).exclude(id=case_id).first()
    if dup:
        dir_label = directory.name if directory else "根级（未分类）"
        raise ValueError(f"目录「{dir_label}」下已存在同名 API 用例「{title}」")

    defaults = {
        "title": title,
        "category": fields.get("category", ""),
        "description": fields.get("description", ""),
        "enabled": fields.get("enabled", True),
        "directory": directory,
        "priority": fields.get("priority", "P1"),
        "precondition": fields.get("precondition", ""),
        "visibility": fields.get("visibility", "public"),
        "permission": fields.get("permission", "edit"),
        "case_type": "api_testing",
    }
    # 只在显式传入 config_json 时才更新，避免覆盖已有配置
    if config_json is not None:
        defaults["config_json"] = config_json
    if "permitted_users" in fields:
        defaults["permitted_users"] = json.dumps(fields["permitted_users"], ensure_ascii=False)
    if "permitted_editors" in fields:
        defaults["permitted_editors"] = json.dumps(fields["permitted_editors"], ensure_ascii=False)
    if "created_by" in fields:
        defaults["created_by"] = fields["created_by"]
    if "updated_by" in fields:
        defaults["updated_by"] = fields["updated_by"]
    obj, _ = ApiTestCase.objects.update_or_create(id=case_id, defaults=defaults)

    # ── WebSocket push: notify editors that case was updated ──
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f"case_editing_{case_id}",
                {
                    "type": "case_updated",
                    "message": '{"type":"case_updated","case_id":"%s"}' % case_id,
                },
            )
    except Exception:
        logger.debug("WebSocket push skipped (channel layer unavailable)", exc_info=True)

    return obj


def batch_save_api_definitions(cases: list[dict], overwrite: bool = False) -> dict:
    """Batch create/update API test cases."""
    imported = []
    skipped = []
    failed = []

    for case in cases:
        cid = case.get("case_id") or case.get("id", "")
        if not cid:
            failed.append({"reason": "missing id", "case": case})
            continue
        if not overwrite and ApiTestCase.objects.filter(id=cid).exists():
            skipped.append({"id": cid, "reason": "already exists"})
            continue
        try:
            obj = save_api_definition(case_id=cid, **case)
            imported.append({"id": obj.id, "title": obj.title})
        except Exception as e:
            failed.append({"id": cid, "reason": str(e)})

    return {"imported": imported, "skipped": skipped, "failed": failed}
