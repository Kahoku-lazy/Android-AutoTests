from django.contrib.auth import get_user_model
from django.db import OperationalError, ProgrammingError
from django.db.models import Count, Q
from django.utils import timezone
from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.apps.ai_assistant.models import AIAssistant, AIModelConfig, AIRole, AISopWorkflow
from backend.apps.case_manager.api import list_projects
from backend.apps.case_manager.models import AutomationCase, CaseProject, FunctionalCase
from backend.apps.dashboard.ai_usage import (
    ai_daily_series,
    ai_recent_tasks,
    ai_task_daily_execution,
    ai_task_execution_summary,
    ai_today_usage_slots,
    ai_usage_stats,
    platform_activities,
    workflow_task_counts,
)
from backend.apps.device_pool.models import Device
from backend.apps.usage_ledger.api import usage_dashboard
from backend.shared.users import is_operator
from utils.logs import backend_log


def _user_id(request):
    uid = getattr(request, "user_id", None)
    if uid is not None and uid != "":
        return uid
    user = getattr(request, "user", None)
    return user.id if user is not None and getattr(user, "id", None) else None


def _safe_count(queryset_or_model, filter_kwargs=None, q_filter=None):
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
        backend_log.debug("Safe count fallback for %s: %s", str(queryset_or_model)[:80], e)
        return 0


def _user_cases_q(user_id):
    uid = str(user_id) if user_id is not None else ""
    return Q(project__created_by=uid)


_VISIBLE_DEVICE_STATUSES = ("ONLINE", "BUSY")
_HIDDEN_DEVICE_STATUSES = ("OFFLINE", "DISCONNECTED")


def _device_dashboard_stats():
    row = Device.objects.exclude(status__in=_HIDDEN_DEVICE_STATUSES).aggregate(
        total=Count("id"),
        online=Count("id", filter=Q(status__in=_VISIBLE_DEVICE_STATUSES)),
    )
    return int(row["online"] or 0), int(row["total"] or 0)


def _platform_counts():
    return {
        "assistants": _safe_count(AIAssistant),
        "workflows": _safe_count(AISopWorkflow),
        "users": _safe_count(get_user_model()),
        "agents": _safe_count(AIRole),
        "models": _safe_count(AIModelConfig),
    }


def _cases_breakdown(user_id=None):
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


@extend_schema(responses=OpenApiTypes.OBJECT)
class DashboardStatsAPIView(APIView):
    def get(self, request):
        user_id = _user_id(request)

        device_online, device_total = _device_dashboard_stats()
        cases_breakdown = _cases_breakdown(user_id)
        case_total = sum(row["total"] for row in cases_breakdown)
        case_enabled = case_total
        tasks = workflow_task_counts(user_id)
        counts = _platform_counts()

        daily_ai = ai_daily_series(user_id)

        payload = {
            "devices": {"online": device_online, "total": device_total},
            "cases": {
                "total": case_total,
                "enabled": case_enabled,
                "breakdown": cases_breakdown,
            },
            "assistants": {"total": counts["assistants"]},
            "workflows": {"total": counts["workflows"]},
            "runs": {"active": tasks["running"], "pending": tasks["pending"]},
            "ai_usage": ai_usage_stats(user_id),
            "usage_ledger": usage_dashboard(),
            "charts": {
                "execution": ai_task_daily_execution(user_id),
                "ai_tokens": {
                    "labels": daily_ai["labels"],
                    "total_tokens": daily_ai["total_tokens"],
                    "cache_tokens": daily_ai["cache_tokens"],
                    "by_model": daily_ai["by_model"],
                    "voice_by_model": daily_ai["voice_by_model"],
                },
                "deepseek_cost": {
                    "labels": daily_ai["labels"],
                    "cost": daily_ai["deepseek_cost"],
                },
                "today_usage": ai_today_usage_slots(user_id),
            },
            "execution_summary": ai_task_execution_summary(user_id),
            "recent_tasks": ai_recent_tasks(user_id),
            "last_updated": timezone.now().strftime("%Y-%m-%d %H:%M"),
            "system_status": "normal" if device_online > 0 or device_total == 0 else "no_devices",
        }
        if is_operator(user_id):
            payload["ops"] = {
                "users": counts["users"],
                "agents": counts["agents"],
                "models": counts["models"],
            }
        return Response(payload)


def _parse_activity_paging(request):
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


@extend_schema(responses=OpenApiTypes.ANY)
class DashboardActivitiesAPIView(APIView):
    def get(self, request):
        limit, offset, err = _parse_activity_paging(request)
        if err:
            return Response({"message": err}, status=400)

        user_id = _user_id(request)
        return Response(platform_activities(user_id, limit=limit, offset=offset))


@extend_schema(responses=OpenApiTypes.OBJECT)
class DeviceStatsAPIView(APIView):
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
    def get(self, request):
        user_id = _user_id(request)
        cq = _user_cases_q(user_id)
        total = _safe_count(AutomationCase, q_filter=cq) + _safe_count(FunctionalCase, q_filter=cq)
        project_total = _safe_count(CaseProject, {"created_by": str(user_id) if user_id else ""})
        return Response(
            {
                "total": total,
                "enabled": total,
                "disabled": 0,
                "projects": project_total,
            }
        )
