"""Dashboard stats views — aggregated platform statistics for the frontend dashboard."""

import logging

from django.db import OperationalError, ProgrammingError
from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai_assistant.api import filter_agents_for_user
from apps.ai_assistant.models import AIAgent
from apps.case_manager.api import list_projects
from apps.case_manager.models import CaseProject, TestDefinition
from apps.dashboard.ai_usage import (
    ai_daily_series,
    ai_recent_tasks,
    ai_task_daily_execution,
    ai_task_execution_summary,
    ai_usage_stats,
    platform_activities,
)
from apps.device_pool.models import Device
from apps.element_locator.models import Element, Page
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
    """Return per-project breakdown for document cases owned by the user."""
    if user_id is None:
        return []
    projects = list_projects(user_id=str(user_id))
    return [
        {
            "project_id": p["id"],
            "name": p["name"],
            "total": p["case_count"],
        }
        for p in projects
    ]


def _elements_breakdown():
    """Return the element breakdown —— Web/API 两域随元素定位下线，只保留 Android。"""
    return [
        {"type": "android", "label": "Android元素", "total": Element.objects.count()},
    ]


def _workflow_stats():
    """Return workflow document count."""
    return {"total": _safe_count(WorkflowDocument)}


@extend_schema(responses=OpenApiTypes.OBJECT)
class DashboardStatsAPIView(APIView):
    """GET /api/dashboard/stats/ — platform-level statistics."""

    def get(self, request):
        user_id = _user_id(request)

        device_online, device_total = _device_dashboard_stats()
        # Totals derive from breakdown (single source of truth — no double counting)
        cases_breakdown = _cases_breakdown(user_id)
        case_total = sum(row["total"] for row in cases_breakdown)
        case_enabled = case_total  # 文档用例无独立 enabled，与 total 同值
        run_total = 0
        run_active = 0
        agent_total = filter_agents_for_user(AIAgent.objects.all(), user_id).count()
        agent_active = (
            filter_agents_for_user(AIAgent.objects.all(), user_id).filter(status="active").count()
        )

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
                    "execution": ai_task_daily_execution(user_id),
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
                "execution_summary": ai_task_execution_summary(user_id),
                "recent_tasks": ai_recent_tasks(user_id),
                "last_updated": timezone.now().strftime("%Y-%m-%d %H:%M"),
                "system_status": "normal"
                if device_online > 0 or device_total == 0
                else "no_devices",
            }
        )


def _parse_activity_paging(request):
    """解析 limit/offset；非法时返回 (None, None, message)。"""
    raw_limit = request.query_params.get("limit")
    raw_offset = request.query_params.get("offset")

    if raw_limit is None or raw_limit == "":
        limit = 10
    else:
        try:
            limit = int(raw_limit)
        except (TypeError, ValueError):
            return None, None, "limit 必须是整数"
        if limit < 1 or limit > 50:
            return None, None, "limit 须为 1–50 的整数"

    if raw_offset is None or raw_offset == "":
        offset = 0
    else:
        try:
            offset = int(raw_offset)
        except (TypeError, ValueError):
            return None, None, "offset 必须是非负整数"
        if offset < 0:
            return None, None, "offset 必须是非负整数"

    return limit, offset, None


# 该视图直接返回 list（活动条目数组），故用 ANY 描述，避免声明成 object
@extend_schema(responses=OpenApiTypes.ANY)
class DashboardActivitiesAPIView(APIView):
    """GET /api/dashboard/activities/ — recent events across the platform.

    查询参数：limit（缺省 10，最大 50）、offset（缺省 0）。
    data 仍为活动数组（非对象包裹）。
    """

    def get(self, request):
        limit, offset, err = _parse_activity_paging(request)
        if err:
            return Response({"message": err}, status=400)

        user_id = _user_id(request)
        return Response(platform_activities(user_id, limit=limit, offset=offset))


@extend_schema(responses=OpenApiTypes.OBJECT)
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


@extend_schema(responses=OpenApiTypes.OBJECT)
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
