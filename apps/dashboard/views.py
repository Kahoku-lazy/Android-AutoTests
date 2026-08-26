"""Dashboard stats views — aggregated platform statistics for the frontend dashboard."""

import logging

from datetime import timedelta

from django.db import OperationalError, ProgrammingError
from django.db.models import Count, Max, Q
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai_assistant.api import filter_agents_for_user
from apps.ai_assistant.models import AIAgent
from apps.case_manager.models import ApiTestCase, StorageTestCase, TestDefinition
from apps.case_manager.models_web import WebTestCase
from apps.dashboard.ai_usage import ai_daily_series, ai_usage_stats
from apps.device_pool.models import Device
from apps.element_locator.models import ApiEndpoint, Element, Page, WebElement
from apps.test_runner.models import TestResult, TestRunRecord
from apps.workflow.models import WorkflowDocument
from shared.users import resolve_username as _resolve_username

logger = logging.getLogger(__name__)


def _user_id(request):
    """Extract authenticated user id from a DRF request."""
    user = getattr(request, "user", None)
    return user.id if user else None


def _safe_count(queryset_or_model, filter_kwargs=None, q_filter=None):
    """Safely count records, returning 0 if the table doesn't exist yet."""
    try:
        qs = (
            queryset_or_model.objects.all()
            if hasattr(queryset_or_model, "objects")
            else queryset_or_model
        )
        if filter_kwargs:
            qs = qs.filter(**filter_kwargs)
        if q_filter:
            qs = qs.filter(q_filter)
        return qs.count()
    except (OperationalError, ProgrammingError) as e:
        logger.debug("Safe count fallback for %s: %s", str(queryset_or_model)[:80], e)
        return 0


def _visibility_q(user_id):
    """Build a Q object for case visibility filtering, matching handle_get_definitions."""
    current_user = _resolve_username(user_id)
    q = Q(visibility="public")
    if current_user:
        q |= Q(created_by=current_user)
        q |= Q(visibility="restricted") & Q(permitted_users__contains=f'"{current_user}"')
    else:
        q |= Q(created_by="")
    return q


PASS_Q = Q(result__iexact="pass") | Q(result__iexact="passed")
FAIL_Q = Q(result__iexact="fail") | Q(result__iexact="failed")

# Match device-pool UI: hide stale OFFLINE / DISCONNECTED records from totals
_VISIBLE_DEVICE_STATUSES = ("ONLINE", "BUSY")
_HIDDEN_DEVICE_STATUSES = ("OFFLINE", "DISCONNECTED")


def _device_dashboard_stats():
    """Return (online, total) consistent with /devices list filtering."""
    visible = Device.objects.exclude(status__in=_HIDDEN_DEVICE_STATUSES)
    total = visible.count()
    online = visible.filter(status__in=_VISIBLE_DEVICE_STATUSES).count()
    return online, total


def _cases_breakdown(user_id=None):
    """Return per-type case breakdown for the dashboard, with visibility filtering."""
    vq = _visibility_q(user_id)
    return [
        {
            "type": "ui_automation",
            "label": "Android",
            "total": TestDefinition.objects.filter(vq).count(),
            "enabled": TestDefinition.objects.filter(vq, enabled=True).count(),
        },
        {
            "type": "web_automation",
            "label": "Web",
            "total": _safe_count(WebTestCase, q_filter=vq),
            "enabled": _safe_count(WebTestCase, {"enabled": True}, q_filter=vq),
        },
        {
            "type": "api_testing",
            "label": "API",
            "total": _safe_count(ApiTestCase, q_filter=vq),
            "enabled": _safe_count(ApiTestCase, {"enabled": True}, q_filter=vq),
        },
        {
            "type": "storage",
            "label": "功能业务",
            "total": _safe_count(StorageTestCase, q_filter=vq),
            "enabled": _safe_count(StorageTestCase, {"enabled": True}, q_filter=vq),
        },
    ]


def _elements_breakdown():
    """Return per-type element breakdown (Android / Web / API)."""
    return [
        {"type": "android", "label": "Android元素", "total": Element.objects.count()},
        {"type": "web", "label": "Web元素", "total": _safe_count(WebElement)},
        {"type": "api", "label": "API接口", "total": _safe_count(ApiEndpoint)},
    ]


def _workflow_stats():
    """Return workflow document count."""
    return {"total": _safe_count(WorkflowDocument)}


def _daily_bucket_counts(queryset, days=12):
    """Group a queryset into `days` calendar-day buckets (midnight-aligned), zero-filled.

    One grouped SQL query replaces N per-day count() calls; buckets match the
    per-day [00:00, 24:00) windows of the original loop implementation.
    """
    first_day = (timezone.now() - timedelta(days=days - 1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    daily = (
        queryset.filter(created_at__gte=first_day)
        .extra(select={"day": "date(created_at)"})
        .values("day")
        .annotate(cnt=Count("id"))
    )
    by_day = {str(row["day"])[:10]: row["cnt"] for row in daily}
    series = []
    for i in range(days):
        day = (first_day + timedelta(days=i)).date().isoformat()
        series.append(by_day.get(day, 0))
    return series


def _daily_execution_series(days=12):
    """Daily success / failed executions (2 grouped queries)."""
    labels = [
        (timezone.now() - timedelta(days=days - 1 - i)).strftime("%m/%d") for i in range(days)
    ]
    success = _daily_bucket_counts(TestResult.objects.filter(PASS_Q), days)
    failed = _daily_bucket_counts(TestResult.objects.filter(FAIL_Q), days)
    return {"labels": labels, "success": success, "failed": failed}


def _case_result_status(passed, failed):
    if passed == 0 and failed == 0:
        return "idle"
    if failed == 0:
        return "success"
    if passed == 0:
        return "failed"
    return "partial"


def _case_titles(case_ids: set) -> dict:
    """Batch-fetch case titles by id; missing ids fall back to the id itself."""
    if not case_ids:
        return {}
    return {
        row["id"]: row["title"]
        for row in TestDefinition.objects.filter(id__in=case_ids).values("id", "title")
    }


def _recent_tasks(limit=8):
    """Recent case execution summaries + active runs."""
    tasks = []

    try:
        from apps.test_runner.api import get_active_runs_info

        active_infos = list(get_active_runs_info())
        selected_ids = {cid for info in active_infos for cid in info.get("selected_cases", [])}
        case_titles = _case_titles(selected_ids)
        for info in active_infos:
            tasks.append(
                {
                    "id": info["run_id"],
                    "title": f"执行中 · {info.get('device_serial') or '设备'}",
                    "status": "running",
                    "passed": 0,
                    "failed": 0,
                    "total": 0,
                    "time": (info.get("started_at") or "")[:16].replace("T", " "),
                    "cases": [
                        {
                            "title": case_titles.get(cid, cid),
                            "status": "running",
                            "passed": 0,
                            "failed": 0,
                        }
                        for cid in info.get("selected_cases", [])
                    ],
                }
            )
    except Exception:
        logger.exception("Failed to fetch active runs for recent tasks")

    recent_cases = (
        TestResult.objects.values("case_id")
        .annotate(last=Max("created_at"))
        .order_by("-last")[:limit]
    )
    rows = list(recent_cases)
    if not rows:
        return tasks

    # Batched: one title query + one results query; per-case 2h windows applied in Python.
    titles = _case_titles({row["case_id"] for row in rows})
    min_start = min(row["last"] for row in rows) - timedelta(hours=2)
    windows = {row["case_id"]: row["last"] - timedelta(hours=2) for row in rows}
    results = TestResult.objects.filter(
        case_id__in=windows.keys(), created_at__gte=min_start
    ).values_list("case_id", "result", "created_at")
    passed_map, failed_map = {}, {}
    for cid, result, created in results:
        if created < windows[cid]:
            continue
        if result.lower() in ("pass", "passed"):
            passed_map[cid] = passed_map.get(cid, 0) + 1
        elif result.lower() in ("fail", "failed"):
            failed_map[cid] = failed_map.get(cid, 0) + 1
    for row in rows:
        cid = row["case_id"]
        passed = passed_map.get(cid, 0)
        failed = failed_map.get(cid, 0)
        if passed == 0 and failed == 0:
            continue
        title = titles.get(cid, cid)
        status = _case_result_status(passed, failed)
        tasks.append(
            {
                "id": cid,
                "title": title,
                "status": status,
                "passed": passed,
                "failed": failed,
                "total": passed + failed,
                "time": row["last"].strftime("%Y-%m-%d %H:%M"),
                "cases": [{"title": title, "status": status, "passed": passed, "failed": failed}],
            }
        )

    return tasks[:limit]


class DashboardStatsAPIView(APIView):
    """GET /api/dashboard/stats/ — platform-level statistics."""

    def get(self, request):
        user_id = _user_id(request)

        device_online, device_total = _device_dashboard_stats()
        # Totals derive from breakdown (single source of truth — no double counting)
        cases_breakdown = _cases_breakdown(user_id)
        case_total = sum(row["total"] for row in cases_breakdown)
        case_enabled = sum(row["enabled"] for row in cases_breakdown)
        run_total = TestRunRecord.objects.count()
        run_active = TestRunRecord.objects.filter(status="RUNNING").count()
        agent_total = filter_agents_for_user(AIAgent.objects.all(), user_id).count()
        agent_active = (
            filter_agents_for_user(AIAgent.objects.all(), user_id).filter(status="active").count()
        )

        # Pass/fail totals from test results (field is 'result', not 'status')
        result_passed = TestResult.objects.filter(PASS_Q).count()
        result_failed = TestResult.objects.filter(FAIL_Q).count()

        # ── Elements: totals + page count ──
        elements_breakdown = _elements_breakdown()
        element_total = sum(row["total"] for row in elements_breakdown)
        pages_count = _safe_count(Page)

        # ── AI 用量 + 每日 token/缓存/费用序列 ──
        daily_ai = ai_daily_series(user_id)

        return Response(
            {
                "devices": {"online": device_online, "total": device_total},
                "cases": {
                    "total": case_total,
                    "enabled": case_enabled,
                    "breakdown": cases_breakdown,
                },
                "elements": {
                    "total": element_total,
                    "pages": pages_count,
                    "type_breakdown": elements_breakdown,
                },
                "workflow": _workflow_stats(),
                "runs": {"total": run_total, "active": run_active},
                "agents": {"total": agent_total, "active": agent_active},
                "ai_usage": ai_usage_stats(user_id),
                "charts": {
                    "execution": _daily_execution_series(),
                    "ai_tokens": {
                        "labels": daily_ai["labels"],
                        "total_tokens": daily_ai["total_tokens"],
                        "cache_tokens": daily_ai["cache_tokens"],
                    },
                    "deepseek_cost": {
                        "labels": daily_ai["labels"],
                        "cost": daily_ai["deepseek_cost"],
                    },
                },
                "execution_summary": {"passed": result_passed, "failed": result_failed},
                "recent_tasks": _recent_tasks(),
                "last_updated": timezone.now().strftime("%Y-%m-%d %H:%M"),
                "system_status": "normal"
                if device_online > 0 or device_total == 0
                else "no_devices",
            }
        )


class DashboardActivitiesAPIView(APIView):
    """GET /api/dashboard/activities/ — recent events across the platform."""

    def get(self, request):
        items = []

        # Recent test runs (started_at is CharField, order by id desc as fallback)
        for run in TestRunRecord.objects.order_by("-id")[:5]:
            items.append(
                {
                    "type": "run",
                    "action": f"测试执行: {run.run_id}",
                    "detail": f"设备: {run.device_serial} · 状态: {run.status}",
                    # 归一化为 16 字符（PRD §5.3：固定 YYYY-MM-DD HH:MM）
                    "time": (run.started_at or "")[:16].replace("T", " "),
                }
            )

        # Recent agents
        user_id = _user_id(request)
        for agent in filter_agents_for_user(AIAgent.objects.all(), user_id).order_by("-updated_at")[
            :3
        ]:
            items.append(
                {
                    "type": "agent",
                    "action": f"智能体更新: {agent.name}",
                    "detail": f"模型: {agent.model_provider}/{agent.model_name}",
                    "time": agent.updated_at.strftime("%Y-%m-%d %H:%M"),
                }
            )

        items.sort(key=lambda x: x.get("time", ""), reverse=True)
        return Response(items[:10])


class DeviceStatsAPIView(APIView):
    """GET /api/devices/stats/ — device pool summary."""

    def get(self, request):
        online, total = _device_dashboard_stats()
        return Response(
            {
                "online": online,
                "busy": Device.objects.filter(status="BUSY").count(),
                "offline": Device.objects.filter(status="OFFLINE").count(),
                "disconnected": Device.objects.filter(status="DISCONNECTED").count(),
                "total": total,
            }
        )


class CaseStatsAPIView(APIView):
    """GET /api/cases/stats/ — test case summary."""

    def get(self, request):
        user_id = _user_id(request)
        vq = _visibility_q(user_id)
        return Response(
            {
                "total": TestDefinition.objects.filter(vq).count()
                + _safe_count(StorageTestCase, q_filter=vq)
                + _safe_count(ApiTestCase, q_filter=vq)
                + _safe_count(WebTestCase, q_filter=vq),
                "enabled": (
                    TestDefinition.objects.filter(vq, enabled=True).count()
                    + _safe_count(StorageTestCase, {"enabled": True}, q_filter=vq)
                    + _safe_count(ApiTestCase, {"enabled": True}, q_filter=vq)
                    + _safe_count(WebTestCase, {"enabled": True}, q_filter=vq)
                ),
                "disabled": (
                    TestDefinition.objects.filter(vq, enabled=False).count()
                    + _safe_count(StorageTestCase, {"enabled": False}, q_filter=vq)
                    + _safe_count(ApiTestCase, {"enabled": False}, q_filter=vq)
                    + _safe_count(WebTestCase, {"enabled": False}, q_filter=vq)
                ),
            }
        )
