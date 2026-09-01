"""ai-assistant API — 跨模块调用的公共接口。

遵循防火墙 #2：所有跨模块写操作必须通过本文件的函数。
"""

import base64
import hashlib
import logging
import os

from cryptography.fernet import Fernet
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q

from apps.ai_assistant.models import (
    AIAgent,
    AIConversation,
    AIExecutionLog,
    AIMessage,
    AIPlatformTool,
    AISharedTool,
    AITask,
)

logger = logging.getLogger("ai_assistant")


__all__ = [
    # Agent 操作
    "get_agent",
    "get_agent_by_scope_id",
    "list_active_agents",
    "create_agent",
    "update_agent",
    "delete_agent",
    "reveal_agent_key",
    "update_agent_connectivity",
    # 平台唯一智能体 / 全局配置
    "get_platform_agent",
    "get_platform_config",
    "update_platform_config",
    # 对话操作
    "get_conversation",
    "get_or_create_conversation",
    "create_conversation",
    "rename_conversation",
    "delete_conversation",
    "log_confirm_result",
    # 工具箱 / 工具操作
    "create_shared_tool",
    "create_shared_skill",
    "update_shared_tool",
    "delete_shared_tool",
    "set_shared_tool_enabled",
    # 平台业务工具全局开关
    "get_platform_tool_enabled_map",
    "set_platform_tool_enabled",
    # 消息操作
    "save_message",
    # 任务操作
    "create_task",
    # 加密工具
    "encrypt_key",
    "decrypt_key",
    "mask_key",
    # 多线路模型配置加密工具
    "encrypt_route_configs",
    "decrypt_route_configs",
    "mask_route_configs",
    "get_route_model_config",
    # 跨模块接口（供 evaluator 等使用）
    "get_kb_doc_count",
    "get_provider_config",
    "search_knowledge",
    # 跨模块只读助手（供 dashboard 等使用，fix-cross-app-firewall）
    "filter_agents_for_user",
]


# ── 跨模块只读助手 ──


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


# ── Agent 查询（只读）──


def get_agent(agent_id: int):
    """根据主键获取 Agent。"""
    try:
        return AIAgent.objects.get(id=agent_id)
    except AIAgent.DoesNotExist:
        return None


def get_agent_by_scope_id(scope_id: str):
    """根据 AgentScope 注册 ID 获取 Agent。"""
    try:
        return AIAgent.objects.get(agent_scope_id=scope_id)
    except (AIAgent.DoesNotExist, AIAgent.MultipleObjectsReturned):
        return None


def list_active_agents():
    """获取所有活跃的 Agent。"""
    return list(
        AIAgent.objects.filter(status="active").values("id", "name", "model_provider", "model_name")
    )


# ── Agent 写操作（Batch 1 起从 views 下沉，遵循防火墙 #2）──

_AGENT_CREATE_DEFAULTS = {
    "avatar": "🤖",
    "model_provider": "dashscope",
    "model_name": "qwen-max",
}


def create_agent(user_id: int, data: dict) -> AIAgent:
    """创建 Agent（含初始工具列表）。入参已由 AgentInputSerializer 校验。"""
    a = AIAgent.objects.create(
        owner_id=int(user_id),
        name=data.get("name", ""),
        avatar=data.get("avatar", _AGENT_CREATE_DEFAULTS["avatar"]),
        tags=data.get("tags", ""),
        description=data.get("description", ""),
        model_provider=data.get("model_provider", _AGENT_CREATE_DEFAULTS["model_provider"]),
        model_name=data.get("model_name", _AGENT_CREATE_DEFAULTS["model_name"]),
        vision_model_name=data.get("vision_model_name", ""),
        strong_model_name=data.get("strong_model_name", ""),
        strong_enabled=data.get("strong_enabled", False),
        api_key=encrypt_key(data.get("api_key", "")),
        base_url=data.get("base_url", ""),
        enable_knowledge_base=data.get("enable_knowledge_base", False),
        enable_workspace_tools=data.get("enable_workspace_tools", False),
        enable_business_tools=data.get("enable_business_tools", False),
        enable_mcp_tools=data.get("enable_mcp_tools", False),
        enable_skills=data.get("enable_skills", False),
        skills_config=data.get("skills_config", {}),
        knowledge_sources=data.get("knowledge_sources", {}),
        route_configs=encrypt_route_configs(data.get("route_configs", {})),
        max_loops=data.get("max_loops", 3),
        key_revealed=False,
    )
    return a


def update_agent(agent: AIAgent, data: dict) -> AIAgent:
    """更新 Agent 配置。脱敏 Key 跳过、Key 变更重置 reveal 标记。"""
    data = dict(data)  # 避免修改调用方（Serializer.validated_data）的字典
    key_changed = False
    if "api_key" in data and data["api_key"]:
        # Frontend sends masked value (contains "***") when key is unchanged
        if "***" in data["api_key"]:
            del data["api_key"]
        else:
            data["api_key"] = encrypt_key(data["api_key"])
            key_changed = True
    if "route_configs" in data:
        data["route_configs"] = encrypt_route_configs(
            data["route_configs"], getattr(agent, "route_configs", {})
        )
    for f in [
        "name",
        "avatar",
        "tags",
        "description",
        "model_provider",
        "model_name",
        "vision_model_name",
        "strong_model_name",
        "strong_enabled",
        "api_key",
        "base_url",
        "enable_knowledge_base",
        "enable_workspace_tools",
        "enable_business_tools",
        "enable_mcp_tools",
        "enable_skills",
        "status",
        "skills_config",
        "knowledge_sources",
        "route_configs",
        "max_loops",
    ]:
        if f in data:
            setattr(agent, f, data[f])
    if key_changed:
        agent.key_revealed = False
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


def update_agent_connectivity(
    agent: AIAgent, *, connected: bool, checked_at, available_models: list | None = None
) -> None:
    """更新连通状态 / 检测时间 / 可用模型缓存（health、test 共用）。"""
    agent.is_connected = connected
    agent.last_checked_at = checked_at
    if available_models:
        import json

        agent.available_models = json.dumps(available_models)
    agent.save()


def get_platform_agent() -> AIAgent | None:
    """返回平台唯一智能体（超级管理员拥有的活跃共享智能体，无则回退首个活跃智能体）。"""
    from django.contrib.auth import get_user_model

    qs = AIAgent.objects.filter(status="active")
    superuser_ids = list(
        get_user_model().objects.filter(is_superuser=True).values_list("id", flat=True)
    )
    if superuser_ids:
        agent = qs.filter(owner_id__in=superuser_ids).order_by("id").first()
        if agent:
            return agent
    return qs.order_by("id").first()


_PLATFORM_CONFIG_FIELDS = (
    "enable_workspace_tools",
    "enable_business_tools",
    "enable_mcp_tools",
    "enable_skills",
    "enable_knowledge_base",
)


def get_platform_config(agent: AIAgent) -> dict:
    """读取平台唯一智能体的工具/知识库配置（供 AI 工具箱 / 知识库页）。"""
    return {
        "agent_id": agent.id,
        "agent_name": agent.name,
        **{f: getattr(agent, f) for f in _PLATFORM_CONFIG_FIELDS},
        "skills_config": agent.skills_config or {},
        "knowledge_sources": agent.knowledge_sources or {},
    }


def update_platform_config(agent: AIAgent, data: dict) -> None:
    """更新平台唯一智能体的能力开关 / 工作区 Skills / 知识库文档范围。"""
    fields: list[str] = []
    for f in _PLATFORM_CONFIG_FIELDS:
        if f in data:
            setattr(agent, f, bool(data[f]))
            fields.append(f)
    if "skills_config" in data:
        agent.skills_config = data["skills_config"] or {}
        fields.append("skills_config")
    if "knowledge_sources" in data:
        agent.knowledge_sources = data["knowledge_sources"] or {}
        fields.append("knowledge_sources")
    if fields:
        agent.save(update_fields=fields + ["updated_at"])


def get_platform_tool_enabled_map() -> dict[str, bool]:
    """平台业务工具全局启用状态（name → enabled）。

    默认（无记录）＝启用；`ai_platform_tools` 仅存停用记录（enabled=False）。
    """
    from apps.ai_assistant.agent_scope.tools import TOOLS

    disabled = set(AIPlatformTool.objects.filter(enabled=False).values_list("name", flat=True))
    return {name: name not in disabled for name in TOOLS}


def set_platform_tool_enabled(name: str, enabled: bool) -> None:
    """启停单个平台业务工具（全局）。

    启用 = 删除停用记录（回默认启用）；停用 = upsert enabled=False。
    """
    if enabled:
        AIPlatformTool.objects.filter(name=name).delete()
    else:
        AIPlatformTool.objects.update_or_create(name=name, defaults={"enabled": False})


# ── 对话操作 ──


def get_conversation(conv_id: int):
    """根据主键获取对话。"""
    try:
        return AIConversation.objects.get(id=conv_id)
    except AIConversation.DoesNotExist:
        return None


def get_or_create_conversation(agent: AIAgent, title: str = "新对话"):
    """获取或创建对话。返回 (conversation, created)。"""
    return AIConversation.objects.get_or_create(
        agent=agent,
        title=title,
        defaults={"status": "active"},
    )


def create_conversation(owner_id: int, agent_id: int, title: str) -> AIConversation:
    """创建对话（Batch 2 起从 views 下沉）。"""
    return AIConversation.objects.create(
        owner_id=int(owner_id),
        agent_id=agent_id,
        title=title,
    )


def rename_conversation(conv: AIConversation, title: str) -> AIConversation:
    """重命名对话。"""
    conv.title = title
    conv.save(update_fields=["title", "updated_at"])
    return conv


def delete_conversation(conv: AIConversation) -> None:
    """删除对话（级联删除消息）。"""
    conv.delete()


def log_confirm_result(agent: AIAgent, message: str, metadata: str) -> None:
    """记录 HITL 确认审计日志。写入失败仅记日志，不阻断确认流程。"""
    try:
        AIExecutionLog.objects.create(
            agent=agent,
            level="info",
            message=message,
            metadata=metadata,
        )
    except Exception:
        logger.exception("AIExecutionLog insert failed for agent_id=%s", agent.id)


# ── 工具箱 / 工具写操作（Batch 3 起从 views 下沉）──

_SHARED_SKILLS_DIR = os.path.join("data", "shared_skills")


def create_shared_tool(
    name: str, item_type: str, description: str = "", config_json: str = "{}"
) -> AISharedTool:
    """新增共享工具箱项（mcp/extension）。"""
    return AISharedTool.objects.create(
        name=name,
        item_type=item_type,
        description=description,
        config_json=config_json,
    )


def create_shared_skill(name: str, file_count: int, size_bytes: int, features: str) -> AISharedTool:
    """新增共享 skill 项（文件内容由调用方写入 data/shared_skills/{id}/）。"""
    import json as _json

    return AISharedTool.objects.create(
        name=name,
        item_type="skill",
        description=f"{file_count} 个文件 — {features}",
        config_json=_json.dumps(
            {
                "file_count": file_count,
                "size_bytes": size_bytes,
                "features": features,
            }
        ),
    )


def update_shared_tool(
    item: AISharedTool, name: str | None, description: str | None, config_json: str | None
) -> AISharedTool:
    """部分更新共享工具箱项。"""
    fields = []
    if name is not None:
        item.name = name
        fields.append("name")
    if description is not None:
        item.description = description
        fields.append("description")
    if config_json is not None:
        item.config_json = config_json
        fields.append("config_json")
    item.save(update_fields=fields + ["updated_at"])
    return item


def delete_shared_tool(item: AISharedTool) -> None:
    """删除共享工具箱项；skill 类型同步清理上传目录。"""
    if item.item_type == "skill":
        skill_dir = os.path.join(_SHARED_SKILLS_DIR, str(item.id))
        if os.path.isdir(skill_dir):
            import shutil

            shutil.rmtree(skill_dir, ignore_errors=True)
    item.delete()


def set_shared_tool_enabled(item: AISharedTool, enabled: bool) -> AISharedTool:
    """启用/停用共享工具箱项（直接决定平台唯一智能体是否使用）。"""
    item.enabled = enabled
    item.save(update_fields=["enabled", "updated_at"])
    return item


# ── 消息操作 ──


def save_message(
    conversation_id: int,
    role: str,
    content: str,
    blocks: str = "",
    reason: str = "normal",
    tokens: int = 0,
    input_tokens: int = 0,
    cache_input_tokens: int = 0,
    cache_creation_input_tokens: int = 0,
    model_name: str = "",
    flow: str = "",
) -> AIMessage:
    """保存一条对话消息到数据库。"""
    return AIMessage.objects.create(
        conversation_id=conversation_id,
        role=role,
        content=content,
        blocks=blocks,
        reason=reason,
        tokens=tokens,
        input_tokens=input_tokens,
        cache_input_tokens=cache_input_tokens,
        cache_creation_input_tokens=cache_creation_input_tokens,
        model_name=model_name,
        flow=flow if flow in ("sse", "fallback") else "",
    )


# ── 任务操作（任务发布）──


def create_task(
    agent: AIAgent,
    *,
    title: str,
    goal: str,
    requirements: str = "",
    attachment: str = "",
    route: str = "device_control",
    checklist: str = "",
    report_name: str = "",
    device_serial: str = "",
) -> AITask:
    """创建任务（任务发布）。"""
    return AITask.objects.create(
        agent=agent,
        title=title,
        goal=goal,
        requirements=requirements,
        attachment=attachment,
        route=route,
        checklist=checklist,
        report_name=report_name,
        device_serial=device_serial,
        status="pending",
    )


# ── 加密工具（与 views.py 共享实现）──


def _get_cipher() -> Fernet:
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt_key(plain: str) -> str:
    """加密 API Key。"""
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
        logger.exception("API key decryption failed — key may be corrupted or SECRET_KEY rotated")
        return ""


def mask_key(key: str) -> str:
    """脱敏显示 API Key：保留前 3 位 + *** + 后 4 位。"""
    if not key or len(key) < 8:
        return "***"
    return key[:3] + "***" + key[-4:]


def _transform_route_configs(route_configs: dict, transform) -> dict:
    """对 route_configs 内每条线路模型的 api_key 应用 transform。"""
    result = {}
    for route, models in (route_configs or {}).items():
        if not isinstance(models, dict):
            continue
        result[route] = {}
        for role, cfg in models.items():
            if not isinstance(cfg, dict):
                continue
            new_cfg = dict(cfg)
            if new_cfg.get("api_key"):
                new_cfg["api_key"] = transform(new_cfg["api_key"])
            result[route][role] = new_cfg
    return result


def encrypt_route_configs(route_configs: dict, old: dict | None = None) -> dict:
    """加密 route_configs 内 api_key；含 *** 的键保留旧加密值。"""
    old = old or {}
    result = {}
    for route, models in (route_configs or {}).items():
        if not isinstance(models, dict):
            continue
        result[route] = {}
        old_models = old.get(route) or {}
        for role, cfg in models.items():
            if not isinstance(cfg, dict):
                continue
            new_cfg = dict(cfg)
            key = new_cfg.get("api_key", "")
            if "***" in key:
                new_cfg["api_key"] = (old_models.get(role) or {}).get("api_key", "")
            elif key:
                new_cfg["api_key"] = encrypt_key(key)
            result[route][role] = new_cfg
    return result


def decrypt_route_configs(route_configs: dict) -> dict:
    """解密 route_configs 内 api_key。"""
    return _transform_route_configs(route_configs, decrypt_key)


def mask_route_configs(route_configs: dict) -> dict:
    """脱敏 route_configs 内 api_key。"""
    return _transform_route_configs(route_configs, mask_key)


def get_route_model_config(agent: AIAgent, route: str, role: str) -> dict:
    """获取某线路某角色（planner/executor）的解密模型配置（供执行用）。"""
    models = (agent.route_configs or {}).get(route) or {}
    cfg = dict(models.get(role) or {})
    if cfg.get("api_key"):
        cfg["api_key"] = decrypt_key(cfg["api_key"])
    return cfg


# ── 跨模块接口（供 evaluator 等使用，避免直接导入 agent_scope 内部模块）──


def get_provider_config(provider: str, base_url: str = "", model_name: str = "") -> dict:
    """获取模型 provider 的 API 配置（base_url + api_key 模式）。
    供 evaluator 等跨模块调用，避免直接导入 agent_scope.provider_registry。
    """
    from apps.ai_assistant.agent_scope.provider_registry import get_provider_config as _get

    return _get(provider, base_url)


def search_knowledge(query: str, top_k: int = 5, sources: list[str] | None = None) -> list[dict]:
    """搜索知识库（已移除，返回空列表）。"""
    return []


def get_kb_doc_count() -> int:
    """获取知识库文档总数（已移除，返回 0）。"""
    return 0
