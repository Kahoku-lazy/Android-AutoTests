import json

from django.db import transaction
from django.http import HttpResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import APIException, NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.apps.task_list import api
from backend.apps.task_list.models import Task
from backend.apps.task_list.serializers import TaskSubmitInputSerializer
from backend.models.constants import TaskKind, TaskStatus


def _case_ids(request) -> list[str]:
    raw_ids = request.data.get("case_ids") or "[]"
    try:
        case_ids = json.loads(raw_ids) if isinstance(raw_ids, str) else list(raw_ids)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValidationError("用例编号必须是 JSON 数组") from exc
    if not isinstance(case_ids, list) or not case_ids:
        raise ValidationError("请至少选择 1 条自动化用例")
    return [str(item) for item in case_ids]


def _platform_milestone(case_ids: list[str], user_id: str):
    from backend.apps.case_manager.api import automation_case_identity, compile_automation_cases
    from backend.apps.task_list.attachments import PreparedUpload, validate_milestone_yaml

    try:
        rows = automation_case_identity(case_ids=case_ids, user_id=str(user_id or ""))
        text = compile_automation_cases(case_ids=case_ids, user_id=str(user_id or ""))
    except (LookupError, ValueError) as exc:
        raise ValidationError(str(exc)) from exc
    validate_milestone_yaml(text)
    content = text.encode("utf-8")
    prepared = PreparedUpload(
        kind="config", filename="platform-cases.yaml", body=text, content=content
    )
    return prepared, {"source": "platform", "rows": rows}


def _current_release_version(workflow_id: int) -> int | None:
    from backend.apps.ai_assistant.models import AssistantRelease

    return (
        AssistantRelease.objects.filter(target_kind="workflow", target_id=str(workflow_id))
        .order_by("-version")
        .values_list("version", flat=True)
        .first()
    )


def _store_attachment(filename: str, content: bytes) -> str:
    from backend.apps.task_list.attachments import store_flat_upload
    from utils.logs import backend_log

    try:
        return store_flat_upload(filename, content)
    except OSError as exc:
        backend_log.exception("任务附件写入失败: %s", filename)
        reason = str(exc.strerror or exc).strip().rstrip("。.")
        raise APIException(
            f"任务配置文件写入失败：{reason}，请检查运行账号对该目录的写权限"
        ) from exc


def _submit_material_workflow(request, workflow, title: str, user_id):
    from backend.apps.task_list.attachments import (
        AttachmentError,
        parse_document_bytes,
    )

    uploaded = request.FILES.get("material")
    if uploaded is None:
        raise ValidationError("请上传需求文档或模块材料")
    try:
        markdown, filename = parse_document_bytes(uploaded.name, uploaded.read())
    except AttachmentError as exc:
        raise ValidationError(str(exc)) from exc
    if not markdown.strip():
        raise ValidationError("文档没有可用文本")
    with transaction.atomic():
        task = api.create_task(
            title=title,
            goal=markdown,
            task_kind=TaskKind.ASSISTANT_SOP,
            created_by=str(user_id or ""),
            workflow_id=workflow.id,
            release_version=_current_release_version(workflow.id),
            orchestration=workflow.orchestration,
            kind=workflow.kind,
        )
        task.result = api.dump_task_run_payload({"workflow_id": workflow.id})
        task.save(update_fields=["result"])
        api.add_task_attachment(
            task,
            kind="document",
            filename=filename,
            body=markdown,
            sort_order=0,
            stored_path=_store_attachment(filename, markdown.encode("utf-8")),
        )
    api.dispatch_case_authoring(task)
    task.refresh_from_db()
    return Response({"id": task.id, "status": task.status, "result": ""})


def _submit_assistant_sop(
    request, title: str, goal: str, device_serial: str, device_label: str, user_id
):
    from backend.apps.ai_assistant import api as assistant_api
    from backend.apps.task_list.attachments import (
        AttachmentError,
        collect_milestone_file,
    )

    raw_id = str(request.data.get("workflow_id") or "").strip()
    try:
        workflow_id = int(raw_id)
        workflow = assistant_api.get_sop_workflow(workflow_id)
    except (ValueError, assistant_api.AISopWorkflow.DoesNotExist) as exc:
        raise ValidationError("工作流不存在") from exc
    if workflow.release_state != "published":
        raise ValidationError("工作流尚未发布")
    if workflow.kind in {"case_authoring", "requirement_breakdown"}:
        return _submit_material_workflow(request, workflow, title, user_id)
    if not device_serial:
        raise ValidationError("请选择设备")
    source = str(request.data.get("case_source") or "yaml")
    try:
        if source == "platform":
            prepared, identity = _platform_milestone(_case_ids(request), str(user_id or ""))
        else:
            prepared = collect_milestone_file(request.FILES.getlist("config"))
            identity = {"source": "milestone", "rows": []}
    except AttachmentError as exc:
        raise ValidationError(str(exc)) from exc
    with transaction.atomic():
        task = api.create_task(
            title=title,
            goal=goal,
            device_serial=device_serial,
            device_label=device_label,
            case_identity=identity,
            task_kind=TaskKind.ASSISTANT_SOP,
            created_by=str(user_id or ""),
            workflow_id=workflow.id,
            release_version=_current_release_version(workflow.id),
            orchestration=workflow.orchestration,
            kind=workflow.kind,
        )
        task.result = api.dump_task_run_payload({"workflow_id": workflow.id})
        task.save(update_fields=["result"])
        api.add_task_attachment(
            task,
            kind=prepared.kind,
            filename=prepared.filename,
            body=prepared.body,
            sort_order=0,
            stored_path=_store_attachment(prepared.filename, prepared.content),
        )
    api.dispatch_device(device_serial)
    task.refresh_from_db()
    return Response({"id": task.id, "status": task.status, "result": ""})


def _visible_task(request, task_id: int) -> Task | None:
    if not getattr(request, "user_id", None):
        return None
    return Task.objects.filter(id=task_id).first()


class TaskSubmitAPIView(APIView):
    @extend_schema(request=TaskSubmitInputSerializer, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        serializer = TaskSubmitInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user_id = getattr(request, "user_id", None)
        title = data["title"]
        goal = (data.get("goal") or "").strip()
        device_serial = (data.get("device_serial") or "").strip()
        device_label = (data.get("device_label") or "").strip()
        if not str(request.data.get("workflow_id") or "").strip():
            raise ValidationError("请从工作流提交任务")
        return _submit_assistant_sop(request, title, goal, device_serial, device_label, user_id)


class AgentTaskListAPIView(APIView):
    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        if not getattr(request, "user_id", None):
            return Response({"tasks": [], "workflows": []})
        workflow_id = str(request.query_params.get("workflow_id") or "").strip()
        status_name = str(request.query_params.get("status") or "").strip()
        tasks = Task.objects.filter(task_kind=TaskKind.ASSISTANT_SOP)
        if workflow_id:
            tasks = tasks.filter(result__contains=f'"workflow_id": {workflow_id}')
        if status_name:
            tasks = tasks.filter(status=status_name)
        rows = list(
            tasks.only(*api.TASK_LIST_FIELDS)
            .prefetch_related("file_attachments")
            .order_by("-id")[:100]
        )
        return Response(
            {
                "tasks": [api.serialize_agent_task_row(task) for task in rows],
                "workflows": api.workflow_filter_options(),
            },
        )


class AgentTaskStatsAPIView(APIView):
    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        if not getattr(request, "user_id", None):
            return Response({"total": 0, "agents": []})
        data = api.task_stats(Task.objects.filter(task_kind=TaskKind.ASSISTANT_SOP))
        data["agents"] = []
        return Response(data)


class AgentTaskDeleteAPIView(APIView):
    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, task_id: int):
        task = _visible_task(request, task_id)
        if task is None:
            raise NotFound("任务不存在")
        api.delete_task(task)
        return Response({})


class AgentTaskCancelAPIView(APIView):
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
    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, task_id: int):
        task = _visible_task(request, task_id)
        if task is None:
            raise NotFound("任务不存在")
        if task.status not in {
            TaskStatus.FAILED,
            TaskStatus.INTERRUPTED,
            TaskStatus.COMPLETED,
            TaskStatus.CANCELLED,
        }:
            raise ValidationError("待执行或执行中的任务不能重新执行")
        new_task = api.rerun_task(task)
        if new_task.kind in {"case_authoring", "requirement_breakdown"}:
            api.dispatch_case_authoring(new_task)
        elif new_task.task_kind == TaskKind.CASE_AUTHORING:
            api.dispatch_case_authoring(new_task)
        else:
            api.dispatch_device(new_task.device_serial or "")
        new_task.refresh_from_db()
        return Response({"id": new_task.id, "status": new_task.status})


class AgentTaskClearAPIView(APIView):
    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        if not getattr(request, "user_id", None):
            return Response({"deleted": 0})
        deleted, _ = Task.objects.all().delete()
        return Response({"deleted": deleted})


class AgentTaskDetailAPIView(APIView):
    @extend_schema(responses=OpenApiTypes.OBJECT, operation_id="ai_agent_task_detail")
    def get(self, request, task_id: int):
        task = _visible_task(request, task_id)
        if task is None:
            raise NotFound("任务不存在")
        return Response(api.serialize_agent_task_detail(task))


class TaskMediaAPIView(APIView):
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
    permission_classes = [AllowAny]

    @staticmethod
    def _require_loopback(request) -> None:
        if request.META.get("REMOTE_ADDR", "") not in ("127.0.0.1", "::1"):
            raise PermissionDenied("仅本机可调用")

    @extend_schema(
        tags=["tasks"],
        operation_id="task_drain_status",
        responses=OpenApiTypes.OBJECT,
    )
    def get(self, request):
        self._require_loopback(request)
        return Response(
            {
                "running": api.count_running_tasks(),
                "running_ids": api.running_task_ids(),
                "draining": api.is_draining(),
            }
        )

    @extend_schema(
        tags=["tasks"],
        operation_id="task_drain_begin",
        request=None,
        responses=OpenApiTypes.OBJECT,
    )
    def post(self, request):
        self._require_loopback(request)
        api.begin_drain()
        return Response(
            {
                "running": api.count_running_tasks(),
                "running_ids": api.running_task_ids(),
                "draining": api.is_draining(),
            }
        )
