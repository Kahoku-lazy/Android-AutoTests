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
    uid = getattr(request, "user_id", None)
    if uid is not None:
        return str(uid)
    user = getattr(request, "user", None)
    if user is not None and hasattr(user, "id"):
        return str(user.id)
    return ""


def _visible_card(assistant_id: str, user_id: str):
    card = api.get_assistant(assistant_id)
    if card is None:
        raise NotFound("助手不存在")
    if is_assistant_author(user_id) or card.release_state == "published":
        return card
    raise NotFound("助手不存在")


def _visible_thread(thread_id: str, user_id: str):
    thread = api.get_thread(thread_id)
    if thread is None:
        return None
    _visible_card(thread.assistant_id, user_id)
    return thread


class ModelConfigDiscoverView(APIView):
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
    queryset = AIModelConfig.objects.all()
    serializer_class = ModelConfigSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return api.list_model_configs()

    def list(self, request, *args, **kwargs):
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
        try:
            api.delete_role(role)
        except api.RoleConflictError as exc:
            raise ValidationError(str(exc)) from exc
        return Response({"role_id": role_id})


class AssistantViewSet(viewsets.ModelViewSet):
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
    @extend_schema(operation_id="ai_assistant_threads_list", responses=OpenApiTypes.OBJECT)
    def get(self, request, assistant_id: str):
        card = _visible_card(assistant_id, _user_id(request))
        return Response(
            [
                {
                    "thread_id": item.thread_id,
                    "status": item.status,
                    "title": item.title,
                }
                for item in api.list_threads(card.assistant_id)
            ]
        )

    @extend_schema(
        operation_id="ai_assistant_threads_create", request=None, responses=OpenApiTypes.OBJECT
    )
    def post(self, request, assistant_id: str):
        card = _visible_card(assistant_id, _user_id(request))
        thread = api.create_thread(card.assistant_id)
        return Response(
            {"thread_id": thread.thread_id, "status": thread.status}, status=status.HTTP_201_CREATED
        )


class AssistantThreadLogView(APIView):
    def get_permissions(self):
        if self.kwargs.get("report_id"):
            return [AllowAny()]
        return super().get_permissions()

    @extend_schema(operation_id="ai_assistant_thread_logs_list", responses=OpenApiTypes.OBJECT)
    def get(self, request, thread_id: str, report_id: str = ""):
        if report_id:
            return AssistantThreadLogFileView().get(request, thread_id, report_id)
        thread = _visible_thread(thread_id, _user_id(request))
        if thread is None:
            return Response({"message": "对话栏不存在"}, status=status.HTTP_404_NOT_FOUND)
        return Response(api.list_thread_logs(thread))

    @extend_schema(
        operation_id="ai_assistant_thread_log_ticket", request=None, responses=OpenApiTypes.OBJECT
    )
    def post(self, request, thread_id: str, report_id: str = ""):
        return AssistantThreadLogFileView().post(request, thread_id, report_id)


class AssistantThreadLogFileView(APIView):
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
        if not api.is_safe_report_id(report_id):
            return Response({"message": "日志不存在"}, status=status.HTTP_404_NOT_FOUND)
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
    @extend_schema(operation_id="ai_assistant_thread_detail", responses=OpenApiTypes.OBJECT)
    def get(self, request, thread_id: str):
        thread = _visible_thread(thread_id, _user_id(request))
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
        thread = _visible_thread(thread_id, _user_id(request))
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
        thread = _visible_thread(thread_id, _user_id(request))
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
        thread = _visible_thread(thread_id, _user_id(request))
        if thread is None:
            return Response({"message": "对话栏不存在"}, status=status.HTTP_404_NOT_FOUND)
        from engines.backend_bridge.agents.thread_run import request_thread_cancel

        request_thread_cancel(thread_id)
        api.cancel_thread(thread)
        return Response({"thread_id": thread_id, "status": thread.status})


class AssistantThreadDeleteView(APIView):
    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, thread_id: str):
        thread = _visible_thread(thread_id, _user_id(request))
        if thread is None:
            return Response({"message": "对话栏不存在"}, status=status.HTTP_404_NOT_FOUND)
        from engines.backend_bridge.agents.thread_run import request_thread_cancel

        request_thread_cancel(thread_id)
        api.delete_thread(thread)
        return Response({"thread_id": thread_id, "deleted": True})


def _sop_workflow_or_404(workflow_id: int):
    try:
        return api.get_sop_workflow(workflow_id)
    except api.AISopWorkflow.DoesNotExist as exc:
        raise NotFound("工作流不存在") from exc


class EvalScoreView(APIView):
    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    def get(self, request):
        _require_author(request)
        kind = str(request.query_params.get("kind") or "")
        target_id = str(request.query_params.get("target_id") or "")
        limit = int(request.query_params.get("limit") or 20)
        try:
            rows = api.list_eval_scores(kind, target_id, limit=max(1, min(limit, 100)))
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response({"scores": rows})

    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        _require_author(request)
        kind = str(request.data.get("kind") or "")
        target_id = str(request.data.get("target_id") or "")
        source_ref = str(request.data.get("source_ref") or "")
        try:
            detail = api.score_eval_target(
                kind,
                target_id,
                source_ref=source_ref,
                created_by=str(getattr(request, "user_id", "") or ""),
            )
        except LookupError as exc:
            raise NotFound(str(exc)) from exc
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response({"score": detail})


class EvalCandidateView(APIView):
    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        _require_author(request)
        kind = str(request.query_params.get("kind") or "")
        target_id = str(request.query_params.get("target_id") or "")
        try:
            rows = api.list_eval_candidates(kind, target_id)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response({"candidates": rows})


class AssistantPublishView(APIView):
    serializer_class = None

    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, assistant_id: str):
        _require_author(request)
        card = api.get_assistant(assistant_id)
        if card is None:
            return Response({"message": "助手不存在"}, status=status.HTTP_404_NOT_FOUND)
        try:
            release = api.publish_assistant(card)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        secret = "api_key" in release.payload or "secret" in release.payload
        return Response(
            {"assistant_id": assistant_id, "version": release.version, "has_secret": secret}
        )


class WorkflowPublishView(APIView):
    serializer_class = None

    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, workflow_id: int):
        _require_author(request)
        try:
            workflow = api.get_sop_workflow(workflow_id)
            release = api.publish_workflow(workflow)
        except api.AISopWorkflow.DoesNotExist as exc:
            raise NotFound("工作流不存在") from exc
        except (api.WorkflowBindingError, ValueError) as exc:
            raise ValidationError(str(exc)) from exc
        return Response({"id": workflow_id, "version": release.version})


class EvalMethodView(APIView):
    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        _require_author(request)
        return Response({"methods": api.list_eval_methods()})


class EvalCaseView(APIView):
    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    def get(self, request):
        _require_author(request)
        return Response({"cases": api.list_eval_cases()})

    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        _require_author(request)
        try:
            row = api.create_eval_case(
                title=str(request.data.get("title") or ""),
                note=str(request.data.get("note") or ""),
                steps=list(request.data.get("steps") or []),
                created_by=str(getattr(request, "user_id", "") or ""),
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response({"case": row})


class EvalCaseDetailView(APIView):
    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    def patch(self, request, case_id: int):
        _require_author(request)
        try:
            row = api.update_eval_case(
                case_id,
                title=str(request.data.get("title") or ""),
                note=request.data.get("note"),
                enabled=request.data.get("enabled"),
                steps=request.data.get("steps"),
            )
        except LookupError as exc:
            raise NotFound(str(exc)) from exc
        return Response({"case": row})

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def delete(self, request, case_id: int):
        _require_author(request)
        try:
            api.delete_eval_case(case_id)
        except LookupError as exc:
            raise NotFound(str(exc)) from exc
        return Response({"deleted": case_id})


class EvalReportView(APIView):
    @extend_schema(responses=OpenApiTypes.BINARY)
    def get(self, request, run_id: int):
        _require_author(request)
        from pathlib import Path

        from django.http import FileResponse

        try:
            path = Path(api.eval_report_file(run_id))
        except LookupError as exc:
            raise NotFound(str(exc)) from exc
        if not path.is_file():
            raise NotFound("看板文件不存在")
        return FileResponse(path.open("rb"), content_type="text/html")


class EvalSuiteScoreView(APIView):
    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    def get(self, request):
        _require_author(request)
        target_id = str(request.query_params.get("target_id") or "")
        limit = int(request.query_params.get("limit") or 20)
        rows = api.list_suite_scores(target_id, limit=max(1, min(limit, 100)))
        return Response({"scores": rows})

    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        _require_author(request)
        kind = str(request.data.get("target_kind") or "")
        target_id = str(request.data.get("target_id") or "")
        serial = str(request.data.get("serial") or "")
        case_ids = [str(item) for item in request.data.get("case_ids") or [] if str(item)]
        if kind not in {"assistant", "workflow"} or not target_id:
            raise ValidationError("请选择助手或工作流")
        if not case_ids:
            raise ValidationError("请至少选择一条真题")
        try:
            detail = api.run_suite_eval(
                kind,
                target_id,
                case_ids=case_ids,
                serial=serial,
                owner_id="1",
                created_by=str(getattr(request, "user_id", "") or ""),
            )
        except LookupError as exc:
            raise NotFound(str(exc)) from exc
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response({"score": detail})


class AgentReportView(APIView):
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
    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        from engines.ae_harness.tools import list_tool_catalog

        return Response(list_tool_catalog())


class AssistantAvatarView(APIView):
    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request, assistant_id: str):
        card = _visible_card(assistant_id, _user_id(request))
        return Response({"assistant_id": card.assistant_id, "avatar": card.avatar})


def _require_author(request) -> None:
    if not is_assistant_author(_user_id(request)):
        raise PermissionDenied("Forbidden")


def _assistant_payload(request) -> dict:
    data = request.data.dict() if hasattr(request.data, "dict") else dict(request.data)
    raw_tools = data.get("tools")
    if isinstance(raw_tools, str) and raw_tools:
        data["tools"] = __import__("json").loads(raw_tools)
    return data


def _avatar_bytes(request) -> bytes | None:
    upload = request.FILES.get("avatar")
    if upload is None:
        return None
    return upload.read()
