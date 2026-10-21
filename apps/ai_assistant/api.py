"""ai-assistant API — agent / route configuration only.

Cross-module writes must go through this module (firewall #2).
"""

import base64
import hashlib

from cryptography.fernet import Fernet
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q

from apps.ai_assistant.models import AIAgent
from models.constants import AgentStatus
from utils.logs import backend_log

__all__ = [
    "create_agent",
    "update_agent",
    "delete_agent",
    "reveal_agent_key",
    "get_platform_agent",
    "get_agent",
    "resolve_assistant_name",
    "encrypt_key",
    "decrypt_key",
    "mask_key",
    "decrypt_route_configs",
    "mask_route_configs",
    "get_provider_config",
    "filter_agents_for_user",
]


def filter_agents_for_user(queryset, user_id: str | None):
    """Scope agent list：超级管理员全量；普通用户 = 超级管理员拥有的共享智能体 ∪ 自己拥有的（遗留）。"""
    if not user_id:
        return queryset.none()
    try:
        is_super = get_user_model().objects.filter(pk=int(user_id), is_superuser=True).exists()
    except (ValueError, TypeError):
        is_super = False
    if is_super:
        return queryset
    superuser_ids = list(
        get_user_model().objects.filter(is_superuser=True).values_list("id", flat=True)
    )
    return queryset.filter(Q(owner_id=user_id) | Q(owner_id__in=superuser_ids))


_AGENT_CREATE_DEFAULTS = {
    "avatar": "🤖",
    "model_provider": "dashscope",
    "model_name": "qwen-max",
}


def _identity_route_config(name: str, avatar: str) -> dict:
    """把基本信息里的名称/头像写进控制设备线路（卡片与任务列表的显示源）。"""
    return {"device_control": {"name": name, "avatar": avatar}}


def create_agent(user_id: int, data: dict) -> AIAgent:
    """创建 Agent：只收基本信息，模型/线路用默认值（改由后台维护）。"""
    name = data.get("name", "")
    avatar = data.get("avatar", _AGENT_CREATE_DEFAULTS["avatar"])
    return AIAgent.objects.create(
        owner_id=int(user_id),
        name=name,
        avatar=avatar,
        tags=data.get("tags", ""),
        description=data.get("description", ""),
        model_provider=_AGENT_CREATE_DEFAULTS["model_provider"],
        model_name=_AGENT_CREATE_DEFAULTS["model_name"],
        route_configs=_identity_route_config(name, avatar),
        key_revealed=False,
    )


def update_agent(agent: AIAgent, data: dict) -> AIAgent:
    """更新基本信息；名称/头像镜像写入控制设备线路，模型配置与 health 保持不变。"""
    data = dict(data)  # 避免修改调用方（Serializer.validated_data）的字典
    for field in ("name", "avatar", "tags", "description"):
        if field in data:
            setattr(agent, field, data[field])

    configs = dict(agent.route_configs or {})
    route = dict(configs.get("device_control") or {})
    identity_changed = False
    for field in ("name", "avatar"):
        if field in data:
            route[field] = data[field]
            identity_changed = True
    if identity_changed:
        configs["device_control"] = route
        agent.route_configs = configs
    agent.save()
    return agent


def delete_agent(agent: AIAgent) -> None:
    """删除 Agent（级联删除其工具/对话/消息）。"""
    agent.delete()


def reveal_agent_key(agent: AIAgent) -> dict:
    """一次性查看 API Key。返回 {api_key, revealed, hint}。"""
    if not agent.api_key:
        raise ValueError("未配置 API Key")
    if agent.key_revealed:
        decrypted = decrypt_key(agent.api_key)
        return {
            "api_key": mask_key(decrypted),
            "revealed": False,
            "hint": "API Key 仅支持一次性查看，已过期",
        }
    decrypted = decrypt_key(agent.api_key)
    agent.key_revealed = True
    agent.save(update_fields=["key_revealed", "updated_at"])
    return {
        "api_key": decrypted,
        "revealed": True,
        "hint": "请立即复制保存，此 Key 仅显示一次",
    }


def get_platform_agent() -> AIAgent | None:
    """返回平台唯一智能体（超级管理员拥有的活跃共享智能体，无则回退首个活跃智能体）。"""
    from django.contrib.auth import get_user_model

    qs = AIAgent.objects.filter(status=AgentStatus.ACTIVE)
    superuser_ids = list(
        get_user_model().objects.filter(is_superuser=True).values_list("id", flat=True)
    )
    if superuser_ids:
        agent = qs.filter(owner_id__in=superuser_ids).order_by("id").first()
        if agent:
            return agent
    return qs.order_by("id").first()


def get_agent(agent_id: int) -> AIAgent | None:
    """按 id 取智能体；不存在返回 None（提交入口用于校验）。"""
    try:
        return AIAgent.objects.filter(id=int(agent_id)).first()
    except (TypeError, ValueError):
        return None


def resolve_assistant_name(agent: AIAgent | None) -> str:
    """当前控制设备线路名；空则回退智能体 name。"""
    if agent is None:
        return ""
    route = (agent.route_configs or {}).get("device_control") or {}
    route_name = str(route.get("name") or "").strip()
    if route_name:
        return route_name
    return str(agent.name or "").strip()


def _get_cipher() -> Fernet:
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt_key(plain: str) -> str:
    """加密 API Key（供数据初始化/测试构造线路配置使用）。"""
    if not plain:
        return ""
    return _get_cipher().encrypt(plain.encode()).decode()


def decrypt_key(encrypted: str) -> str:
    """解密 API Key。解密失败时返回空字符串而非崩溃。"""
    if not encrypted:
        return ""
    try:
        return _get_cipher().decrypt(encrypted.encode()).decode()
    except Exception:
        backend_log.exception(
            "API key decryption failed — key may be corrupted or SECRET_KEY rotated"
        )
        return ""


def mask_key(key: str) -> str:
    """脱敏显示 API Key：保留前 3 位 + *** + 后 4 位。"""
    if not key or len(key) < 8:
        return "***"
    return key[:3] + "***" + key[-4:]


ROUTE_MODEL_ROLES = ("planner", "executor", "verifier")


def _copy_route_meta(src: dict, dest: dict) -> None:
    """保留线路级展示字段（name/avatar 等），不进入模型角色加密逻辑。"""
    for key, val in src.items():
        if key not in ROUTE_MODEL_ROLES:
            dest[key] = val


def _transform_route_configs(route_configs: dict, transform) -> dict:
    """对 route_configs 内每条线路模型的 api_key 应用 transform。"""
    result = {}
    for route, models in (route_configs or {}).items():
        if not isinstance(models, dict):
            continue
        result[route] = {}
        _copy_route_meta(models, result[route])
        for role in ROUTE_MODEL_ROLES:
            cfg = models.get(role)
            if not isinstance(cfg, dict):
                continue
            new_cfg = dict(cfg)
            if new_cfg.get("api_key"):
                new_cfg["api_key"] = transform(new_cfg["api_key"])
            result[route][role] = new_cfg
    return result


def decrypt_route_configs(route_configs: dict) -> dict:
    """解密 route_configs 内 api_key。"""
    return _transform_route_configs(route_configs, decrypt_key)


def mask_route_configs(route_configs: dict) -> dict:
    """脱敏 route_configs 内 api_key。"""
    return _transform_route_configs(route_configs, mask_key)


def get_provider_config(provider: str, base_url: str = "", model_name: str = "") -> dict:
    """获取模型 provider 的 API 配置（base_url + api_key 模式）。
    供管理命令等跨模块调用，避免直接导入 agent_scope.provider_registry。
    """
    from apps.ai_assistant.provider_registry import get_provider_config as _get

    return _get(provider, base_url)
