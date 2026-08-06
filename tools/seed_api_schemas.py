"""Update existing ApiEndpoint records with headers, request/response body schemas."""

import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django

django.setup()

from apps.element_locator.models import ApiEndpoint

# Common auth header
AUTH_HEADER = {"Authorization": "Bearer <JWT>"}
JSON_HEADER = {"Content-Type": "application/json", "Authorization": "Bearer <JWT>"}
FORM_HEADER = {"Content-Type": "application/x-www-form-urlencoded", "Authorization": "Bearer <JWT>"}
MULTIPART_HEADER = {"Content-Type": "multipart/form-data", "Authorization": "Bearer <JWT>"}
NO_AUTH_JSON = {"Content-Type": "application/json"}
PLAIN_HEADER = {"Authorization": "Bearer <JWT>"}

# Response wrappers
OK_RESP = {"status": True, "data": "object | array | null"}
ERR_RESP = {"status": False, "error": "string — error description"}
LIST_RESP = {"status": True, "data": {"items": "array", "total": "integer"}}
PAGINATED_RESP = {
    "status": True,
    "data": {"items": "array", "total": "integer", "page": "integer", "page_size": "integer"},
}

# ── Schema templates by category ──
SCHEMAS = {
    # Auth
    "login": {
        "headers": NO_AUTH_JSON,
        "request": {"username": "string", "password": "string"},
        "response": {
            "status": True,
            "access_token": "string — JWT",
            "refresh_token": "string",
            "token_type": "bearer",
            "user": {"id": 1, "username": "string"},
        },
    },
    "register": {
        "headers": NO_AUTH_JSON,
        "request": {"username": "string", "password": "string", "email": "string (optional)"},
        "response": {"status": True, "user": {"id": 1, "username": "string"}},
    },
    "refresh": {
        "headers": NO_AUTH_JSON,
        "request": {"refresh_token": "string"},
        "response": {"status": True, "access_token": "string — new JWT"},
    },
    "logout": {
        "headers": AUTH_HEADER,
        "request": None,
        "response": {"status": True},
    },
    "me": {
        "headers": AUTH_HEADER,
        "request": None,
        "response": {"status": True, "user": {"id": 1, "username": "string", "email": "string"}},
    },
    # List queries
    "list": {
        "headers": AUTH_HEADER,
        "request": None,
        "response": {"status": True, "items": "array", "total": "integer"},
    },
    "list_paginated": {
        "headers": AUTH_HEADER,
        "request": None,
        "response": {"status": True, "items": "array", "total": "integer", "page": "integer"},
    },
    "detail": {
        "headers": AUTH_HEADER,
        "request": None,
        "response": {"status": True, "item": "object"},
    },
    # CRUD operations
    "create": {
        "headers": JSON_HEADER,
        "request": "object — resource fields",
        "response": {"status": True, "item": {"id": "integer", "name": "string", "...": "..."}},
    },
    "update": {
        "headers": JSON_HEADER,
        "request": {"field1": "value1", "...": "partial update fields"},
        "response": {"status": True, "item": "object — updated resource"},
    },
    "delete": {
        "headers": AUTH_HEADER,
        "request": None,
        "response": {"status": True},
    },
    "batch": {
        "headers": JSON_HEADER,
        "request": {"items": "array of objects", "action": "string (optional)"},
        "response": {
            "status": True,
            "saved": "integer",
            "updated": "integer",
            "skipped": "integer",
        },
    },
    "batch_move": {
        "headers": JSON_HEADER,
        "request": {"ids": "array of integers", "parent_id": "integer | null"},
        "response": {"status": True, "moved": "integer"},
    },
    # Device operations
    "device_connect": {
        "headers": JSON_HEADER,
        "request": {"activate": "boolean", "mode": "string — observe | control"},
        "response": {"status": True, "serial": "string", "status": "string — ONLINE"},
    },
    "device_lock": {
        "headers": JSON_HEADER,
        "request": {"user_id": "string", "timeout": "integer — seconds"},
        "response": {"status": True, "lock_id": "integer", "expires_at": "string — ISO datetime"},
    },
    # Test execution
    "start_run": {
        "headers": JSON_HEADER,
        "request": {
            "case_ids": "array",
            "device_serial": "string",
            "loop_count": "integer (default: 3)",
        },
        "response": {"status": True, "run_id": "string", "ws_url": "string"},
    },
    "run_status": {
        "headers": AUTH_HEADER,
        "request": None,
        "response": {
            "status": True,
            "run_id": "string",
            "status": "string — running | completed | failed | stopped",
            "progress": "object",
        },
    },
    # Dump / screenshot
    "dump": {
        "headers": AUTH_HEADER,
        "request": None,
        "response": {
            "status": True,
            "serial": "string",
            "package": "string",
            "activity": "string",
            "elements": "array of element objects",
            "actionable": "array",
        },
    },
    "screenshot": {
        "headers": AUTH_HEADER,
        "request": None,
        "response": {
            "status": True,
            "image": "string — base64 JPEG",
            "format": "jpeg",
            "screen_w": "integer",
            "screen_h": "integer",
        },
    },
    "device_action": {
        "headers": JSON_HEADER,
        "request": {
            "action": "string — click | input | swipe | drag",
            "x": "integer",
            "y": "integer",
            "text": "string (for input)",
        },
        "response": {"status": True},
    },
    # Import/Export
    "import": {
        "headers": JSON_HEADER,
        "request": "object — JSON envelope with nested data",
        "response": {"status": True, "imported": "integer"},
    },
    "export": {
        "headers": JSON_HEADER,
        "request": {"ids": "array — item IDs to export", "format": "string — yaml | json"},
        "response": {"status": True, "filename": "string", "data": "string — file content"},
    },
    # File upload
    "upload": {
        "headers": MULTIPART_HEADER,
        "request": "FormData — file binary",
        "response": {"status": True, "filename": "string", "url": "string"},
    },
    "file_download": {
        "headers": AUTH_HEADER,
        "request": None,
        "response": "binary file stream",
    },
    # KB / RAG
    "kb_search": {
        "headers": JSON_HEADER,
        "request": {"query": "string", "top_k": "integer (default: 5)"},
        "response": {"status": True, "results": "array of {chunk, score, source}"},
    },
    # AgentScope SSE
    "sse_stream": {
        "headers": JSON_HEADER,
        "request": {"message": "string — user input", "conversation_id": "integer"},
        "response": "SSE event stream (text/event-stream)",
    },
    "hitl_confirm": {
        "headers": JSON_HEADER,
        "request": {"tool_call_id": "string", "decision": "string — ALLOW | DENY"},
        "response": {"status": True},
    },
    # Health / Info
    "health": {
        "headers": AUTH_HEADER,
        "request": None,
        "response": {"status": True, "service": "string", "status": "string — healthy"},
    },
    "detect": {
        "headers": JSON_HEADER,
        "request": {"api_key": "string (optional)", "base_url": "string (optional)"},
        "response": {"status": True, "models": "array of {id, name, provider}"},
    },
    # Task card
    "task_save": {
        "headers": JSON_HEADER,
        "request": {
            "name": "string",
            "description": "string",
            "status": "string",
            "device_serial": "string",
            "case_ids": "array",
        },
        "response": {"status": True, "task": "object"},
    },
    # WebSocket (special)
    "ws_screenshot": {
        "headers": None,
        "request": "WebSocket connect to ws://host/ws/screenshot",
        "response": "Frame stream: {type: 'screenshot', url: 'string — base64 PNG data URL'} @2fps",
    },
    "ws_test_run": {
        "headers": None,
        "request": "WebSocket connect to ws://host/ws/test-run/{run_id}/",
        "response": "Event stream: {type: log|case_started|iteration_result|case_finished|run_finished|device_error}",
    },
    # Eval / Scoring
    "eval_start": {
        "headers": JSON_HEADER,
        "request": {
            "bank_id": "integer",
            "agent_id": "integer",
            "model": "string",
            "iterations": "integer",
        },
        "response": {"status": True, "run_id": "integer", "status": "string — running"},
    },
    "human_score": {
        "headers": JSON_HEADER,
        "request": {
            "dimensions": "object — {accuracy: n, completeness: n, ...}",
            "comment": "string",
        },
        "response": {"status": True},
    },
    # Lock / permission
    "lock": {
        "headers": JSON_HEADER,
        "request": {"user_id": "string", "duration": "integer — seconds"},
        "response": {"status": True, "locked_by": "string", "expires_at": "string"},
    },
    "unlock": {
        "headers": AUTH_HEADER,
        "request": None,
        "response": {"status": True},
    },
    "visibility": {
        "headers": JSON_HEADER,
        "request": {"visibility": "string — public | private | restricted"},
        "response": {"status": True},
    },
}


# ── Match URL patterns to schemas ──
def schema_for(name, method, url):
    """Determine best schema for an endpoint based on its attributes."""
    name_lower = (name or "").lower()
    url_lower = (url or "").lower()

    # Auth endpoints
    if "login" in url_lower and "refresh" not in url_lower:
        return SCHEMAS["login"]
    if "register" in url_lower:
        return SCHEMAS["register"]
    if "refresh" in url_lower:
        return SCHEMAS["refresh"]
    if "logout" in url_lower:
        return SCHEMAS["logout"]
    if url_lower.endswith("/me") or url_lower.endswith("/auth/me"):
        return SCHEMAS["me"]

    # WebSocket
    if method == "WS":
        if "screenshot" in url_lower:
            return SCHEMAS["ws_screenshot"]
        if "test-run" in url_lower:
            return SCHEMAS["ws_test_run"]
        return SCHEMAS["ws_screenshot"]

    # KB / RAG
    if "kb-search" in url_lower or "kb_self_test" in url_lower:
        return SCHEMAS["kb_search"]
    if "reindex" in url_lower:
        return dict(
            SCHEMAS["kb_search"], response={"status": True, "status": "string — reindex complete"}
        )

    # File operations
    if "upload" in url_lower or "upload" in name_lower:
        if "avatar" in url_lower:
            return SCHEMAS["upload"]
        if "file" in url_lower:
            return SCHEMAS["upload"]
    if "download" in url_lower:
        return SCHEMAS["file_download"]
    if "export" in name_lower and method == "GET":
        return SCHEMAS["file_download"]
    if "serve" in url_lower or "avatars/" in url_lower:
        return SCHEMAS["file_download"]

    # SSE / Stream
    if "stream" in url_lower:
        return SCHEMAS["sse_stream"]
    if "send" in url_lower and method == "POST" and "message" in url_lower:
        return SCHEMAS["sse_stream"]
    if "confirm-result" in url_lower:
        return SCHEMAS["hitl_confirm"]

    # Health / Detect
    if "health" in url_lower or "health" in name_lower:
        return SCHEMAS["health"]
    if "detect" in url_lower or "models/detect" in url_lower:
        return SCHEMAS["detect"]
    if "default-system-prompt" in url_lower:
        return SCHEMAS["detail"]

    # Eval
    if "banks/seed" in url_lower:
        return SCHEMAS["create"]
    if "score" in url_lower and "human" in name_lower:
        return SCHEMAS["human_score"]
    if "runs/start" in url_lower or "start_eval" in name_lower:
        return SCHEMAS["eval_start"]
    if "frameworks" in url_lower:
        return SCHEMAS["list"]
    if "kb-self-test" in url_lower:
        return SCHEMAS["kb_search"]

    # Test execution
    if (
        url_lower == "/api/runner/run"
        or "start_test_run" in name_lower
        or ("run" in url_lower and "start" not in url_lower and url_lower.endswith("run"))
    ):
        return SCHEMAS["start_run"]
    if "status" in url_lower:
        return SCHEMAS["run_status"]
    if "run-step" in url_lower:
        return SCHEMAS["device_action"]
    if "snapshot" in url_lower:
        return SCHEMAS["run_status"]
    if "monitor" in url_lower:
        return SCHEMAS["detail"]
    if "active" in url_lower:
        return SCHEMAS["list"]
    if "/runs" in url_lower or "list_test_runs" in name_lower:
        return SCHEMAS["list_paginated"]
    if "stop" in url_lower:
        return SCHEMAS["update"]
    if "queue/cancel" in url_lower:
        return SCHEMAS["update"]

    # Task cards
    if "tasks/save" in url_lower:
        return SCHEMAS["task_save"]
    if "tasks/" in url_lower and method == "DELETE":
        return SCHEMAS["delete"]
    if "/tasks" in url_lower and method == "GET":
        return SCHEMAS["list"]

    # Report
    if (
        "/reports/" in url_lower
        and method == "GET"
        and ("run/" in url_lower or "task/" in url_lower)
    ):
        return SCHEMAS["detail"]
    if "cases" in url_lower and "breakdown" in url_lower:
        return SCHEMAS["list"]
    if "content" in url_lower:
        return SCHEMAS["detail"]
    if url_lower.endswith("/reports/"):
        return SCHEMAS["list_paginated"]

    # Device operations
    if "dump" in url_lower:
        return SCHEMAS["dump"]
    if "screenshot" in url_lower:
        return SCHEMAS["screenshot"]
    if "action" in url_lower and method == "POST":
        return SCHEMAS["device_action"]
    if "device-info" in url_lower:
        return SCHEMAS["detail"]
    if "scan" in url_lower:
        return SCHEMAS["create"]
    if "connect" in url_lower:
        return SCHEMAS["device_connect"]
    if "disconnect" in url_lower:
        return SCHEMAS["device_connect"]
    if "activate" in url_lower:
        return SCHEMAS["device_connect"]
    if (
        "lock" in url_lower
        and method == "POST"
        and "unlock" not in url_lower
        and "batch" not in url_lower
    ):
        return SCHEMAS["device_lock"]
    if "release" in url_lower:
        return SCHEMAS["unlock"]
    if "heartbeat" in url_lower:
        return SCHEMAS["health"]
    if "queue" in url_lower and "leave" in url_lower:
        return SCHEMAS["unlock"]
    if "queue" in url_lower:
        return SCHEMAS["device_lock"]
    if "current" in url_lower:
        return SCHEMAS["detail"]

    # Lock / permission
    if "lock" in url_lower and method == "POST":
        return SCHEMAS["lock"]
    if "unlock" in url_lower:
        return SCHEMAS["unlock"]
    if "visibility" in url_lower:
        return SCHEMAS["visibility"]
    if "permission" in url_lower:
        return SCHEMAS["update"]

    # Batch operations
    if "batch-move" in url_lower or "batch_move" in name_lower:
        return SCHEMAS["batch_move"]
    if "batch" in url_lower and method == "POST":
        return SCHEMAS["batch"]
    if "import" in url_lower or "import" in name_lower:
        return SCHEMAS["import"]
    if "export" in url_lower and method == "POST":
        return SCHEMAS["export"]

    # Clear (dangerous)
    if "clear" in url_lower:
        return SCHEMAS["update"]

    # MCP / Tool management
    if "mcp/test" in url_lower:
        return SCHEMAS["detail"]
    if "mcp/save" in url_lower:
        return SCHEMAS["create"]
    if "skill/upload" in url_lower:
        return SCHEMAS["upload"]
    if "toggle" in url_lower:
        return SCHEMAS["update"]
    if "tools/" in url_lower and method == "DELETE":
        return SCHEMAS["delete"]
    if "tools" in url_lower and method == "GET":
        return SCHEMAS["list"]

    # Agent management
    if "register-scope" in url_lower:
        return SCHEMAS["create"]
    if "create-scope-session" in url_lower:
        return SCHEMAS["create"]
    if "reveal-key" in url_lower:
        return SCHEMAS["detail"]
    if "test" in url_lower and "agent" in url_lower:
        return SCHEMAS["detail"]
    if "models" in url_lower and method == "GET":
        return SCHEMAS["list"]
    if "agents/health" in url_lower:
        return SCHEMAS["health"]

    # CRUD by method
    if method == "POST" and "create" in url_lower:
        return SCHEMAS["create"]
    if method == "POST" and "save" in url_lower:
        return SCHEMAS["create"]
    if method == "POST" and "send" in url_lower:
        return SCHEMAS["sse_stream"]
    if method == "POST" and "save-message" in url_lower:
        return SCHEMAS["create"]
    if method == "POST" and "rename" in url_lower:
        return SCHEMAS["update"]
    if method == "POST":
        return SCHEMAS["create"]
    if method == "PUT":
        return SCHEMAS["update"]
    if method == "DELETE":
        return SCHEMAS["delete"]
    if method == "GET" and "<" in url:
        return SCHEMAS["detail"]
    if method == "GET":
        return SCHEMAS["list"]

    return SCHEMAS["list"] if method == "GET" else SCHEMAS["create"]


# ── Main ──
print("Updating ApiEndpoint records with headers & body schemas...")
updated = 0
for ep in ApiEndpoint.objects.all():
    s = schema_for(ep.name, ep.method, ep.url)
    if s:
        ep.headers = s.get("headers") or {}
        ep.request_body_schema = s.get("request") if s.get("request") is not None else {}
        ep.response_body_schema = s.get("response") if s.get("response") is not None else {}
        ep.save(update_fields=["headers", "request_body_schema", "response_body_schema"])
        updated += 1

print(f"Updated {updated} endpoints with schema data.")

# Quick stats
from collections import Counter

methods = Counter(ep.method for ep in ApiEndpoint.objects.all())
print(f"Methods: {dict(methods)}")
ep_with_req = ApiEndpoint.objects.exclude(request_body_schema={}).count()
print(f"Endpoints with request body schema: {ep_with_req}")
ep_with_resp = ApiEndpoint.objects.exclude(response_body_schema={}).count()
print(f"Endpoints with response body schema: {ep_with_resp}")
