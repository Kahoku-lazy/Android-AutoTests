"""ai-assistant API — 跨模块调用的公共接口。

遵循防火墙 #2：所有跨模块写操作必须通过本文件的函数。
"""

import base64
import hashlib
import json
import logging
import os
import shutil

from cryptography.fernet import Fernet
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone

from apps.ai_assistant.deepseek_billing import task_deepseek_cost
from apps.ai_assistant.models import (
    AIAgent,
    AIConversation,
    AIExecutionLog,
    AIMessage,
    AIPlatformTool,
    AISharedTool,
    AITask,
)
from apps.ai_assistant.skills_catalog import SHARED_SKILLS_DIR, scan_skill_folders, skill_origin

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
    "update_route_connectivity",
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
    "ensure_disk_skills",
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
    "start_task",
    "patch_task_progress",
    "finalize_task",
    "delete_task",
    "clear_agent_tasks",
    "parse_task_result",
    "task_result_preview",
    "serialize_agent_task_row",
    "serialize_agent_task_detail",
    "dump_task_run_payload",
    "task_deepseek_cost",
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


def update_route_connectivity(
    agent: AIAgent, route: str, *, connected: bool, checked_at, results: dict
) -> None:
    """把某条线路的校验结果写入 route_configs.health，并同步智能体级连通字段。"""
    agent.refresh_from_db(fields=["route_configs"])
    configs = dict(agent.route_configs or {})
    current = dict(configs.get(route) or {})
    stamp = (
        checked_at.isoformat(sep=" ", timespec="seconds")
        if hasattr(checked_at, "isoformat")
        else str(checked_at)
    )
    current["health"] = {
        "is_connected": bool(connected),
        "last_checked_at": stamp,
        "results": results or {},
    }
    configs[route] = current
    agent.route_configs = configs
    healths = []
    for key in ("device_control",):
        health = (configs.get(key) or {}).get("health")
        if isinstance(health, dict) and "is_connected" in health:
            healths.append(bool(health["is_connected"]))
    agent.is_connected = all(healths) if healths else bool(connected)
    agent.last_checked_at = checked_at
    agent.save(update_fields=["route_configs", "is_connected", "last_checked_at", "updated_at"])


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
    from apps.ai_assistant.tools import TOOLS

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


def create_shared_skill(
    name: str,
    file_count: int,
    size_bytes: int,
    features: str,
    *,
    origin: str = "uploaded",
    description: str | None = None,
) -> AISharedTool:
    """新增共享 skill 项（文件内容由调用方写入 engines/ai/skills/{name}/）。"""
    desc = description if description is not None else f"{file_count} 个文件 — {features}"
    return AISharedTool.objects.create(
        name=name,
        item_type="skill",
        description=desc,
        config_json=json.dumps(
            {
                "file_count": file_count,
                "size_bytes": size_bytes,
                "features": features,
                "origin": origin,
            }
        ),
    )


def ensure_disk_skills() -> None:
    """磁盘上有 SKILL.md 的文件夹若无库记录则补一条（origin=local）。"""
    existing = set(
        AISharedTool.objects.filter(item_type="skill").values_list("name", flat=True)
    )
    for folder in scan_skill_folders():
        name = folder["folder"]
        if name in existing:
            continue
        create_shared_skill(
            name,
            folder["file_count"],
            folder["size_bytes"],
            "local",
            origin="local",
            description=folder["description"] or name,
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
    """删除共享工具箱项；仅上传 skill 可删并清目录。本地 skill 拒绝删除。"""
    if item.item_type == "skill":
        if skill_origin(item) == "local":
            raise ValueError("仓库内置 Skill 不能删除")
        skill_dir = os.path.join(SHARED_SKILLS_DIR, item.name)
        if os.path.isdir(skill_dir):
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
    attachment: str = "",
    device_serial: str = "",
) -> AITask:
    """创建任务（任务发布）。"""
    return AITask.objects.create(
        agent=agent,
        title=title,
        goal=goal,
        attachment=attachment,
        device_serial=device_serial,
        status="pending",
    )


def start_task(task: AITask) -> AITask:
    """标记任务开始执行（异步执行线程启动时调用）。"""
    task.status = "running"
    task.started_at = timezone.now()
    task.save(update_fields=["status", "started_at"])
    return task


def patch_task_progress(
    task: AITask,
    *,
    result: str,
    usage: dict | None = None,
) -> AITask:
    """运行中增量写入过程 JSON，不改 status / finished_at。"""
    task.result = result
    fields = ["result"]
    if usage:
        task.input_tokens = int(usage.get("input_tokens") or 0)
        task.output_tokens = int(usage.get("output_tokens") or 0)
        task.cache_input_tokens = int(usage.get("cache_input_tokens") or 0)
        task.model_usage = usage.get("models") or {}
        task.by_role = usage.get("by_role") or {}
        fields += ["input_tokens", "output_tokens", "cache_input_tokens", "model_usage", "by_role"]
    task.save(update_fields=fields)
    return task


def finalize_task(
    task: AITask,
    *,
    status: str,
    result: str = "",
    usage: dict | None = None,
) -> AITask:
    """完成任务：状态/结果/完成时间 + 累计 token 用量（任务发布完成时调用）。

    usage 为工作流返回的任务级 token 累加器（含按模型拆分），空则只落状态/结果。
    """
    task.status = status
    task.result = result
    task.finished_at = timezone.now()
    fields = ["status", "result", "finished_at"]
    if usage:
        task.input_tokens = int(usage.get("input_tokens") or 0)
        task.output_tokens = int(usage.get("output_tokens") or 0)
        task.cache_input_tokens = int(usage.get("cache_input_tokens") or 0)
        task.model_usage = usage.get("models") or {}
        task.by_role = usage.get("by_role") or {}
        fields += ["input_tokens", "output_tokens", "cache_input_tokens", "model_usage", "by_role"]
    task.save(update_fields=fields)
    return task


def delete_task(task: AITask) -> None:
    """删除任务发布记录。"""
    task.delete()


def clear_agent_tasks(agent: AIAgent) -> int:
    """调试：清空该智能体下全部任务发布记录，返回删除条数。"""
    deleted, _ = AITask.objects.filter(agent=agent).delete()
    return deleted


def parse_task_result(raw: str) -> dict:
    """解析任务 result 文本：JSON 对象原样返回，纯文本包成 {summary}。"""
    text = (raw or "").strip()
    if not text:
        return {}
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        return {"summary": text}
    if isinstance(obj, dict):
        return obj
    return {"summary": str(obj)}


def task_result_preview(raw: str, limit: int = 120) -> str:
    """列表卡片用的短摘要，避免把整份过程 JSON 下发。"""
    obj = parse_task_result(raw)
    summary = obj.get("summary") or obj.get("message") or obj.get("reason") or ""
    if not summary and isinstance(obj.get("completed"), list) and obj["completed"]:
        summary = f"已完成 {len(obj['completed'])} 项"
    if not summary:
        summary = (raw or "").strip()
    summary = " ".join(str(summary).split())
    if len(summary) > limit:
        return summary[:limit] + "…"
    return summary


def serialize_agent_task_row(task: AITask) -> dict:
    """任务发布列表行。"""
    return {
        "id": task.id,
        "title": task.title,
        "goal": task.goal,
        "status": task.status,
        "result": task_result_preview(task.result),
        "device_serial": task.device_serial,
        "created_at": str(task.created_at) if task.created_at else "",
    }


def serialize_agent_task_detail(task: AITask) -> dict:
    """任务发布详情（含过程日志）。"""
    return {
        "id": task.id,
        "title": task.title,
        "goal": task.goal,
        "status": task.status,
        "device_serial": task.device_serial,
        "created_at": str(task.created_at) if task.created_at else "",
        "started_at": str(task.started_at) if task.started_at else "",
        "finished_at": str(task.finished_at) if task.finished_at else "",
        "input_tokens": task.input_tokens,
        "output_tokens": task.output_tokens,
        "cache_input_tokens": task.cache_input_tokens,
        "model_usage": task.model_usage or {},
        "deepseek_cost": task_deepseek_cost(task),
        "run": parse_task_result(task.result),
    }


def dump_task_run_payload(payload: dict) -> str:
    """过程结果落库为 JSON 文本。"""
    return json.dumps(payload, ensure_ascii=False)


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


def encrypt_route_configs(route_configs: dict, old: dict | None = None) -> dict:
    """加密 route_configs 内 api_key；含 *** 的键保留旧加密值。"""
    old = old or {}
    result = {}
    for route, models in (route_configs or {}).items():
        if not isinstance(models, dict):
            continue
        old_models = old.get(route) or {}
        result[route] = {}
        _copy_route_meta(old_models, result[route])
        _copy_route_meta(models, result[route])
        for role in ROUTE_MODEL_ROLES:
            cfg = models.get(role)
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
    from apps.ai_assistant.provider_registry import get_provider_config as _get

    return _get(provider, base_url)


def search_knowledge(query: str, top_k: int = 5, sources: list[str] | None = None) -> list[dict]:
    """搜索知识库（AgentScope RAG + chromadb 向量检索）。"""
    from . import rag_service

    return rag_service.search(query, top_k)


def get_kb_doc_count() -> int:
    """获取知识库文档总数。"""
    from . import rag_service

    return rag_service.kb_doc_count()


def list_kb_documents() -> list[dict]:
    """列出 data/rag_datas 下的文档（磁盘层级，非向量库 UUID）。"""
    from . import kb_files

    return kb_files.list_rag_files()


def reindex_knowledge() -> dict:
    """重新索引 data/rag_datas 下的文档。"""
    from . import rag_service

    return rag_service.index_rag_directory()
