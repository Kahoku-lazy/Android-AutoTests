"""Agent 配置写库。只登记名称、模型配置外键和系统提示词，不创建 Agent。"""

from django.db import IntegrityError, transaction

from backend.apps.ai_assistant.models import AIRole
from backend.apps.ai_assistant.services.model_configs import (
    get_model_config,
)
from backend.apps.ai_assistant.services.role_id import generate_unique_role_id


class RoleConflictError(Exception):
    """名称或短标识已被占用。"""


class RoleIdExhaustedError(Exception):
    """当日可用的短标识已耗尽。"""


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
    get_model_config(model_config_id)
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


def update_role(role: AIRole, data: dict) -> AIRole:
    """部分更新 Agent 配置。短标识不可改。

    Args:
        role: 待更新的配置。
        data: 已校验字段，键取 name / model_config_id / system_prompt。

    Returns:
        更新后的配置，已带出关联的模型配置。

    Raises:
        ModelConfigMissingError: 新的模型配置不存在。
        RoleConflictError: 新名称已被占用。
    """
    if "model_config_id" in data:
        get_model_config(data["model_config_id"])
    for field in ("name", "model_config_id", "system_prompt"):
        if field in data:
            setattr(role, field, data[field])
    try:
        with transaction.atomic():
            role.save()
    except IntegrityError as exc:
        raise RoleConflictError("名称已存在") from exc
    return AIRole.objects.select_related("model_config").get(pk=role.pk)


def delete_role(role: AIRole) -> None:
    """物理删除 Agent 配置。"""
    role.delete()


def list_roles():
    """返回全部 Agent 配置，按创建时间倒序，并带出模型配置。"""
    return AIRole.objects.select_related("model_config").order_by("-created_at", "-id")


def get_role(role_id: str) -> AIRole | None:
    """按短标识取 Agent 配置；不存在返回 None。"""
    return AIRole.objects.select_related("model_config").filter(role_id=role_id).first()
