"""Dashboard stats views — aggregated platform statistics for the frontend dashboard."""

import logging

from datetime import timedelta

from django.db import OperationalError, ProgrammingError
from django.db.models import Count, Max, Q
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from apps.ai_assistant.models import AIAgent
from apps.case_manager.models import ApiTestCase, StorageTestCase, TestDefinition
from apps.case_manager.models_web import WebTestCase
from apps.device_pool.models import Device
from apps.element_locator.models import ApiEndpoint, Element, Page, WebElement
from apps.report_generator.models import Report
from apps.test_runner.models import TestResult, TestRunRecord
from apps.workflow.models import WorkflowDocument

logger = logging.getLogger(__name__)


def _safe_count(queryset_or_model, filter_kwargs=None):
    """Safely count records, returning 0 if the table doesn't exist yet."""
    try:
        qs = (
            queryset_or_model.objects.all()
            if hasattr(queryset_or_model, "objects")
            else queryset_or_model
        )
        if filter_kwargs:
            qs = qs.filter(**filter_kwargs)
        return qs.count()
    except (OperationalError, ProgrammingError) as e:
        logger.debug("Safe count fallback for %s: %s", str(queryset_or_model)[:80], e)
        return 0


def _safe_pct(part, total):
    """Return percentage as float, 0 if total is 0."""
    if total == 0:
        return 0
    return round(part / total * 100, 1)


def _daily_counts(queryset, date_field, days=12):
    """Group a queryset by day for the last N days; returns a list of daily counts."""
    cutoff = timezone.now() - timedelta(days=days)
    daily = (
        queryset.filter(**{f"{date_field}__gte": cutoff})
        .extra(select={"day": f"date({date_field})"})
        .values("day")
        .annotate(cnt=Count("id"))
        .order_by("day")
    )
    by_day = {}
    for row in daily:
        key = str(row["day"])[:10]  # 'YYYY-MM-DD'
        by_day[key] = row["cnt"]
    series = []
    for i in range(days):
        d = (timezone.now() - timedelta(days=days - 1 - i)).date().isoformat()
        series.append(by_day.get(d, 0))
    return series


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


def _cases_breakdown():
    """Return per-type case breakdown for the dashboard."""
    return [
        {
            "type": "ui_automation",
            "label": "Android",
            "total": TestDefinition.objects.count(),
            "enabled": TestDefinition.objects.filter(enabled=True).count(),
        },
        {
            "type": "web_automation",
            "label": "Web",
            "total": _safe_count(WebTestCase),
            "enabled": _safe_count(WebTestCase, {"enabled": True}),
        },
        {
            "type": "api_testing",
            "label": "API",
            "total": _safe_count(ApiTestCase),
            "enabled": _safe_count(ApiTestCase, {"enabled": True}),
        },
        {
            "type": "storage",
            "label": "功能业务",
            "total": _safe_count(StorageTestCase),
            "enabled": _safe_count(StorageTestCase, {"enabled": True}),
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
    """Return workflow document counts."""
    total = _safe_count(WorkflowDocument)
    page_flows = _safe_count(WorkflowDocument, {"doc_type": "page_flow"})
    test_cases = _safe_count(WorkflowDocument, {"doc_type": "test_case"})
    return {"total": total, "page_flows": page_flows, "test_cases": test_cases}


def _daily_execution_series(days=12):
    """Daily success / failed executions and newly created cases."""
    labels, success, failed, new_cases = [], [], [], []
    for i in range(days):
        day_start = timezone.now() - timedelta(days=days - 1 - i)
        day_start = day_start.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        labels.append(day_start.strftime("%m/%d"))
        success.append(
            TestResult.objects.filter(
                PASS_Q, created_at__gte=day_start, created_at__lt=day_end
            ).count()
        )
        failed.append(
            TestResult.objects.filter(
                FAIL_Q, created_at__gte=day_start, created_at__lt=day_end
            ).count()
        )
        new_cases.append(
            TestDefinition.objects.filter(created_at__gte=day_start, created_at__lt=day_end).count()
        )
    return {"labels": labels, "success": success, "failed": failed, "new_cases": new_cases}


def _case_result_status(passed, failed):
    if passed == 0 and failed == 0:
        return "idle"
    if failed == 0:
        return "success"
    if passed == 0:
        return "failed"
    return "partial"


def _recent_tasks(limit=8):
    """Recent case execution summaries + active runs."""
    tasks = []

    try:
        from apps.test_runner.api import get_active_runs_info

        for info in get_active_runs_info():
            case_titles = {}
            for cid in info.get("selected_cases", []):
                try:
                    case_titles[cid] = TestDefinition.objects.get(id=cid).title
                except TestDefinition.DoesNotExist:
                    case_titles[cid] = cid
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
    for row in recent_cases:
        cid = row["case_id"]
        last = row["last"]
        window_start = last - timedelta(hours=2)
        qs = TestResult.objects.filter(
            case_id=cid, created_at__gte=window_start, created_at__lte=last
        )
        passed = qs.filter(PASS_Q).count()
        failed = qs.filter(FAIL_Q).count()
        if passed == 0 and failed == 0:
            continue
        try:
            title = TestDefinition.objects.get(id=cid).title
        except TestDefinition.DoesNotExist:
            title = cid
        status = _case_result_status(passed, failed)
        tasks.append(
            {
                "id": cid,
                "title": title,
                "status": status,
                "passed": passed,
                "failed": failed,
                "total": passed + failed,
                "time": last.strftime("%Y-%m-%d %H:%M"),
                "cases": [{"title": title, "status": status, "passed": passed, "failed": failed}],
            }
        )

    return tasks[:limit]


@csrf_exempt
def dashboard_stats(request):
    """GET /api/dashboard/stats/ — platform-level statistics."""
    device_online, device_total = _device_dashboard_stats()
    case_total = (
        TestDefinition.objects.count()
        + _safe_count(StorageTestCase)
        + _safe_count(ApiTestCase)
        + _safe_count(WebTestCase)
    )
    case_enabled = (
        TestDefinition.objects.filter(enabled=True).count()
        + _safe_count(StorageTestCase, {"enabled": True})
        + _safe_count(ApiTestCase, {"enabled": True})
        + _safe_count(WebTestCase, {"enabled": True})
    )
    run_total = TestRunRecord.objects.count()
    run_active = TestRunRecord.objects.filter(status="RUNNING").count()
    agent_total = AIAgent.objects.count()
    agent_active = AIAgent.objects.filter(status="active").count()

    # Pass rate from test results (field is 'result', not 'status')
    result_total = TestResult.objects.count()
    result_passed = TestResult.objects.filter(PASS_Q).count()
    result_failed = TestResult.objects.filter(FAIL_Q).count()
    pass_rate = _safe_pct(result_passed, result_total)

    # Trend series (last 12 days)
    # TestRunRecord.started_at is CharField, so we use TestResult.created_at (DateTimeField) for activity trend
    activity_trend = _daily_counts(TestResult.objects, "created_at")
    case_trend = _daily_counts(TestDefinition.objects, "created_at")

    # Pass-rate trend per day
    pass_trend = []
    for i in range(12):
        day_start = timezone.now() - timedelta(days=12 - 1 - i)
        day_end = day_start + timedelta(days=1)
        day_total = TestResult.objects.filter(
            created_at__gte=day_start, created_at__lt=day_end
        ).count()
        day_passed = TestResult.objects.filter(
            PASS_Q,
            created_at__gte=day_start,
            created_at__lt=day_end,
        ).count()
        pass_trend.append(_safe_pct(day_passed, day_total))

    # Trends — this week's new items
    week_ago = timezone.now() - timedelta(days=7)
    case_trend_num = (
        TestDefinition.objects.filter(created_at__gte=week_ago).count()
        + _safe_count(StorageTestCase, {"created_at__gte": week_ago})
        + _safe_count(ApiTestCase, {"created_at__gte": week_ago})
        + _safe_count(WebTestCase, {"created_at__gte": week_ago})
    )
    # Device activity = runs this week
    device_trend_num = TestResult.objects.filter(created_at__gte=week_ago).count()

    # ── Elements: per-page breakdown from element-manager (el_pages + el_elements) ──
    element_total = Element.objects.count() + _safe_count(WebElement) + _safe_count(ApiEndpoint)
    pages_qs = Page.objects.annotate(live_count=Count("elements")).order_by("-live_count")
    element_breakdown = [
        {
            "page_name": p.label or f"页面 #{p.id}",
            "package": p.package or "",
            "element_count": p.live_count,
            "page_id": p.id,
        }
        for p in pages_qs
    ]

    return JsonResponse(
        {
            "ok": True,
            "data": {
                "devices": {
                    "online": device_online,
                    "total": device_total,
                    "trend": device_trend_num,
                },
                "cases": {
                    "total": case_total,
                    "enabled": case_enabled,
                    "trend": case_trend_num,
                    "breakdown": _cases_breakdown(),
                },
                "elements": {
                    "total": element_total,
                    "pages": len(element_breakdown),
                    "breakdown": element_breakdown,
                    "type_breakdown": _elements_breakdown(),
                },
                "workflow": _workflow_stats(),
                "runs": {
                    "total": run_total,
                    "active": run_active,
                    "trend": run_total,
                },
                "agents": {
                    "total": agent_total,
                    "active": agent_active,
                    "trend": agent_active,
                },
                "reports": {
                    "total": Report.objects.count(),
                },
                "pass_rate": pass_rate,
                "charts": {
                    "devices": activity_trend if sum(activity_trend) > 0 else [1] * 12,
                    "cases": case_trend if sum(case_trend) > 0 else [1] * 12,
                    "pass_rate": pass_trend if sum(pass_trend) > 0 else [0] * 12,
                    "execution": _daily_execution_series(),
                },
                "execution_summary": {
                    "passed": result_passed,
                    "failed": result_failed,
                    "new_cases_week": case_trend_num,
                },
                "recent_tasks": _recent_tasks(),
                "last_updated": timezone.now().strftime("%Y-%m-%d %H:%M"),
                "system_status": "normal"
                if device_online > 0 or device_total == 0
                else "no_devices",
            },
        }
    )


@csrf_exempt
def dashboard_activities(request):
    """GET /api/dashboard/activities/ — recent events across the platform."""
    items = []

    # Recent test runs (started_at is CharField, order by id desc as fallback)
    for run in TestRunRecord.objects.order_by("-id")[:5]:
        items.append(
            {
                "type": "run",
                "action": f"测试执行: {run.run_id}",
                "detail": f"设备: {run.device_serial} · 状态: {run.status}",
                "time": run.started_at if run.started_at else "",
            }
        )

    # Recent agents
    for agent in AIAgent.objects.order_by("-updated_at")[:3]:
        items.append(
            {
                "type": "agent",
                "action": f"智能体更新: {agent.name}",
                "detail": f"模型: {agent.model_provider}/{agent.model_name}",
                "time": agent.updated_at.strftime("%Y-%m-%d %H:%M"),
            }
        )

    items.sort(key=lambda x: x.get("time", ""), reverse=True)
    return JsonResponse({"ok": True, "data": items[:10]})


@csrf_exempt
def device_stats(request):
    """GET /api/devices/stats/ — device pool summary."""
    online, total = _device_dashboard_stats()
    return JsonResponse(
        {
            "ok": True,
            "data": {
                "online": online,
                "busy": Device.objects.filter(status="BUSY").count(),
                "offline": Device.objects.filter(status="OFFLINE").count(),
                "disconnected": Device.objects.filter(status="DISCONNECTED").count(),
                "total": total,
            },
        }
    )


@csrf_exempt
def case_stats(request):
    """GET /api/cases/stats/ — test case summary."""
    return JsonResponse(
        {
            "ok": True,
            "data": {
                "total": TestDefinition.objects.count()
                + _safe_count(StorageTestCase)
                + _safe_count(ApiTestCase)
                + _safe_count(WebTestCase),
                "enabled": (
                    TestDefinition.objects.filter(enabled=True).count()
                    + _safe_count(StorageTestCase, {"enabled": True})
                    + _safe_count(ApiTestCase, {"enabled": True})
                    + _safe_count(WebTestCase, {"enabled": True})
                ),
                "disabled": (
                    TestDefinition.objects.filter(enabled=False).count()
                    + _safe_count(StorageTestCase, {"enabled": False})
                    + _safe_count(ApiTestCase, {"enabled": False})
                    + _safe_count(WebTestCase, {"enabled": False})
                ),
            },
        }
    )
