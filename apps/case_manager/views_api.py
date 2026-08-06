"""case-manager API interface test case endpoints — CRUD, batch."""

import json
import logging
import random
import string

from datetime import datetime

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .api_api import batch_save_api_definitions
from .models_api import ApiTestCase
from .views_base import (
    handle_batch_definitions,
    handle_definition_detail,
    handle_get_definitions,
    handle_post_definition,
)
from .views_helpers import resolve_username as _resolve_username

logger = logging.getLogger(__name__)


def _serialize_api(row):
    """Convert an ApiTestCase ORM row to a dict for JSON responses."""
    d = {
        "id": row.id,
        "title": row.title,
        "case_type": row.case_type,
        "category": row.category,
        "description": row.description,
        "enabled": row.enabled,
        "priority": row.priority,
        "precondition": row.precondition,
        "method": row.method,
        "url": row.url,
        "headers": row.headers,
        "body": row.body,
        "expected_response": row.expected_response,
        "steps_json": row.steps_json,
        "expected_status": row.expected_status,
        "assertions": row.assertions,
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


def _normalize_api_batch(cases, directory_id):
    """Normalize batch-imported API cases to a standard format."""
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
                "method": c.get("http_method", c.get("method", "GET")),
                "url": c.get("url", ""),
                "headers": c.get("headers", {}),
                "body": c.get("request_body", c.get("body", {})),
                "expected_status": c.get("expected_status", 200),
                "expected_response": c.get("expected_response", {}),
                "assertions": c.get("assertions", []),
                "design_method": c.get("design_method", ""),
                "precondition": c.get("precondition", ""),
                "expected_result": c.get("expected_result", ""),
                "metrics": c.get("metrics", ""),
            }
        )
    return normalized


# ══════════════════════════════════════════════════════════════════
# API Testing definitions CRUD
# ══════════════════════════════════════════════════════════════════


@csrf_exempt
def api_testing_definitions_handler(request):
    """GET/POST /api/cases/api-testing/definitions — API test case list and create/update."""
    if request.method == "GET":
        return handle_get_definitions(request, ApiTestCase, _serialize_api)

    elif request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"status": False, "message": "无效的 JSON"}, status=400)

        case_id = data.get("id", "").strip()
        if not case_id:
            suffix = "".join(random.choices(string.digits, k=4))
            case_id = f"API-{datetime.now().strftime('%Y%m%d')}-{datetime.now().strftime('%H%M%S')}-{suffix}"

        defaults = {
            "method": data.get("method", "GET"),
            "url": data.get("url", ""),
            "expected_status": data.get("expected_status", 200),
            "title": data.get("title", ""),
            "category": data.get("category", ""),
            "description": data.get("description", ""),
            "enabled": bool(data.get("enabled", True)),
            "priority": data.get("priority", "P1"),
            "precondition": data.get("precondition", ""),
            "headers": data.get("headers", ""),
            "body": data.get("body", ""),
            "expected_response": data.get("expected_response", ""),
            "steps_json": data.get("steps_json", "[]"),
            "custom_columns": data.get("custom_columns", []),
            "rows": data.get("rows", []),
            "design_method": data.get("design_method", ""),
            "metrics": data.get("metrics", ""),
            "visibility": data.get("visibility", "public"),
            "permitted_users": json.dumps(data.get("permitted_users", []), ensure_ascii=False),
            "permission": data.get("permission", "edit"),
            "permitted_editors": json.dumps(data.get("permitted_editors", []), ensure_ascii=False),
            "case_type": "api_testing",
            "_directory_id": data.get("directory_id"),
            "_client_updated_at": data.get("updated_at"),
        }

        return handle_post_definition(
            request,
            case_id,
            ApiTestCase,
            "api_testing",
            "API 用例",
            defaults,
        )

    return JsonResponse({"status": False, "message": "method not allowed"}, status=405)


def api_testing_definition_detail(request, case_id):
    """GET/DELETE /api/cases/api-testing/definitions/{case_id} — API test single case."""
    return handle_definition_detail(request, case_id, ApiTestCase, _serialize_api)


@csrf_exempt
def api_testing_definitions_batch(request):
    """POST /api/cases/api-testing/definitions/batch — Batch import API test cases."""
    return handle_batch_definitions(request, batch_save_api_definitions, _normalize_api_batch)
