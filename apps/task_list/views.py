"""task-list views — task submit/list/detail/rerun/cancel/delete/clear."""

from django.http import JsonResponse
from django.views import View
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai_assistant import api as agent_api
from apps.task_list import api, engine_adapter
from apps.task_list.models import Task
from apps.task_list.serializers import TaskSubmitInputSerializer
from apps.task_list.task_reports import build_task_flow


class TaskSubmitAPIView(APIView):
    """POST /api/tasks/submit — 提交任务；按设备调度（同设备排队 / 异设备并行）。"""

    @extend_schema(request=TaskSubmitInputSerializer, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        serializer = TaskSubmitInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        agent = agent_api.get_agent(data["agent_id"])
        if agent is None:
            raise ValidationError("智能体不存在或不可用")
        try:
            engine_adapter.sop_role_models(agent)
        except ValueError as exc:
            raise ValidationError(f"智能体不可用于 SOP：{exc}") from exc

        title = data["title"]
        goal = (data.get("goal") or "").strip()
        device_serial = (data.get("device_serial") or "").strip()
        device_label = (data.get("device_label") or "").strip()
        case_title = (data.get("case_title") or "").strip()

        from apps.task_list.attachments import (
            AttachmentError,
            collect_task_files,
            store_flat_upload,
        )

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
    """GET /api/tasks — 任务发布列表（Task）。"""

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        agent = agent_api.get_platform_agent()
        if agent is None:
            return Response({"tasks": []})
        tasks = Task.objects.filter(agent=agent).select_related("agent").order_by("-id")[:100]
        return Response({"tasks": [api.serialize_agent_task_row(t) for t in tasks]})


class AgentTaskDeleteAPIView(APIView):
    """POST /api/tasks/{task_id}/delete — 删除任务发布记录。"""

    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, task_id: int):
        agent = agent_api.get_platform_agent()
        if agent is None:
            raise NotFound("任务不存在")
        try:
            task = Task.objects.get(id=task_id, agent=agent)
        except Task.DoesNotExist:
            raise NotFound("任务不存在")
        api.delete_task(task)
        return Response({})


class AgentTaskCancelAPIView(APIView):
    """POST /api/tasks/{task_id}/cancel — 关闭运行中的 SOP。"""

    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, task_id: int):
        agent = agent_api.get_platform_agent()
        if agent is None:
            raise NotFound("任务不存在")
        try:
            task = Task.objects.get(id=task_id, agent=agent)
        except Task.DoesNotExist:
            raise NotFound("任务不存在")
        try:
            task = api.cancel_running_task(task)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response({"id": task.id, "status": task.status})


class AgentTaskRerunAPIView(APIView):
    """POST /api/tasks/{task_id}/rerun — 失败任务克隆新建并调度。"""

    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, task_id: int):
        from models.constants import TaskStatus

        agent = agent_api.get_platform_agent()
        if agent is None:
            raise NotFound("任务不存在")
        try:
            task = Task.objects.select_related("agent").get(id=task_id, agent=agent)
        except Task.DoesNotExist:
            raise NotFound("任务不存在")
        if task.status != TaskStatus.FAILED:
            raise ValidationError("仅失败任务可重新执行")
        new_task = api.rerun_task(task)
        api.dispatch_device(new_task.device_serial or "")
        new_task.refresh_from_db()
        return Response({"id": new_task.id, "status": new_task.status})


class AgentTaskClearAPIView(APIView):
    """POST /api/tasks/clear — 调试：清空全部任务发布记录。"""

    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        agent = agent_api.get_platform_agent()
        if agent is None:
            return Response({"deleted": 0})
        deleted = api.clear_agent_tasks(agent)
        return Response({"deleted": deleted})


class AgentTaskDetailAPIView(APIView):
    """GET /api/tasks/{task_id} — 任务发布详情（过程日志）。"""

    @extend_schema(responses=OpenApiTypes.OBJECT, operation_id="ai_agent_task_detail")
    def get(self, request, task_id: int):
        agent = agent_api.get_platform_agent()
        if agent is None:
            raise NotFound("任务不存在")
        try:
            task = Task.objects.select_related("agent").get(id=task_id, agent=agent)
        except Task.DoesNotExist:
            raise NotFound("任务不存在")
        return Response(api.serialize_agent_task_detail(task))


class TaskReportAPIView(View):
    """GET /api/tasks/{task_id}/report — 平铺任务事件流程（兼容报告页结构）。"""

    def get(self, request, task_id: int):
        user_id = getattr(request, "user_id", None)
        payload = build_task_flow(user_id, task_id)
        if payload is None:
            return JsonResponse({"status": False, "message": "task not found"}, status=404)
        return JsonResponse(payload)
