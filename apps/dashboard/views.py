"""Dashboard stats views — aggregated platform statistics for the frontend dashboard."""

import logging

from datetime import timedelta

from django.db import OperationalError, ProgrammingError
from django.db.models import Q
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai_assistant.api import filter_agents_for_user
from apps.ai_assistant.models import AIAgent
from apps.case_manager.models import CaseProject, TestDefinition
from apps.dashboard.ai_usage import ai_daily_series, ai_usage_stats
from apps.device_pool.models import Device
from apps.element_locator.models import ApiEndpoint, Element, Page, WebElement
from apps.workflow.models import WorkflowDocument

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


def _user_cases_q(user_id):
    """Filter document cases owned via project.created_by."""
    uid = str(user_id) if user_id is not None else ""
    return Q(project__created_by=uid)


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
    """Return per test_type breakdown for document cases owned by the user."""
    cq = _user_cases_q(user_id)
    labels = {"app": "APP", "web": "WEB", "api": "API", "func": "FUNC"}
    rows = []
    for key, label in labels.items():
        total = _safe_count(TestDefinition, {"test_type": key}, q_filter=cq)
        rows.append({"type": key, "label": label, "total": total, "enabled": total})
    return rows


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


def _daily_execution_series(days=12):
    """Daily success / failed executions. Execution engine removed — always zeros."""
    labels = [
        (timezone.now() - timedelta(days=days - 1 - i)).strftime("%m/%d") for i in range(days)
    ]
    zeros = [0] * days
    return {"labels": labels, "success": zeros, "failed": zeros}


def _recent_tasks(_limit=8):
    """Recent case execution summaries. Execution engine removed — always empty."""
    return []


class DashboardStatsAPIView(APIView):
    """GET /api/dashboard/stats/ — platform-level statistics."""

    def get(self, request):
        user_id = _user_id(request)

        device_online, device_total = _device_dashboard_stats()
        # Totals derive from breakdown (single source of truth — no double counting)
        cases_breakdown = _cases_breakdown(user_id)
        case_total = sum(row["total"] for row in cases_breakdown)
        case_enabled = sum(row["enabled"] for row in cases_breakdown)
        run_total = 0
        run_active = 0
        agent_total = filter_agents_for_user(AIAgent.objects.all(), user_id).count()
        agent_active = (
            filter_agents_for_user(AIAgent.objects.all(), user_id).filter(status="active").count()
        )

        # Pass/fail totals from test results (field is 'result', not 'status')
        result_passed = 0
        result_failed = 0

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
    """GET /api/cases/stats/ — document case summary."""

    def get(self, request):
        user_id = _user_id(request)
        cq = _user_cases_q(user_id)
        total = _safe_count(TestDefinition, q_filter=cq)
        project_total = _safe_count(CaseProject, {"created_by": str(user_id) if user_id else ""})
        return Response(
            {
                "total": total,
                "enabled": total,
                "disabled": 0,
                "projects": project_total,
            }
        )
