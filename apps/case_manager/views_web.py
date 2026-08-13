"""case-manager web automation test case endpoints."""

import json
import logging
import random
import string

from datetime import datetime

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .api_web import batch_save_web_definitions
from .models_web import WebTestCase
from .views_base import (
    handle_batch_definitions,
    handle_definition_detail,
    handle_get_definitions,
    handle_post_definition,
)
from .views_helpers import resolve_username as _resolve_username

logger = logging.getLogger(__name__)


def _serialize_web(row):
    steps_data = []
    try:
        steps_data = json.loads(row.steps_json or "[]")
    except (json.JSONDecodeError, TypeError):
        steps_data = []

    d = {
        "id": row.id,
        "title": row.title,
        "case_type": row.case_type,
        "category": row.category,
        "description": row.description,
        "enabled": row.enabled,
        "priority": row.priority,
        "url": row.url,
        "precondition": row.precondition,
        "steps": row.steps,
        "expected_result": row.expected_result,
        "steps_json": row.steps_json,
        "steps_data": steps_data,
        "custom_columns": row.custom_columns if isinstance(row.custom_columns, list) else [],
        "rows": row.rows if isinstance(row.rows, list) else [],
        "created_at": str(row.created_at),
        "updated_at": str(row.updated_at),
        "created_by": _resolve_username(row.created_by) if row.created_by else "",
        "updated_by": _resolve_username(row.updated_by) if row.updated_by else "",
        "editing_by": _resolve_username(row.editing_by) if row.editing_by else "",
        "editing_since": str(row.editing_since) if row.editing_since else "",
        "locked": row.locked,
        "visibility": row.visibility,
        "permitted_users": json.loads(row.permitted_users or "[]"),
        "permission": row.permission,
        "permitted_editors": json.loads(row.permitted_editors or "[]"),
        "directory_id": row.directory_id,
        "directory_name": row.directory.name if row.directory else None,
        "design_method": row.design_method,
        "metrics": row.metrics,
    }
    return d


def _normalize_web_batch(cases, directory_id):
    """Normalize batch-imported web cases to a standard format."""
    normalized = []
    for c in cases:
        normalized.append(
            {
                "case_id": c.get("id", c.get("case_id", "")),
                "title": c.get("title", ""),
                "category": c.get("category", ""),
                "description": c.get("description", ""),
                "enabled": c.get("enabled", False),
                "directory_id": directory_id,
                "priority": c.get("priority", "P1"),
                "url": c.get("url", ""),
                "precondition": c.get("precondition", ""),
                "steps": c.get("steps", ""),
                "expected_result": c.get("expected_result", ""),
                "custom_columns": c.get("custom_columns", []),
                "design_method": c.get("design_method", ""),
                "metrics": c.get("metrics", ""),
            }
        )
    return normalized


# ══════════════════════════════════════════════════════════════════
# Web Automation definitions CRUD
# ══════════════════════════════════════════════════════════════════


@csrf_exempt
def web_definitions_handler(request):
    """GET/POST /api/cases/web/definitions — Web automation case list and create/update."""
    if request.method == "GET":
        return handle_get_definitions(request, WebTestCase, _serialize_web)

    elif request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"status": False, "message": "无效的 JSON"}, status=400)

        case_id = data.get("id", "").strip()
        if not case_id:
            suffix = "".join(random.choices(string.digits, k=4))
            case_id = f"WEB-{datetime.now().strftime('%Y%m%d')}-{datetime.now().strftime('%H%M%S')}-{suffix}"

        fields = {
            "title": data.get("title", ""),
            "category": data.get("category", ""),
            "description": data.get("description", ""),
            "enabled": bool(data.get("enabled", True)),
            "priority": data.get("priority", "P1"),
            "url": data.get("url", ""),
            "precondition": data.get("precondition", ""),
            "steps": data.get("steps", ""),
            "expected_result": data.get("expected_result", ""),
            "steps_json": data.get("steps_json", "[]"),
            "custom_columns": data.get("custom_columns", []),
            "rows": data.get("rows", []),
            "design_method": data.get("design_method", ""),
            "metrics": data.get("metrics", ""),
            "visibility": data.get("visibility", "public"),
            "permitted_users": data.get("permitted_users", []),
            "permission": data.get("permission", "edit"),
            "permitted_editors": data.get("permitted_editors", []),
            "case_type": "web_automation",
            "directory_id": data.get("directory_id"),
            "client_updated_at": data.get("updated_at"),
        }

        return handle_post_definition(
            request,
            case_id,
            WebTestCase,
            "web_automation",
            "Web 用例",
            fields,
        )

    return JsonResponse({"status": False, "message": "method not allowed"}, status=405)


def web_definition_detail(request, case_id):
    """GET/DELETE /api/cases/web/definitions/{case_id} — Web automation single case."""
    return handle_definition_detail(request, case_id, WebTestCase, _serialize_web)


@csrf_exempt
def web_definitions_batch(request):
    """POST /api/cases/web/definitions/batch — Batch import web automation test cases."""
    return handle_batch_definitions(request, batch_save_web_definitions, _normalize_web_batch)
