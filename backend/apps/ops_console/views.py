from __future__ import annotations

from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.shared.users import is_operator

from . import api


def _actor_id(request) -> int:
    raw = getattr(request, "user_id", "") or getattr(getattr(request, "user", None), "id", "")
    try:
        return int(str(raw))
    except (TypeError, ValueError):
        return 0


def _require_operator(request) -> None:
    if not is_operator(_actor_id(request)):
        raise PermissionDenied("仅运营可访问运营后台")


def _parse_active(raw) -> bool | None:
    text = str(raw or "").strip().lower()
    if text in {"true", "1", "active", "enabled"}:
        return True
    if text in {"false", "0", "inactive", "disabled"}:
        return False
    return None


def _parse_page(raw, default: int) -> int:
    try:
        return max(int(str(raw)), 1)
    except (TypeError, ValueError):
        return default


class OpsUserListView(APIView):
    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        _require_operator(request)
        payload = api.list_users(
            page=_parse_page(request.query_params.get("page"), 1),
            page_size=_parse_page(request.query_params.get("page_size"), api.DEFAULT_PAGE_SIZE),
            keyword=request.query_params.get("keyword") or "",
            active=_parse_active(request.query_params.get("active")),
        )
        return Response(payload)


class OpsUserBatchDisableView(APIView):
    @extend_schema(
        operation_id="ops_users_batch_disable",
        request=OpenApiTypes.OBJECT,
        responses=OpenApiTypes.OBJECT,
    )
    def post(self, request):
        _require_operator(request)
        user_ids = _parse_user_ids(request.data.get("user_ids"))
        return Response(api.disable_users(_actor_id(request), user_ids))


class OpsUserPurgeView(APIView):
    @extend_schema(
        operation_id="ops_users_purge",
        request=OpenApiTypes.OBJECT,
        responses=OpenApiTypes.OBJECT,
    )
    def post(self, request):
        _require_operator(request)
        user_ids = _parse_user_ids(request.data.get("user_ids"))
        try:
            payload = api.purge_users(_actor_id(request), user_ids)
        except PermissionError as exc:
            raise PermissionDenied(str(exc)) from exc
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(payload)


class OpsUserDisableView(APIView):
    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, user_id: int):
        _require_operator(request)
        return Response(_toggle(request, user_id, active=False))


class OpsUserEnableView(APIView):
    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, user_id: int):
        _require_operator(request)
        return Response(_toggle(request, user_id, active=True))


class OpsUserModelGrantView(APIView):
    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    def post(self, request, user_id: int):
        raw = request.data.get("model_config_id")
        if isinstance(raw, bool) or not isinstance(raw, int) or raw < 1:
            raise ValidationError("模型配置主键必须是正整数")
        enabled = bool(request.data.get("enabled", True))
        try:
            payload = api.set_model_use(_actor_id(request), user_id, raw, enabled)
        except LookupError as exc:
            raise NotFound(str(exc)) from exc
        except PermissionError as exc:
            raise PermissionDenied(str(exc)) from exc
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(payload)


class OpsUserGrantAuthorView(APIView):
    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, user_id: int):
        return Response(_author(request, user_id, enabled=True))


class OpsUserRevokeAuthorView(APIView):
    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, user_id: int):
        return Response(_author(request, user_id, enabled=False))


class OpsUserGrantOperatorView(APIView):
    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, user_id: int):
        _require_operator(request)
        return Response(_grant(request, user_id, enabled=True))


class OpsUserRevokeOperatorView(APIView):
    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, user_id: int):
        _require_operator(request)
        return Response(_grant(request, user_id, enabled=False))


class OpsUserResetPasswordView(APIView):
    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, user_id: int):
        _require_operator(request)
        try:
            payload = api.reset_password(_actor_id(request), user_id)
        except LookupError as exc:
            raise NotFound(str(exc)) from exc
        except PermissionError as exc:
            raise PermissionDenied(str(exc)) from exc
        return Response(payload)


def _parse_user_ids(raw) -> list[int]:
    if not isinstance(raw, list) or not raw or len(raw) > api.MAX_PAGE_SIZE:
        raise ValidationError("请提交 1 到 100 个账号")
    seen: list[int] = []
    for item in raw:
        if isinstance(item, bool) or not isinstance(item, int) or item < 1:
            raise ValidationError("账号主键必须是正整数")
        if item not in seen:
            seen.append(item)
    return seen


def _author(request, user_id: int, *, enabled: bool) -> dict:
    try:
        return api.set_assistant_author(_actor_id(request), user_id, enabled)
    except LookupError as exc:
        raise NotFound(str(exc)) from exc
    except PermissionError as exc:
        raise PermissionDenied(str(exc)) from exc


def _grant(request, user_id: int, *, enabled: bool) -> dict:
    action = api.grant_operator if enabled else api.revoke_operator
    try:
        return action(_actor_id(request), user_id)
    except LookupError as exc:
        raise NotFound(str(exc)) from exc
    except PermissionError as exc:
        raise PermissionDenied(str(exc)) from exc


def _toggle(request, user_id: int, *, active: bool) -> dict:
    try:
        return api.set_active(_actor_id(request), user_id, active)
    except LookupError as exc:
        raise NotFound(str(exc)) from exc
    except PermissionError as exc:
        raise PermissionDenied(str(exc)) from exc
