"""运营后台（JWT）：账号列表 / 停用 / 启用 / 重置密码 / 批量停用 / 批量注销。

GET  /api/ops/users/                              运营可读：分页账号列表
POST /api/ops/users/<int:user_id>/disable/        运营：停用普通账号
POST /api/ops/users/<int:user_id>/enable/         运营：启用普通账号
POST /api/ops/users/<int:user_id>/reset-password/ 运营：重置普通账号密码
POST /api/ops/users/<int:user_id>/model-grants/    仅超管：改模型名单
POST /api/ops/users/<int:user_id>/grant-author/    仅超管：授予助手作者
POST /api/ops/users/<int:user_id>/revoke-author/   仅超管：收回助手作者
POST /api/ops/users/<int:user_id>/grant-operator/  仅超管：设为运营
POST /api/ops/users/<int:user_id>/revoke-operator/ 仅超管：取消运营
POST /api/ops/users/disable/                       运营：本页批量停用
POST /api/ops/users/purge/                         仅超管：批量注销（只删账号）

端点都要求运营身份（超级管理员天然算运营），普通用户一律 403。
按 id 的删除路径不注册，自然落到 404。
"""

from __future__ import annotations

from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.shared.users import is_operator

from . import api


def _actor_id(request) -> int:
    """取当前操作者的账号主键。

    Args:
        request: DRF 请求；网关中间件注入 `user_id`，DRF 认证另会设 `user`。

    Returns:
        正整数主键；取不到返回 0。
    """
    raw = getattr(request, "user_id", "") or getattr(getattr(request, "user", None), "id", "")
    try:
        return int(str(raw))
    except (TypeError, ValueError):
        return 0


def _require_operator(request) -> None:
    """要求当前请求来自运营，否则抛 403。

    Args:
        request: DRF 请求。

    Returns:
        None：通过校验。

    Raises:
        PermissionDenied: 当前账号不是运营。
    """
    if not is_operator(_actor_id(request)):
        raise PermissionDenied("仅运营可访问运营后台")


def _parse_active(raw) -> bool | None:
    """把查询参数解析成三态启用状态。

    Args:
        raw: `active` 查询参数原文。

    Returns:
        True/False 表示筛选启用或停用，None 表示不筛。
    """
    text = str(raw or "").strip().lower()
    if text in {"true", "1", "active", "enabled"}:
        return True
    if text in {"false", "0", "inactive", "disabled"}:
        return False
    return None


def _parse_page(raw, default: int) -> int:
    """把查询参数解析成正整数，非法值回落到默认值。

    Args:
        raw: 查询参数原文。
        default: 解析失败时使用的默认值。

    Returns:
        正整数。
    """
    try:
        return max(int(str(raw)), 1)
    except (TypeError, ValueError):
        return default


class OpsUserListView(APIView):
    """GET /api/ops/users/ — 分页账号列表（运营可读）。"""

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
    """POST /api/ops/users/disable/ — 本页批量停用（运营）。"""

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
    """POST /api/ops/users/purge/ — 批量注销（仅超管，只删账号）。"""

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
    """POST /api/ops/users/<int:user_id>/disable/ — 停用普通账号（运营）。"""

    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, user_id: int):
        _require_operator(request)
        return Response(_toggle(request, user_id, active=False))


class OpsUserEnableView(APIView):
    """POST /api/ops/users/<int:user_id>/enable/ — 启用普通账号（运营）。"""

    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, user_id: int):
        _require_operator(request)
        return Response(_toggle(request, user_id, active=True))


class OpsUserModelGrantView(APIView):
    """POST /api/ops/users/<int:user_id>/model-grants/ — 修改模型名单（仅超管）。"""

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
    """POST /api/ops/users/<int:user_id>/grant-author/ — 授予助手作者（仅超管）。"""

    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, user_id: int):
        return Response(_author(request, user_id, enabled=True))


class OpsUserRevokeAuthorView(APIView):
    """POST /api/ops/users/<int:user_id>/revoke-author/ — 收回助手作者（仅超管）。"""

    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, user_id: int):
        return Response(_author(request, user_id, enabled=False))


class OpsUserGrantOperatorView(APIView):
    """POST /api/ops/users/<int:user_id>/grant-operator/ — 设为运营（仅超管）。"""

    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, user_id: int):
        _require_operator(request)
        return Response(_grant(request, user_id, enabled=True))


class OpsUserRevokeOperatorView(APIView):
    """POST /api/ops/users/<int:user_id>/revoke-operator/ — 取消运营（仅超管）。"""

    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, user_id: int):
        _require_operator(request)
        return Response(_grant(request, user_id, enabled=False))


class OpsUserResetPasswordView(APIView):
    """POST /api/ops/users/<int:user_id>/reset-password/ — 重置普通账号密码（运营）。"""

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
    """把批量请求体解析成去重后的主键列表。

    Args:
        raw: `user_ids` 原文，须为列表。

    Returns:
        去重且保持原顺序的正整数主键。

    Raises:
        ValidationError: 不是列表、为空、超过 100，或含非正整数。
    """
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
    """授予或收回助手作者，并把领域错误映射成 HTTP 状态码。"""
    try:
        return api.set_assistant_author(_actor_id(request), user_id, enabled)
    except LookupError as exc:
        raise NotFound(str(exc)) from exc
    except PermissionError as exc:
        raise PermissionDenied(str(exc)) from exc


def _grant(request, user_id: int, *, enabled: bool) -> dict:
    """授予/取消运营共用分发：把 api 层的内置异常映射成 HTTP 状态码。

    Args:
        request: DRF 请求。
        user_id: 目标账号主键。
        enabled: True 授予、False 取消。

    Returns:
        含该账号最新一行的字典。

    Raises:
        NotFound: 目标账号不存在。
        PermissionDenied: 操作者不是超管，或目标不可被授予。
    """
    action = api.grant_operator if enabled else api.revoke_operator
    try:
        return action(_actor_id(request), user_id)
    except LookupError as exc:
        raise NotFound(str(exc)) from exc
    except PermissionError as exc:
        raise PermissionDenied(str(exc)) from exc


def _toggle(request, user_id: int, *, active: bool) -> dict:
    """停用/启用共用分发：把 api 层的内置异常映射成 HTTP 状态码。

    Args:
        request: DRF 请求。
        user_id: 目标账号主键。
        active: True 启用、False 停用。

    Returns:
        含该账号最新一行的字典。

    Raises:
        NotFound: 目标账号不存在。
        PermissionDenied: 目标不可被当前操作者管理。
    """
    try:
        return api.set_active(_actor_id(request), user_id, active)
    except LookupError as exc:
        raise NotFound(str(exc)) from exc
    except PermissionError as exc:
        raise PermissionDenied(str(exc)) from exc
