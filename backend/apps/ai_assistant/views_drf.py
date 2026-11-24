"""ai-assistant DRF 视图 — 角色注册表。

路径：
  GET    /api/ai/roles/             列表
  POST   /api/ai/roles/             创建
  GET    /api/ai/roles/{role_id}/   详情
  PATCH  /api/ai/roles/{role_id}/   部分更新
  DELETE /api/ai/roles/{role_id}/   删除

鉴权：JWT 中间件已先校验并注入 request.user_id；DRF 全局 IsAuthenticated 兜底。
写库：全部经 api.py。成功信封由 EnvelopeJSONRenderer 统一包裹。
"""

from django.db import IntegrityError
from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework import status, viewsets
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.shared.users import is_assistant_author, is_operator

from . import api
from .models import AIAssistant, AIModelConfig, AIRole
from .serializers import (
    AssistantInputSerializer,
    AssistantOutputSerializer,
    ModelConfigSerializer,
    RoleInputSerializer,
    RoleOutputSerializer,
    SopWorkflowInputSerializer,
    SopWorkflowOutputSerializer,
)


def _user_id(request) -> str:
    """用户 id：优先中间件注入的 request.user_id，回退 DRF request.user.id。"""
    uid = getattr(request, "user_id", None)
    if uid is not None:
        return str(uid)
    user = getattr(request, "user", None)
    if user is not None and hasattr(user, "id"):
        return str(user.id)
    return ""


class ModelConfigDiscoverView(APIView):
    """POST /api/ai/model-configs/discover/ — 向厂商查询模型名，不写库。"""

    @extend_schema(request=ModelConfigSerializer, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        if not is_operator(_user_id(request)):
            raise PermissionDenied("Forbidden")
        serializer = ModelConfigSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            found = api.discover_model_names(
                data["provider"], data["api_key_env"], data.get("base_url") or ""
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(found)


class ModelConfigViewSet(viewsets.ModelViewSet):
    """模型配置 — /api/ai/model-configs/。登录可读，运营可写。"""

    queryset = AIModelConfig.objects.all()
    serializer_class = ModelConfigSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return api.list_model_configs()

    def list(self, request, *args, **kwargs):
        # 运营维护配置时仍看全部。主动选择只看自己的名单。
        if request.query_params.get("selectable") == "1":
            configs = api.list_selectable_model_configs(_user_id(request))
        else:
            configs = self.get_queryset()
        kind = request.query_params.get("model_kind", "")
        if kind:
            configs = configs.filter(model_kind=kind)
        return Response({"configs": ModelConfigSerializer(configs, many=True).data})

    def create(self, request, *args, **kwargs):
        self._require_operator(request)
        serializer = ModelConfigSerializer(data=request.data, context={"require_model_name": True})
        serializer.is_valid(raise_exception=True)
        try:
            config = api.create_model_config(serializer.validated_data)
        except IntegrityError as exc:
            raise ValidationError("该密钥下已有同名模型") from exc
        return Response(ModelConfigSerializer(config).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        self._require_operator(request)
        config = self.get_object()
        serializer = ModelConfigSerializer(
            data=request.data, partial=True, context={"require_model_name": True}
        )
        serializer.is_valid(raise_exception=True)
        config = api.update_model_config(config, serializer.validated_data)
        return Response(ModelConfigSerializer(config).data)

    def destroy(self, request, *args, **kwargs):
        self._require_operator(request)
        config = self.get_object()
        try:
            api.delete_model_config(config)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response({})

    def _require_operator(self, request) -> None:
        if not is_operator(_user_id(request)):
            raise PermissionDenied("Forbidden")


class RoleViewSet(viewsets.ModelViewSet):
    """角色增删改查 — /api/ai/roles/ 与 /api/ai/roles/{role_id}/。"""

    queryset = AIRole.objects.all()
    lookup_field = "role_id"
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_serializer_class(self):
        if self.action in ("create", "partial_update"):
            return RoleInputSerializer
        return RoleOutputSerializer

    def get_queryset(self):
        return api.list_roles()

    def list(self, request, *args, **kwargs):
        return Response(RoleOutputSerializer(self.get_queryset(), many=True).data)

    def retrieve(self, request, *args, **kwargs):
        return Response(RoleOutputSerializer(self.get_object()).data)

    def create(self, request, *args, **kwargs):
        if not is_operator(_user_id(request)):
            raise PermissionDenied("Forbidden")
        serializer = RoleInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if "name" not in data or "model_config_id" not in data:
            raise ValidationError("名称与模型配置不能为空")
        if not api.can_select_model(_user_id(request), data["model_config_id"]):
            raise PermissionDenied("不能使用该模型")
        kinds = data.get("kinds") or []
        if not kinds:
            raise ValidationError("请选择类型")
        try:
            role = api.create_role(
                data["name"],
                data["model_config_id"],
                data.get("system_prompt", ""),
                kinds=kinds,
            )
        except (api.ModelConfigMissingError, ValueError) as exc:
            raise ValidationError(str(exc)) from exc
        except api.RoleConflictError as exc:
            return Response({"message": str(exc)}, status=status.HTTP_409_CONFLICT)
        except api.RoleIdExhaustedError as exc:
            return Response({"message": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(RoleOutputSerializer(role).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        if not is_operator(_user_id(request)):
            raise PermissionDenied("Forbidden")
        serializer = RoleInputSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        # 缺省＝不改动类型；显式 [] ＝置为未分类。
        kinds = data.pop("kinds", None)
        if "model_config_id" in data and not api.can_select_model(
            _user_id(request), data["model_config_id"]
        ):
            raise PermissionDenied("不能使用该模型")
        try:
            role = api.update_role(self.get_object(), data, kinds)
        except (api.ModelConfigMissingError, ValueError) as exc:
            raise ValidationError(str(exc)) from exc
        except api.RoleConflictError as exc:
            return Response({"message": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(RoleOutputSerializer(role).data)

    def destroy(self, request, *args, **kwargs):
        if not is_operator(_user_id(request)):
            raise PermissionDenied("Forbidden")
        role = self.get_object()
        role_id = role.role_id
        api.delete_role(role)
        return Response({"role_id": role_id})


class AssistantViewSet(viewsets.ModelViewSet):
    """助手名片 — /api/ai/assistants/ 与 /api/ai/assistants/{assistant_id}/。"""

    queryset = AIAssistant.objects.all()
    lookup_field = "assistant_id"
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_serializer_class(self):
        if self.action in ("create", "partial_update"):
            return AssistantInputSerializer
        return AssistantOutputSerializer

    def get_queryset(self):
        rows = api.list_assistants()
        if is_assistant_author(_user_id(self.request)):
            return rows
        return rows.filter(release_state="published")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        role_ids = list(self.get_queryset().values_list("role_id", flat=True))
        context["role_names"] = dict(
            AIRole.objects.filter(role_id__in=role_ids).values_list("role_id", "name")
        )
        return context

    def list(self, request, *args, **kwargs):
        return Response(self.get_serializer(self.get_queryset(), many=True).data)

    def retrieve(self, request, *args, **kwargs):
        return Response(self.get_serializer(self.get_object()).data)

    def create(self, request, *args, **kwargs):
        self._require_author(request)
        payload = _assistant_payload(request)
        serializer = AssistantInputSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if "display_name" not in data or "role_id" not in data:
            raise ValidationError("名称与 Agent 配置不能为空")
        try:
            card = api.create_assistant(
                data["display_name"],
                data["role_id"],
                avatar=_avatar_bytes(request),
                tools=data.get("tools") or [],
            )
        except api.AssistantRoleMissingError as exc:
            raise ValidationError(str(exc)) from exc
        except api.AvatarRejectedError as exc:
            raise ValidationError(str(exc)) from exc
        except api.AssistantIdExhaustedError as exc:
            return Response({"message": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(
            AssistantOutputSerializer(card, context=self._names_for([card])).data,
            status=status.HTTP_201_CREATED,
        )

    def partial_update(self, request, *args, **kwargs):
        self._require_author(request)
        serializer = AssistantInputSerializer(data=_assistant_payload(request), partial=True)
        serializer.is_valid(raise_exception=True)
        payload = dict(serializer.validated_data)
        if "avatar" in request.FILES or request.data.get("clear_avatar"):
            payload["avatar"] = _avatar_bytes(request)
        try:
            card = api.update_assistant(self.get_object(), payload)
        except api.AssistantRoleMissingError as exc:
            raise ValidationError(str(exc)) from exc
        except api.AvatarRejectedError as exc:
            raise ValidationError(str(exc)) from exc
        except api.AssistantRevisionConflict as exc:
            return Response({"message": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(AssistantOutputSerializer(card, context=self._names_for([card])).data)

    def destroy(self, request, *args, **kwargs):
        self._require_author(request)
        card = self.get_object()
        assistant_id = card.assistant_id
        try:
            api.delete_assistant(card)
        except api.AssistantInUseError as exc:
            raise ValidationError(str(exc)) from exc
        return Response({"assistant_id": assistant_id})

    def _names_for(self, cards) -> dict:
        role_ids = [card.role_id for card in cards]
        return {
            "role_names": dict(
                AIRole.objects.filter(role_id__in=role_ids).values_list("role_id", "name")
            )
        }

    def _require_author(self, request) -> None:
        if not is_assistant_author(_user_id(request)):
            raise PermissionDenied("Forbidden")


class AssistantThreadView(APIView):
    """测试对话栏：建栏、列表、发送、轮询、取消。发送只落库并排队，不在请求里跑模型。"""

    @extend_schema(operation_id="ai_assistant_threads_list", responses=OpenApiTypes.OBJECT)
    def get(self, request, assistant_id: str):
        return Response(
            [
                {
                    "thread_id": item.thread_id,
                    "status": item.status,
                    "title": item.title,
                }
                for item in api.list_threads(assistant_id)
            ]
        )

    @extend_schema(
        operation_id="ai_assistant_threads_create", request=None, responses=OpenApiTypes.OBJECT
    )
    def post(self, request, assistant_id: str):
        try:
            thread = api.create_thread(assistant_id)
        except AIAssistant.DoesNotExist:
            return Response({"message": "助手不存在"}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            {"thread_id": thread.thread_id, "status": thread.status}, status=status.HTTP_201_CREATED
        )


class AssistantThreadLogView(APIView):
    """列出该栏日志，或用 ticket 打开一份 HTML。report_id 为空时只列目录。"""

    def get_permissions(self):
        if self.kwargs.get("report_id"):
            return [AllowAny()]
        return super().get_permissions()

    @extend_schema(operation_id="ai_assistant_thread_logs_list", responses=OpenApiTypes.OBJECT)
    def get(self, request, thread_id: str, report_id: str = ""):
        if report_id:
            return AssistantThreadLogFileView().get(request, thread_id, report_id)
        thread = api.get_thread(thread_id)
        if thread is None:
            return Response({"message": "对话栏不存在"}, status=status.HTTP_404_NOT_FOUND)
        return Response(api.list_thread_logs(thread))

    @extend_schema(
        operation_id="ai_assistant_thread_log_ticket", request=None, responses=OpenApiTypes.OBJECT
    )
    def post(self, request, thread_id: str, report_id: str = ""):
        return AssistantThreadLogFileView().post(request, thread_id, report_id)


class AssistantThreadLogFileView(APIView):
    """用一次性 ticket 打开一份已写完的 HTML 日志。只挂带 report_id 的路径。"""

    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="ai_assistant_thread_log_file",
        responses={(200, "text/html"): OpenApiTypes.BINARY},
    )
    def get(self, request, thread_id: str, report_id: str):
        thread = api.get_thread(thread_id)
        if thread is None:
            return Response({"message": "对话栏不存在"}, status=status.HTTP_404_NOT_FOUND)
        if thread.status == "running":
            return Response({"message": "还在写"}, status=status.HTTP_409_CONFLICT)
        from backend.apps.ai_assistant.services.log_ticket import LogTicketError, consume_log_ticket

        try:
            consume_log_ticket(str(request.GET.get("ticket") or ""), thread_id, report_id)
        except LogTicketError as exc:
            return Response({"message": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)
        path = api.resolve_thread_report(thread, report_id)
        if path is None or not path.is_file():
            return Response({"message": "日志不存在"}, status=status.HTTP_404_NOT_FOUND)
        from django.http import FileResponse

        return FileResponse(path.open("rb"), content_type="text/html")

    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, thread_id: str, report_id: str = ""):
        thread = api.get_thread(thread_id)
        if thread is None:
            return Response({"message": "对话栏不存在"}, status=status.HTTP_404_NOT_FOUND)
        if thread.status == "running" or not report_id:
            return Response({"message": "还在写"}, status=status.HTTP_409_CONFLICT)
        from backend.apps.ai_assistant.services.log_ticket import issue_log_ticket

        return Response({"ticket": issue_log_ticket(thread_id, report_id)})


class AssistantThreadDetailView(APIView):
    """GET 轮询消息；POST 发送；PATCH 重命名；DELETE 取消。"""

    @extend_schema(operation_id="ai_assistant_thread_detail", responses=OpenApiTypes.OBJECT)
    def get(self, request, thread_id: str):
        thread = api.get_thread(thread_id)
        if thread is None:
            return Response({"message": "对话栏不存在"}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            {
                "thread_id": thread.thread_id,
                "status": thread.status,
                "messages": api.message_rows(thread),
            }
        )

    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    def patch(self, request, thread_id: str):
        thread = api.get_thread(thread_id)
        if thread is None:
            return Response({"message": "对话栏不存在"}, status=status.HTTP_404_NOT_FOUND)
        title = str(request.data.get("title") or "").strip()
        api.rename_thread(thread, title)
        return Response({"thread_id": thread.thread_id, "title": thread.title})

    @extend_schema(
        operation_id="ai_assistant_thread_send",
        request=OpenApiTypes.OBJECT,
        responses=OpenApiTypes.OBJECT,
    )
    def post(self, request, thread_id: str):
        thread = api.get_thread(thread_id)
        if thread is None:
            return Response({"message": "对话栏不存在"}, status=status.HTTP_404_NOT_FOUND)
        content = str(request.data.get("content") or "").strip()
        if not content:
            raise ValidationError("消息不能为空")
        if thread.status == "running":
            return Response({"message": "这一轮还在跑"}, status=status.HTTP_409_CONFLICT)
        try:
            api.send_message(thread, content)
        except api.AssistantRoleMissingError as exc:
            return Response({"message": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(
            {"thread_id": thread.thread_id, "status": "running"}, status=status.HTTP_202_ACCEPTED
        )

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def delete(self, request, thread_id: str):
        thread = api.get_thread(thread_id)
        if thread is None:
            return Response({"message": "对话栏不存在"}, status=status.HTTP_404_NOT_FOUND)
        from engines.backend_bridge.agents.thread_run import request_thread_cancel

        request_thread_cancel(thread_id)
        api.cancel_thread(thread)
        return Response({"thread_id": thread_id, "status": thread.status})


class AssistantThreadDeleteView(APIView):
    """POST /api/ai/assistants/threads/{thread_id}/delete/ — 删除对话栏与其消息。

    进行中的轮次先请求取消，再删记录；后台线程写回时发现栏已不存在会跳过。
    """

    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, thread_id: str):
        thread = api.get_thread(thread_id)
        if thread is None:
            return Response({"message": "对话栏不存在"}, status=status.HTTP_404_NOT_FOUND)
        from engines.backend_bridge.agents.thread_run import request_thread_cancel

        request_thread_cancel(thread_id)
        api.delete_thread(thread)
        return Response({"thread_id": thread_id, "deleted": True})


def _sop_workflow_or_404(workflow_id: int):
    """按主键取工作流；不存在时抛 404。"""
    try:
        return api.get_sop_workflow(workflow_id)
    except api.AISopWorkflow.DoesNotExist as exc:
        raise NotFound("工作流不存在") from exc


class LiveEvalDetailView(APIView):
    """GET /api/ai/evals/runs/{run_id}/ — 一次评测的进度与逐条过程。"""

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request, run_id: int):
        _require_author(request)
        detail = api.live_run_detail(run_id)
        if detail is None:
            raise NotFound("评测运行不存在")
        return Response(detail)


class EvalRunView(APIView):
    """POST /api/ai/evals/run/ — 作者选择一条助手或工作流后自测。"""

    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        _require_author(request)
        kind = str(request.data.get("kind") or "")
        target_id = str(request.data.get("target_id") or "")
        if kind not in {"assistant", "workflow"} or not target_id:
            raise ValidationError("请选择助手或工作流")
        try:
            run = api.start_live_eval(kind, target_id)
            from backend.apps.ai_assistant.services.live_runner import start_live_eval

            start_live_eval(run.pk)
            return Response({"id": run.pk, "status": run.status})
        except LookupError as exc:
            raise NotFound(str(exc)) from exc
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc


class AssistantPublishView(APIView):
    """POST /api/ai/assistants/{assistant_id}/publish/ — 发布当前草稿。"""

    serializer_class = None

    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, assistant_id: str):
        _require_author(request)
        card = api.get_assistant(assistant_id)
        if card is None:
            return Response({"message": "助手不存在"}, status=status.HTTP_404_NOT_FOUND)
        payload = api._release_payload_for_assistant(card)
        if not api.eval_passed("assistant", card.assistant_id, payload):
            raise ValidationError("自测未通过，不能发布")
        release = api.publish_assistant(card)
        secret = "api_key" in release.payload or "secret" in release.payload
        return Response(
            {"assistant_id": assistant_id, "version": release.version, "has_secret": secret}
        )


class WorkflowPublishView(APIView):
    """POST /api/ai/sop-workflows/{workflow_id}/publish/ — 发布当前草稿。"""

    serializer_class = None

    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, workflow_id: int):
        _require_author(request)
        try:
            workflow = api.get_sop_workflow(workflow_id)
            if api.workflow_requires_eval(workflow) and not api.eval_passed(
                "workflow", str(workflow.id), api.workflow_eval_payload(workflow)
            ):
                raise ValidationError("自测未通过，不能发布")
            release = api.publish_workflow(workflow)
        except api.AISopWorkflow.DoesNotExist as exc:
            raise NotFound("工作流不存在") from exc
        except api.WorkflowBindingError as exc:
            raise ValidationError(str(exc)) from exc
        return Response({"id": workflow_id, "version": release.version})


class AgentReportView(APIView):
    """GET /api/ai/agent-reports/{run}/{name}/ — 只读平台报告正文。"""

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request, run: str, name: str):
        from engines.backend_bridge.reports import REPORT_ROOT

        root = REPORT_ROOT.resolve()
        path = (root / run / name).resolve()
        if (
            path.parent != (root / run).resolve()
            or not path.is_file()
            or path.suffix.lower() != ".html"
        ):
            return Response({"message": "报告不存在"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"run": run, "name": name, "content": path.read_text(encoding="utf-8")})


class SopWorkflowView(APIView):
    """GET/POST /api/ai/sop-workflows/ — 列出与创建 SOP 工作流。"""

    @extend_schema(responses=SopWorkflowOutputSerializer(many=True))
    def get(self, request):
        rows = api.list_sop_workflows()
        if not is_assistant_author(_user_id(request)):
            rows = [row for row in rows if row.release_state == "published"]
        return Response(SopWorkflowOutputSerializer(rows, many=True).data)

    @extend_schema(request=SopWorkflowInputSerializer, responses=SopWorkflowOutputSerializer)
    def post(self, request):
        _require_author(request)
        serializer = SopWorkflowInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            workflow = api.create_sop_workflow(
                data["name"],
                data.get("executor_assistant_id") or "",
                data.get("verifier_assistant_id") or "",
                orchestration=data.get("orchestration") or api.ORCHESTRATION_SOP,
                kind=data.get("kind") or api.KIND_UI,
                leader_assistant_id=data.get("leader_assistant_id") or "",
                members=data.get("members") or [],
            )
        except (
            api.WorkflowNameError,
            api.WorkflowAssistantMissingError,
            api.WorkflowPairError,
            api.WorkflowBindingError,
        ) as exc:
            raise ValidationError(str(exc)) from exc
        return Response(SopWorkflowOutputSerializer(workflow).data, status=status.HTTP_201_CREATED)


class SopWorkflowDetailView(APIView):
    """PATCH/DELETE /api/ai/sop-workflows/{workflow_id}/ — 编辑或删除一条工作流。

    编辑与创建共用同一份入参与校验；删除只删工作流记录，
    名片、Agent 配置与历史任务都不受影响。
    """

    @extend_schema(request=SopWorkflowInputSerializer, responses=SopWorkflowOutputSerializer)
    def patch(self, request, workflow_id: int):
        _require_author(request)
        workflow = _sop_workflow_or_404(workflow_id)
        serializer = SopWorkflowInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            workflow = api.update_sop_workflow(
                workflow,
                data["name"],
                data.get("executor_assistant_id") or "",
                data.get("verifier_assistant_id") or "",
                leader_assistant_id=data.get("leader_assistant_id") or "",
                members=data.get("members") or [],
            )
        except (
            api.WorkflowNameError,
            api.WorkflowAssistantMissingError,
            api.WorkflowPairError,
            api.WorkflowBindingError,
        ) as exc:
            raise ValidationError(str(exc)) from exc
        return Response(SopWorkflowOutputSerializer(workflow).data)

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def delete(self, request, workflow_id: int):
        _require_author(request)
        workflow = _sop_workflow_or_404(workflow_id)
        api.delete_sop_workflow(workflow)
        return Response({"id": workflow_id, "deleted": True})


class ToolCatalogView(APIView):
    """GET /api/ai/tool-catalog/ — 只读工具目录，不含实现。"""

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        from engines.ae_harness.tools import list_tool_catalog

        return Response(list_tool_catalog())


class AssistantAvatarView(APIView):
    """GET /api/ai/assistants/{assistant_id}/avatar/ — 只返回压缩后的头像正文。"""

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request, assistant_id: str):
        card = api.get_assistant(assistant_id)
        if card is None:
            return Response({"message": "助手不存在"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"assistant_id": card.assistant_id, "avatar": card.avatar})


def _require_author(request) -> None:
    """助手与工作流的写操作只允许助手作者。运营身份本身不够。"""
    if not is_assistant_author(_user_id(request)):
        raise PermissionDenied("Forbidden")


def _assistant_payload(request) -> dict:
    """表单里的 tools 是 JSON 字符串，先解开再交给序列化器。"""
    data = request.data.dict() if hasattr(request.data, "dict") else dict(request.data)
    raw_tools = data.get("tools")
    if isinstance(raw_tools, str) and raw_tools:
        data["tools"] = __import__("json").loads(raw_tools)
    return data


def _avatar_bytes(request) -> bytes | None:
    """从表单文件读取头像；没有文件时返回 None。"""
    upload = request.FILES.get("avatar")
    if upload is None:
        return None
    return upload.read()
