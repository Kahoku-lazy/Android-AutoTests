"""task-list views — task submit/list/detail/rerun/cancel/delete/clear."""

import gzip
import hashlib
import json

from django.core.cache import cache
from django.http import HttpResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.apps.ai_assistant import api as agent_api
from backend.apps.ai_assistant.models import AIAgent
from backend.apps.task_list import api
from backend.apps.task_list.models import Task
from backend.apps.task_list.serializers import TaskSubmitInputSerializer
from backend.apps.task_list.task_reports import build_task_flow, report_cache_meta
from backend.models.constants import TaskKind, TaskStatus

# 任务进入终态后事件不再变化，报告可缓存；运行中任务每轮都可能新增事件，不缓存。
_REPORT_CACHE_TTL = 600
_REPORT_TERMINAL_STATUSES = {"completed", "failed", "interrupted", "cancelled", "stopped"}


def _report_body(payload: dict) -> tuple[bytes, bytes, str]:
    """把报告渲染成信封字节、gzip 字节与 ETag。

    Args:
        payload: 报告数据。

    Returns:
        (明文 JSON 字节, gzip 字节, ETag)。ETag 取明文摘要，与压缩无关。
    """
    raw = json.dumps(
        {"status": True, "data": payload}, ensure_ascii=False, separators=(",", ":"), default=str
    ).encode("utf-8")
    return raw, gzip.compress(raw), hashlib.sha1(raw).hexdigest()


def _visible_task(request, task_id: int) -> Task | None:
    """按当前用户可见的智能体取任务；不可见或不存在返回 None。"""
    user_id = getattr(request, "user_id", None)
    agents = agent_api.filter_agents_for_user(AIAgent.objects.all(), user_id)
    return Task.objects.select_related("agent").filter(id=task_id, agent__in=agents).first()


class TaskSubmitAPIView(APIView):
    """POST /api/tasks/submit — 提交任务；按设备调度（同设备排队 / 异设备并行）。"""

    @extend_schema(request=TaskSubmitInputSerializer, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        serializer = TaskSubmitInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user_id = getattr(request, "user_id", None)
        agent = agent_api.get_agent(data["agent_id"])
        if agent is None:
            raise ValidationError("智能体不存在或不可用")

        title = data["title"]
        goal = (data.get("goal") or "").strip()
        device_serial = (data.get("device_serial") or "").strip()
        device_label = (data.get("device_label") or "").strip()
        case_title = (data.get("case_title") or "").strip()
        task_kind = str(getattr(agent, "task_kind", "") or TaskKind.DEVICE_CONTROL)

        from backend.apps.task_list.attachments import (
            AttachmentError,
            collect_document_files,
            collect_task_files,
            store_flat_upload,
        )

        if task_kind == TaskKind.CASE_AUTHORING:
            try:
                prepared = collect_document_files(request.FILES.getlist("documents"))
            except AttachmentError as exc:
                raise ValidationError(str(exc)) from exc
            task = api.create_task(
                agent,
                title=title,
                goal=goal,
                task_kind=TaskKind.CASE_AUTHORING,
                created_by=str(user_id or ""),
            )
            for index, item in enumerate(prepared):
                api.add_task_attachment(
                    task,
                    kind=item.kind,
                    filename=item.filename,
                    body=item.body,
                    sort_order=index,
                    stored_path=store_flat_upload(item.filename, item.content),
                )
            api.dispatch_case_authoring(task)
            task.refresh_from_db()
            return Response({"id": task.id, "status": task.status, "result": ""})

        if not device_serial:
            raise ValidationError("请选择设备")
        try:
            prepared = collect_task_files(
                request.FILES.getlist("config"),
                request.FILES.getlist("documents"),
            )
        except AttachmentError as exc:
            raise ValidationError(str(exc)) from exc

        task = api.create_task(
            agent,
            title=title,
            goal=goal,
            device_serial=device_serial,
            device_label=device_label,
            case_title=case_title,
            task_kind=TaskKind.DEVICE_CONTROL,
            created_by=str(user_id or ""),
        )
        for index, item in enumerate(prepared):
            api.add_task_attachment(
                task,
                kind=item.kind,
                filename=item.filename,
                body=item.body,
                sort_order=index,
                stored_path=store_flat_upload(item.filename, item.content),
            )
        api.dispatch_device(device_serial)
        task.refresh_from_db()
        return Response({"id": task.id, "status": task.status, "result": ""})


class AgentTaskListAPIView(APIView):
    """GET /api/tasks — 当前用户可见的全部任务发布（设备执行 + 用例编写）。"""

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        user_id = getattr(request, "user_id", None)
        agents = agent_api.filter_agents_for_user(AIAgent.objects.all(), user_id)
        tasks = Task.objects.filter(agent__in=agents).select_related("agent").order_by("-id")[:100]
        return Response({"tasks": [api.serialize_agent_task_row(t) for t in tasks]})


class AgentTaskDeleteAPIView(APIView):
    """POST /api/tasks/{task_id}/delete — 删除任务发布记录。"""

    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, task_id: int):
        task = _visible_task(request, task_id)
        if task is None:
            raise NotFound("任务不存在")
        api.delete_task(task)
        return Response({})


class AgentTaskCancelAPIView(APIView):
    """POST /api/tasks/{task_id}/cancel — 关闭运行中的 SOP。"""

    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, task_id: int):
        task = _visible_task(request, task_id)
        if task is None:
            raise NotFound("任务不存在")
        try:
            task = api.cancel_running_task(task)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response({"id": task.id, "status": task.status})


class AgentTaskRerunAPIView(APIView):
    """POST /api/tasks/{task_id}/rerun — 失败/中断任务克隆新建并调度。"""

    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, task_id: int):
        task = _visible_task(request, task_id)
        if task is None:
            raise NotFound("任务不存在")
        if task.status not in {TaskStatus.FAILED, TaskStatus.INTERRUPTED}:
            raise ValidationError("仅失败或已中断任务可重新执行")
        new_task = api.rerun_task(task)
        if new_task.task_kind == TaskKind.CASE_AUTHORING:
            api.dispatch_case_authoring(new_task)
        else:
            api.dispatch_device(new_task.device_serial or "")
        new_task.refresh_from_db()
        return Response({"id": new_task.id, "status": new_task.status})


class AgentTaskClearAPIView(APIView):
    """POST /api/tasks/clear — 调试：清空当前用户可见的全部任务发布记录。"""

    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        user_id = getattr(request, "user_id", None)
        agents = agent_api.filter_agents_for_user(AIAgent.objects.all(), user_id)
        deleted = 0
        for agent in agents:
            deleted += api.clear_agent_tasks(agent)
        return Response({"deleted": deleted})


class AgentTaskDetailAPIView(APIView):
    """GET /api/tasks/{task_id} — 任务发布详情（过程日志）。"""

    @extend_schema(responses=OpenApiTypes.OBJECT, operation_id="ai_agent_task_detail")
    def get(self, request, task_id: int):
        task = _visible_task(request, task_id)
        if task is None:
            raise NotFound("任务不存在")
        return Response(api.serialize_agent_task_detail(task))


class TaskReportAPIView(APIView):
    """GET /api/tasks/{task_id}/report — 任务事件流程（标准 {status, data} 信封）。

    终态任务的报告按「任务编号 + 最大事件序号」缓存，并给出 ETag；运行中任务每次重建。
    """

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT, 304: None},
        operation_id="task_flow_report",
    )
    def get(self, request, task_id: int):
        user_id = getattr(request, "user_id", None)
        meta = report_cache_meta(user_id, task_id)
        if meta is None:
            raise NotFound("任务不存在")

        status, max_seq = meta
        terminal = status in _REPORT_TERMINAL_STATUSES
        cache_key = f"task-flow:{task_id}:{max_seq}"
        cached = cache.get(cache_key) if terminal else None
        if cached is None:
            payload = build_task_flow(user_id, task_id)
            if payload is None:
                raise NotFound("任务不存在")
            cached = _report_body(payload)
            if terminal:
                cache.set(cache_key, cached, _REPORT_CACHE_TTL)

        raw, zipped, etag = cached
        quoted = f'"{etag}"'
        if (request.headers.get("If-None-Match") or "").replace("W/", "").strip() == quoted:
            response = HttpResponse(status=304)
        elif "gzip" in (request.headers.get("Accept-Encoding") or ""):
            response = HttpResponse(zipped, content_type="application/json")
            response["Content-Encoding"] = "gzip"
        else:
            response = HttpResponse(raw, content_type="application/json")
        response["ETag"] = quoted
        response["Cache-Control"] = "private, max-age=60"
        response["Vary"] = "Authorization, Accept-Encoding"
        return response


class TaskMediaAPIView(APIView):
    """GET /api/tasks/{task_id}/media/{media_id} — 截图缩略图字节（WebP，非信封）。"""

    @extend_schema(
        tags=["tasks"],
        operation_id="task_media",
        responses={(200, "image/webp"): OpenApiTypes.BINARY},
    )
    def get(self, request, task_id: int, media_id: int):
        user_id = getattr(request, "user_id", None)
        media = api.get_task_media(user_id, task_id, media_id)
        if media is None:
            raise NotFound("图片不存在")
        etag = f'"{media["sha256"]}"'
        if request.headers.get("If-None-Match") == etag:
            response = HttpResponse(status=304)
        else:
            response = HttpResponse(media["data"], content_type=media["media_type"])
            response["ETag"] = etag
        response["Cache-Control"] = "private, max-age=31536000, immutable"
        return response


class TaskDrainAPIView(APIView):
    """GET/POST /api/system/drain — 停机排空：只允许本机回环调用。"""

    permission_classes = [AllowAny]

    @staticmethod
    def _require_loopback(request) -> None:
        """拒绝非回环来源，避免把停机开关暴露给局域网。"""
        if request.META.get("REMOTE_ADDR", "") not in ("127.0.0.1", "::1"):
            raise PermissionDenied("仅本机可调用")

    @extend_schema(
        tags=["tasks"],
        operation_id="task_drain_status",
        responses=OpenApiTypes.OBJECT,
    )
    def get(self, request):
        """只读：返回 running 数与当前排空标志。"""
        self._require_loopback(request)
        return Response({"running": api.count_running_tasks(), "draining": api.is_draining()})

    @extend_schema(
        tags=["tasks"],
        operation_id="task_drain_begin",
        request=None,
        responses=OpenApiTypes.OBJECT,
    )
    def post(self, request):
        """置位排空标志；此后不再派发新任务。"""
        self._require_loopback(request)
        api.begin_drain()
        return Response({"running": api.count_running_tasks(), "draining": api.is_draining()})
