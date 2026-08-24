"""ai-assistant API — 跨模块调用的公共接口。

遵循防火墙 #2：所有跨模块写操作必须通过本文件的函数。
"""

import base64
import hashlib
import logging
import os

from cryptography.fernet import Fernet
from django.conf import settings

from apps.ai_assistant.models import (
    AIAgent,
    AIConversation,
    AIExecutionLog,
    AIMessage,
    AISharedTool,
    AITool,
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
    "sync_agent_tools",
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
    "import_shared_tool",
    "set_tool_enabled",
    "delete_agent_tool",
    # 消息操作
    "save_message",
    # 加密工具
    "encrypt_key",
    "decrypt_key",
    "mask_key",
    # 跨模块接口（供 evaluator 等使用）
    "get_kb_doc_count",
    "get_provider_config",
    "search_knowledge",
    # 跨模块只读助手（供 dashboard 等使用，fix-cross-app-firewall）
    "filter_agents_for_user",
]


# ── 跨模块只读助手 ──


def filter_agents_for_user(queryset, user_id: str | None):
    """Scope agent list to user-owned rows only（自 permissions 平移，跨 App 合法通道）。"""
    if not user_id:
        return queryset.none()
    return queryset.filter(owner_id=user_id)


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
    "temperature": 0.7,
    "max_tokens": 4096,
    "formatter": "dashscope",
    "max_iters": 20,
    "parallel_tool_calls": True,
    "memory_mode": "inmemory",
    "long_term_memory_mode": "both",
    "enable_rewrite_query": True,
    "generate_kwargs": "{}",
    "compression_threshold": 10000,
    "compression_keep_recent": 3,
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
        api_key=encrypt_key(data.get("api_key", "")),
        base_url=data.get("base_url", ""),
        system_prompt=data.get("system_prompt", ""),
        temperature=data.get("temperature", _AGENT_CREATE_DEFAULTS["temperature"]),
        max_tokens=data.get("max_tokens", _AGENT_CREATE_DEFAULTS["max_tokens"]),
        formatter=data.get("formatter", _AGENT_CREATE_DEFAULTS["formatter"]),
        max_iters=data.get("max_iters", _AGENT_CREATE_DEFAULTS["max_iters"]),
        parallel_tool_calls=data.get(
            "parallel_tool_calls", _AGENT_CREATE_DEFAULTS["parallel_tool_calls"]
        ),
        print_hint_msg=data.get("print_hint_msg", False),
        memory_mode=data.get("memory_mode", _AGENT_CREATE_DEFAULTS["memory_mode"]),
        long_term_memory_mode=data.get(
            "long_term_memory_mode", _AGENT_CREATE_DEFAULTS["long_term_memory_mode"]
        ),
        enable_meta_tool=data.get("enable_meta_tool", False),
        enable_rewrite_query=data.get(
            "enable_rewrite_query", _AGENT_CREATE_DEFAULTS["enable_rewrite_query"]
        ),
        enable_knowledge_base=data.get("enable_knowledge_base", False),
        enable_workspace_tools=data.get("enable_workspace_tools", False),
        enable_business_tools=data.get("enable_business_tools", False),
        enable_mcp_tools=data.get("enable_mcp_tools", False),
        enable_skills=data.get("enable_skills", False),
        generate_kwargs=data.get("generate_kwargs", _AGENT_CREATE_DEFAULTS["generate_kwargs"]),
        compression_enabled=data.get("compression_enabled", False),
        compression_threshold=data.get(
            "compression_threshold", _AGENT_CREATE_DEFAULTS["compression_threshold"]
        ),
        compression_keep_recent=data.get(
            "compression_keep_recent", _AGENT_CREATE_DEFAULTS["compression_keep_recent"]
        ),
        compression_prompt=data.get("compression_prompt", ""),
        compression_template=data.get("compression_template", ""),
        tts_enabled=data.get("tts_enabled", False),
        skills_config=data.get("skills_config", {}),
        knowledge_sources=data.get("knowledge_sources", {}),
        key_revealed=False,
    )
    for t in data.get("tools", []):
        AITool.objects.create(
            agent=a,
            name=t.get("name", ""),
            tool_type=t.get("tool_type", "mcp"),
            config_json=t.get("config_json", "{}"),
            enabled=t.get("enabled", True),
        )
    return a


def update_agent(agent: AIAgent, data: dict) -> AIAgent:
    """更新 Agent 配置。脱敏 Key 跳过、Key 变更重置 reveal 标记、prompt 变更清 agent_scope_id。"""
    data = dict(data)  # 避免修改调用方（Serializer.validated_data）的字典
    key_changed = False
    prompt_changed = False
    if "api_key" in data and data["api_key"]:
        # Frontend sends masked value (contains "***") when key is unchanged
        if "***" in data["api_key"]:
            del data["api_key"]
        else:
            data["api_key"] = encrypt_key(data["api_key"])
            key_changed = True
    for f in [
        "name",
        "avatar",
        "tags",
        "description",
        "model_provider",
        "model_name",
        "api_key",
        "base_url",
        "system_prompt",
        "temperature",
        "max_tokens",
        "formatter",
        "max_iters",
        "parallel_tool_calls",
        "print_hint_msg",
        "memory_mode",
        "long_term_memory_mode",
        "enable_meta_tool",
        "enable_rewrite_query",
        "enable_knowledge_base",
        "enable_workspace_tools",
        "enable_business_tools",
        "enable_mcp_tools",
        "enable_skills",
        "generate_kwargs",
        "compression_enabled",
        "compression_threshold",
        "compression_keep_recent",
        "compression_prompt",
        "compression_template",
        "tts_enabled",
        "status",
        "skills_config",
        "knowledge_sources",
    ]:
        if f in data:
            if f == "system_prompt" and str(getattr(agent, f, "")) != str(data[f]):
                prompt_changed = True
            setattr(agent, f, data[f])
    if key_changed:
        agent.key_revealed = False
    # When system_prompt changes, clear agent_scope_id so it gets
    # re-registered with the new prompt on the next session creation.
    if prompt_changed and agent.agent_scope_id:
        agent.agent_scope_id = ""
    agent.save()
    if "tools" in data:
        sync_agent_tools(agent, data["tools"])
    if "platform_tools" in data:
        sync_platform_tools(agent, data["platform_tools"])
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


def sync_agent_tools(agent: AIAgent, tools_data: list) -> None:
    """Diff-based tool sync: add new, update changed, remove deleted.

    Avoids the DELETE-ALL + INSERT-ALL anti-pattern — only touches
    rows that actually changed, preserving primary keys.
    """
    existing = {t.name: t for t in agent.tools.all()}
    incoming = {}
    for t in tools_data:
        name = (t.get("name") or "").strip()
        if not name:
            continue
        incoming[name] = t

    # Delete removed tools
    for name, existing_tool in existing.items():
        if name not in incoming:
            existing_tool.delete()

    # Create new / update existing
    for name, tool_data in incoming.items():
        if name in existing:
            et = existing[name]
            new_config = tool_data.get("config_json", "{}")
            new_type = tool_data.get("tool_type", "mcp")
            new_enabled = tool_data.get("enabled", True)
            if (
                et.config_json != new_config
                or et.tool_type != new_type
                or et.enabled != new_enabled
            ):
                et.config_json = new_config
                et.tool_type = new_type
                et.enabled = new_enabled
                et.save()
        else:
            AITool.objects.create(
                agent=agent,
                name=name,
                tool_type=tool_data.get("tool_type", "mcp"),
                config_json=tool_data.get("config_json", "{}"),
                enabled=tool_data.get("enabled", True),
            )


def sync_platform_tools(agent: AIAgent, names: list[str]) -> None:
    """同步平台工具勾选（仅 tool_type='platform'）：删除未勾选、补齐新勾选。

    编辑模式前端经 AgentInputSerializer.platform_tools 提交勾选结果。
    只动 platform 类型记录——MCP/Skill 副本（含 skill 目录配置）不受影响。
    名字以 TOOL_SCHEMAS 为准过滤，防止无效记录入库。
    """
    from apps.ai_assistant.agent_scope.tool_registry import TOOL_SCHEMAS

    valid_names = {t["name"] for t in TOOL_SCHEMAS}
    wanted = {n.strip() for n in (names or []) if n and n.strip() in valid_names}
    for record in agent.tools.filter(tool_type="platform"):
        if record.name not in wanted:
            record.delete()
        elif not record.enabled:
            record.enabled = True
            record.save(update_fields=["enabled"])
    existing = set(agent.tools.filter(tool_type="platform").values_list("name", flat=True))
    for name in wanted - existing:
        AITool.objects.create(
            agent=agent,
            name=name,
            tool_type="platform",
            config_json="{}",
            enabled=True,
        )


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

# Agent 专属 skill 目录 —— 必须与 agent_factory._resolve_skill_paths 的加载根一致
_AGENT_SKILLS_DIR = os.path.join("data", "agentscope_workspaces", "skills")


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


def import_shared_tool(agent_id: int, shared: AISharedTool) -> AITool | None:
    """导入共享项到 Agent（生成 per-agent AITool 副本）。重名返回 None。"""
    exists = AITool.objects.filter(
        agent_id=agent_id,
        name=shared.name,
        tool_type=shared.item_type,
    ).exists()
    if exists:
        return None

    # For skill type, copy files to agent's skill directory
    # （与 agent_factory._resolve_skill_paths 的加载目录保持一致）
    config = shared.config_json
    if shared.item_type == "skill":
        src_dir = os.path.join(_SHARED_SKILLS_DIR, str(shared.id))
        dst_dir = os.path.join(_AGENT_SKILLS_DIR, str(agent_id), shared.name)
        if os.path.isdir(src_dir) and not os.path.isdir(dst_dir):
            import json as _json
            import shutil

            shutil.copytree(src_dir, dst_dir)
            cfg = _json.loads(config) if isinstance(config, str) else config
            cfg["dir_path"] = dst_dir
            config = _json.dumps(cfg)

    return AITool.objects.create(
        agent_id=agent_id,
        name=shared.name,
        tool_type=shared.item_type,
        config_json=config,
        enabled=True,
    )


def set_tool_enabled(tool: AITool, enabled: bool) -> AITool:
    """启用/禁用 Agent 工具。"""
    tool.enabled = enabled
    tool.save(update_fields=["enabled"])
    return tool


def delete_agent_tool(tool: AITool) -> None:
    """删除 Agent 工具；skill 类型同步清理目录（限定 _AGENT_SKILLS_DIR 内）。"""
    if tool.tool_type == "skill":
        try:
            import json as _json

            from pathlib import Path

            cfg = _json.loads(tool.config_json)
            dir_path = cfg.get("dir_path", "")
            if dir_path:
                skill_dir = Path(dir_path)
                skills_root = Path(_AGENT_SKILLS_DIR).resolve()
                if skill_dir.exists() and str(skill_dir.resolve()).startswith(str(skills_root)):
                    import shutil

                    shutil.rmtree(skill_dir)
        except Exception:
            logger.exception("Skill dir cleanup failed for tool_id=%s", tool.id)

    tool.delete()


# ── 消息操作 ──


def save_message(
    conversation_id: int,
    role: str,
    content: str,
    blocks: str = "",
    reason: str = "normal",
    tokens: int = 0,
    input_tokens: int = 0,
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
        model_name=model_name,
        flow=flow if flow in ("sse", "fallback") else "",
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


# ── 跨模块接口（供 evaluator 等使用，避免直接导入 agent_scope 内部模块）──


def get_provider_config(provider: str, base_url: str = "", model_name: str = "") -> dict:
    """获取模型 provider 的 API 配置（base_url + api_key 模式）。
    供 evaluator 等跨模块调用，避免直接导入 agent_scope.provider_registry。
    """
    from apps.ai_assistant.agent_scope.provider_registry import get_provider_config as _get

    return _get(provider, base_url)


def search_knowledge(query: str, top_k: int = 5, sources: list[str] | None = None) -> list[dict]:
    """搜索知识库。供 evaluator 等跨模块调用。"""
    from apps.ai_assistant.agent_scope.rag_service import search

    return search(query, top_k=top_k, sources=sources)


def get_kb_doc_count() -> int:
    """获取知识库文档总数。供 evaluator 等跨模块调用。"""
    from apps.ai_assistant.agent_scope.rag_service import _get_collection

    return _get_collection().count()
