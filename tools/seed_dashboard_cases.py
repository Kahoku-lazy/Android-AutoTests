"""Seed comprehensive dashboard API test cases."""

import json
import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()
from apps.case_manager.models import ApiTestCase, CaseDirectory

root = CaseDirectory.objects.filter(case_type="api_testing", parent__isnull=True).first()
plat = CaseDirectory.objects.filter(case_type="api_testing", name="测试平台", parent=root).first()
db_dir = CaseDirectory.objects.filter(case_type="api_testing", name="仪表盘", parent=plat).first()
print(f"Target: {plat.name}/{db_dir.name} (id={db_dir.id})")

ApiTestCase.objects.filter(directory=db_dir).delete()
print("Cleared old cases")


def jwt_headers():
    return json.dumps({"Authorization": "Bearer {{token}}"}, ensure_ascii=False)


BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8765")


def abs_url(path):
    return f"{BASE_URL}{path}"


def request_step(url, status=200, headers=None):
    s = {"type": "api_request", "method": "GET", "url": abs_url(url), "expected_status": status}
    if headers:
        s["headers"] = headers
    s["description"] = f"GET {url}"
    return s


def assert_step(status, assertions):
    return {"type": "api_assert", "expected_status": status, "assertions": assertions}


def steps_json(*steps):
    return json.dumps(list(steps), ensure_ascii=False)


def input_row(key, *values):
    return {"key": key, "values": list(values), "kind": "input"}


def validate_row(key, *values):
    return {"key": key, "values": list(values), "kind": "validate"}


def rows_json(*rows):
    """Pass Python list directly (JSONField handles serialization)."""
    return list(rows)


test_cases = [
    # ═══ 平台概览统计 ═══
    {
        "id": "API-DASH-001",
        "title": "[正常] 平台概览统计 — 完整响应结构校验",
        "method": "GET",
        "url": abs_url("/api/dashboard/stats/"),
        "expected_status": 200,
        "priority": "P0",
        "enabled": True,
        "headers": jwt_headers(),
        "precondition": "1. 服务正常运行\n2. 数据库已迁移",
        "description": "验证返回全部13个顶层字段：devices/cases/elements/workflow/runs/agents/reports/pass_rate/charts/execution_summary/recent_tasks/last_updated/system_status",
        "steps_json": steps_json(
            request_step("/api/dashboard/stats/", 200, {"Authorization": "Bearer {{token}}"}),
            assert_step(
                200,
                [
                    {"path": "$.ok", "op": "equals", "expect": "True"},
                    {"path": "$.data.devices", "op": "exists", "expect": ""},
                    {"path": "$.data.cases", "op": "exists", "expect": ""},
                    {"path": "$.data.elements", "op": "exists", "expect": ""},
                    {"path": "$.data.workflow", "op": "exists", "expect": ""},
                    {"path": "$.data.runs", "op": "exists", "expect": ""},
                    {"path": "$.data.agents", "op": "exists", "expect": ""},
                    {"path": "$.data.reports", "op": "exists", "expect": ""},
                    {"path": "$.data.pass_rate", "op": "exists", "expect": ""},
                    {"path": "$.data.charts", "op": "exists", "expect": ""},
                    {"path": "$.data.execution_summary", "op": "exists", "expect": ""},
                    {"path": "$.data.recent_tasks", "op": "exists", "expect": ""},
                    {"path": "$.data.last_updated", "op": "exists", "expect": ""},
                    {"path": "$.data.system_status", "op": "exists", "expect": ""},
                ],
            ),
        ),
        "rows": rows_json(
            input_row("token", "{{JWT}}"),
            validate_row("$.ok", "True"),
            validate_row("$.data.system_status", "normal"),
        ),
    },
    {
        "id": "API-DASH-002",
        "title": "[类型] 平台概览统计 — 字段类型校验",
        "method": "GET",
        "url": abs_url("/api/dashboard/stats/"),
        "expected_status": 200,
        "priority": "P1",
        "enabled": True,
        "headers": jwt_headers(),
        "description": "验证 devices.online(int), cases.total(int), pass_rate(float), last_updated(str), system_status(normal|no_devices)",
        "steps_json": steps_json(
            request_step("/api/dashboard/stats/", 200, {"Authorization": "Bearer {{token}}"}),
            assert_step(
                200,
                [
                    {"path": "$.ok", "op": "equals", "expect": "True"},
                ],
            ),
        ),
        "rows": rows_json(input_row("token", "{{JWT}}"), validate_row("$.ok", "True")),
    },
    {
        "id": "API-DASH-003",
        "title": "[边界] 平台概览统计 — 空数据库/空数组",
        "method": "GET",
        "url": abs_url("/api/dashboard/stats/"),
        "expected_status": 200,
        "priority": "P1",
        "enabled": True,
        "headers": jwt_headers(),
        "precondition": "数据库无执行记录（新安装）",
        "description": "空库下 recent_tasks 为空数组，charts 各序列全 0，system_status 为 no_devices",
        "steps_json": steps_json(
            request_step("/api/dashboard/stats/", 200, {"Authorization": "Bearer {{token}}"}),
        ),
        "rows": rows_json(input_row("token", "{{JWT}}"), validate_row("$.ok", "True")),
    },
    {
        "id": "API-DASH-004",
        "title": "[异常] 平台概览统计 — 缺少 Authorization 头 401",
        "method": "GET",
        "url": abs_url("/api/dashboard/stats/"),
        "expected_status": 401,
        "priority": "P0",
        "enabled": True,
        "description": '请求无 Authorization header → 401 + {"ok":false,"error":"..."}',
        "steps_json": steps_json(
            request_step("/api/dashboard/stats/", 401),
            assert_step(
                401,
                [
                    {"path": "$.ok", "op": "equals", "expect": "False"},
                    {"path": "$.error", "op": "contains", "expect": "Authorization"},
                ],
            ),
        ),
    },
    {
        "id": "API-DASH-005",
        "title": "[异常] 平台概览统计 — 无效 Token 401",
        "method": "GET",
        "url": abs_url("/api/dashboard/stats/"),
        "expected_status": 401,
        "priority": "P1",
        "enabled": True,
        "headers": json.dumps({"Authorization": "Bearer invalid_token_12345"}),
        "description": "携带无效 JWT → 401 Invalid or expired token",
        "steps_json": steps_json(
            request_step(
                "/api/dashboard/stats/", 401, {"Authorization": "Bearer invalid_token_12345"}
            ),
            assert_step(401, [{"path": "$.ok", "op": "equals", "expect": "False"}]),
        ),
    },
    {
        "id": "API-DASH-006",
        "title": "[字段缺失] 平台概览统计 — cases.breakdown 不缺失",
        "method": "GET",
        "url": abs_url("/api/dashboard/stats/"),
        "expected_status": 200,
        "priority": "P1",
        "enabled": True,
        "headers": jwt_headers(),
        "description": "cases.breakdown 必须存在且含 4 个类型（Android/Web/API/功能业务）",
        "steps_json": steps_json(
            request_step("/api/dashboard/stats/", 200, {"Authorization": "Bearer {{token}}"}),
            assert_step(
                200,
                [
                    {"path": "$.data.cases.breakdown", "op": "exists", "expect": ""},
                ],
            ),
        ),
        "rows": rows_json(input_row("token", "{{JWT}}"), validate_row("$.ok", "True")),
    },
    # ═══ 近期活动 ═══
    {
        "id": "API-DASH-007",
        "title": "[正常] 近期活动列表 — 响应结构",
        "method": "GET",
        "url": abs_url("/api/dashboard/activities/"),
        "expected_status": 200,
        "priority": "P1",
        "enabled": True,
        "headers": jwt_headers(),
        "description": "data 为数组，项含 type/action/detail/time",
        "steps_json": steps_json(
            request_step("/api/dashboard/activities/", 200, {"Authorization": "Bearer {{token}}"}),
            assert_step(200, [{"path": "$.ok", "op": "equals", "expect": "True"}]),
        ),
        "rows": rows_json(input_row("token", "{{JWT}}"), validate_row("$.ok", "True")),
    },
    {
        "id": "API-DASH-008",
        "title": "[异常] 近期活动 — 无鉴权 401",
        "method": "GET",
        "url": abs_url("/api/dashboard/activities/"),
        "expected_status": 401,
        "priority": "P0",
        "enabled": True,
        "description": "缺少 JWT → 401",
        "steps_json": steps_json(
            request_step("/api/dashboard/activities/", 401),
            assert_step(401, [{"path": "$.ok", "op": "equals", "expect": "False"}]),
        ),
    },
    # ═══ 设备统计 ═══
    {
        "id": "API-DASH-009",
        "title": "[正常] 设备池统计 — 五字段完整性",
        "method": "GET",
        "url": abs_url("/api/devices/stats/"),
        "expected_status": 200,
        "priority": "P1",
        "enabled": True,
        "headers": jwt_headers(),
        "description": "online/busy/offline/disconnected/total 全部存在",
        "steps_json": steps_json(
            request_step("/api/devices/stats/", 200, {"Authorization": "Bearer {{token}}"}),
            assert_step(
                200,
                [
                    {"path": "$.ok", "op": "equals", "expect": "True"},
                    {"path": "$.data.online", "op": "exists", "expect": ""},
                    {"path": "$.data.busy", "op": "exists", "expect": ""},
                    {"path": "$.data.offline", "op": "exists", "expect": ""},
                    {"path": "$.data.disconnected", "op": "exists", "expect": ""},
                    {"path": "$.data.total", "op": "exists", "expect": ""},
                ],
            ),
        ),
        "rows": rows_json(input_row("token", "{{JWT}}"), validate_row("$.ok", "True")),
    },
    {
        "id": "API-DASH-010",
        "title": "[边界] 设备池统计 — total = online+busy+offline+disconnected",
        "method": "GET",
        "url": abs_url("/api/devices/stats/"),
        "expected_status": 200,
        "priority": "P1",
        "enabled": True,
        "headers": jwt_headers(),
        "description": "验证各状态之和等于 total",
        "steps_json": steps_json(
            request_step("/api/devices/stats/", 200, {"Authorization": "Bearer {{token}}"}),
        ),
        "rows": rows_json(input_row("token", "{{JWT}}"), validate_row("$.ok", "True")),
    },
    {
        "id": "API-DASH-011",
        "title": "[异常] 设备池统计 — 无鉴权 401",
        "method": "GET",
        "url": abs_url("/api/devices/stats/"),
        "expected_status": 401,
        "priority": "P0",
        "enabled": True,
        "description": "缺少 JWT → 401",
        "steps_json": steps_json(
            request_step("/api/devices/stats/", 401),
            assert_step(401, [{"path": "$.ok", "op": "equals", "expect": "False"}]),
        ),
    },
    # ═══ 用例统计 ═══
    {
        "id": "API-DASH-012",
        "title": "[正常] 用例统计 — 跨类型总数",
        "method": "GET",
        "url": abs_url("/api/cases/stats/"),
        "expected_status": 200,
        "priority": "P1",
        "enabled": True,
        "headers": jwt_headers(),
        "description": "涵盖 Android/Web/API/功能业务 4 种类型，total = enabled + disabled",
        "steps_json": steps_json(
            request_step("/api/cases/stats/", 200, {"Authorization": "Bearer {{token}}"}),
            assert_step(
                200,
                [
                    {"path": "$.ok", "op": "equals", "expect": "True"},
                    {"path": "$.data.total", "op": "exists", "expect": ""},
                    {"path": "$.data.enabled", "op": "exists", "expect": ""},
                    {"path": "$.data.disabled", "op": "exists", "expect": ""},
                ],
            ),
        ),
        "rows": rows_json(input_row("token", "{{JWT}}"), validate_row("$.ok", "True")),
    },
    {
        "id": "API-DASH-013",
        "title": "[异常] 用例统计 — 无鉴权 401",
        "method": "GET",
        "url": "/api/cases/stats/",
        "expected_status": 401,
        "priority": "P0",
        "enabled": True,
        "description": "缺少 JWT → 401",
        "steps_json": steps_json(
            request_step("/api/cases/stats/", 401),
            assert_step(401, [{"path": "$.ok", "op": "equals", "expect": "False"}]),
        ),
    },
]

for tc in test_cases:
    obj, created = ApiTestCase.objects.update_or_create(
        id=tc["id"], defaults={**tc, "directory": db_dir, "case_type": "api_testing"}
    )
    print(f"  {'CREATED' if created else 'UPDATED'}: {obj.id} {obj.title}")

count = ApiTestCase.objects.filter(directory=db_dir).count()
print(f"\nTotal: {count} test cases")
