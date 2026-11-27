from django.db import IntegrityError, transaction

from backend.apps.ai_assistant.models import AIRole, AIRoleKind
from backend.apps.ai_assistant.services.model_configs import (
    get_model_config,
)
from backend.apps.ai_assistant.services.role_id import generate_unique_role_id


class RoleConflictError(Exception):
    pass


class RoleIdExhaustedError(Exception):
    pass


def _require_chat_model(model_config_id: int):
    config = get_model_config(model_config_id)
    if config.model_kind != "chat":
        raise ValueError("Agent 配置只能绑定聊天模型")
    return config


def _role_id_taken(candidate: str) -> bool:
    return AIRole.objects.filter(role_id=candidate).exists()


def prepare_role(name: str, model_config_id: int, system_prompt: str = "") -> dict:
    _require_chat_model(model_config_id)
    try:
        role_id = generate_unique_role_id(_role_id_taken)
    except RuntimeError as exc:
        raise RoleIdExhaustedError(str(exc)) from exc
    return {
        "role_id": role_id,
        "name": name,
        "model_config_id": model_config_id,
        "system_prompt": system_prompt,
    }


def update_role(role: AIRole, data: dict, kinds: list[str] | None = None) -> AIRole:
    if "model_config_id" in data:
        _require_chat_model(data["model_config_id"])
    for field in ("name", "model_config_id", "system_prompt"):
        if field in data:
            setattr(role, field, data[field])
    try:
        with transaction.atomic():
            role.save()
            if kinds is not None:
                replace_kinds(role, kinds)
    except IntegrityError as exc:
        raise RoleConflictError("名称已存在") from exc
    return AIRole.objects.select_related("model_config").prefetch_related("kinds").get(pk=role.pk)


def replace_kinds(role: AIRole, kinds: list[str]) -> None:
    wanted = list(dict.fromkeys(kinds))
    with transaction.atomic():
        AIRoleKind.objects.filter(role=role).exclude(kind__in=wanted).delete()
        existing = set(AIRoleKind.objects.filter(role=role).values_list("kind", flat=True))
        AIRoleKind.objects.bulk_create(
            [AIRoleKind(role=role, kind=kind) for kind in wanted if kind not in existing]
        )


def delete_role(role: AIRole) -> None:
    from backend.apps.ai_assistant.models import AIAssistant

    names = list(
        AIAssistant.objects.filter(role_id=role.role_id)
        .order_by("id")
        .values_list("display_name", flat=True)
    )
    if names:
        quoted = "、".join(f"「{name}」" for name in names)
        raise RoleConflictError(f"该 Agent 配置仍被助手{quoted}使用，请先解除引用再删除")
    role.delete()


def list_roles():
    return (
        AIRole.objects.select_related("model_config")
        .prefetch_related("kinds")
        .order_by("-created_at", "-id")
    )


def get_role(role_id: str) -> AIRole | None:
    return (
        AIRole.objects.select_related("model_config")
        .prefetch_related("kinds")
        .filter(role_id=role_id)
        .first()
    )
