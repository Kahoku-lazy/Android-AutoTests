"""
模块功能：➡️ Agent 配置写库。只登记名称、模型配置外键和系统提示词，不创建 Agent 🏁
Python 调试：➡️ python -m backend.apps.ai_assistant.services.agent_configs 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 暂无（经 ai_assistant 的功能用例间接覆盖，未直接 import 本模块）
🏁
"""

from django.db import IntegrityError, transaction

from backend.apps.ai_assistant.models import AIRole, AIRoleKind
from backend.apps.ai_assistant.services.model_configs import (
    get_model_config,
)
from backend.apps.ai_assistant.services.role_id import generate_unique_role_id


class RoleConflictError(Exception):
    """名称或短标识已被占用。"""


class RoleIdExhaustedError(Exception):
    """当日可用的短标识已耗尽。"""


def _require_chat_model(model_config_id: int):
    """Agent 配置只能绑定聊天模型。

    Raises:
        ModelConfigMissingError: 模型配置不存在。
        ValueError: 模型类型不是聊天。
    """
    config = get_model_config(model_config_id)
    if config.model_kind != "chat":
        raise ValueError("Agent 配置只能绑定聊天模型")
    return config


def _role_id_taken(candidate: str) -> bool:
    """判断候选短标识是否已被占用。"""
    return AIRole.objects.filter(role_id=candidate).exists()


def prepare_role(name: str, model_config_id: int, system_prompt: str = "") -> dict:
    """校验并生成待写入字段。不写库。

    Args:
        name: 名称，已去空白且非空。
        model_config_id: 模型配置主键。
        system_prompt: 系统提示词正文，允许为空。

    Returns:
        含短标识、名称、模型配置主键和提示词的字段字典。

    Raises:
        ModelConfigMissingError: 模型配置不存在。
        RoleIdExhaustedError: 当日短标识空间耗尽。
    """
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
    """部分更新 Agent 配置。短标识不可改。

    Args:
        role: 待更新的配置。
        data: 已校验字段，键取 name / model_config_id / system_prompt。
        kinds: 目标类型列表；None 表示不改动类型，空列表表示置为未分类。

    Returns:
        更新后的配置，已带出关联的模型配置与类型标签。

    Raises:
        ModelConfigMissingError: 新的模型配置不存在。
        RoleConflictError: 新名称已被占用。
    """
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
    """整组替换配置的类型标签。空列表表示未分类。

    只补差集、不先清后插，避免已有标签的 created_at 被无谓刷新。

    Args:
        role: 已存在的 Agent 配置。
        kinds: 目标类型列表，取值与长度由序列化器先行校验。

    Returns:
        无返回值。
    """
    wanted = list(dict.fromkeys(kinds))
    with transaction.atomic():
        AIRoleKind.objects.filter(role=role).exclude(kind__in=wanted).delete()
        existing = set(AIRoleKind.objects.filter(role=role).values_list("kind", flat=True))
        AIRoleKind.objects.bulk_create(
            [AIRoleKind(role=role, kind=kind) for kind in wanted if kind not in existing]
        )


def delete_role(role: AIRole) -> None:
    """物理删除 Agent 配置。类型标签随外键级联删除。"""
    role.delete()


def list_roles():
    """返回全部 Agent 配置，按创建时间倒序，并带出模型配置与类型标签。"""
    return (
        AIRole.objects.select_related("model_config")
        .prefetch_related("kinds")
        .order_by("-created_at", "-id")
    )


def get_role(role_id: str) -> AIRole | None:
    """按短标识取 Agent 配置；不存在返回 None。"""
    return (
        AIRole.objects.select_related("model_config")
        .prefetch_related("kinds")
        .filter(role_id=role_id)
        .first()
    )
