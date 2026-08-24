"""Agent factory — build AgentScope Agent instances from Django AIAgent config.

Replaces the HTTP-based registration flow (register agent → create credential →
create session in AgentScope FastAPI) with direct in-process Agent construction.
"""

from __future__ import annotations

import json
import logging
import os

from pathlib import Path

from agentscope.agent import Agent
from agentscope.agent._config import ContextConfig, ModelConfig, ReActConfig
from agentscope.credential import DashScopeCredential, OpenAICredential
from agentscope.model import DashScopeChatModel, OpenAIChatModel
from agentscope.tool import Toolkit

from apps.ai_assistant.agent_scope.in_process_tool import build_platform_tools
from apps.ai_assistant.agent_scope.provider_registry import get_provider_config
from apps.ai_assistant.api import decrypt_key

logger = logging.getLogger("ai_assistant.factory")

# ── Workspace tool imports (AgentScope built-in) ──
from agentscope.tool._builtin import Bash, Edit, Glob, Grep, Read, Write

# ── Workspace directory for file-system tools (Bash/Edit/Glob/Grep/Read/Write) ──
_WORKSPACE_ROOT = Path(os.environ.get("AGENTSCOPE_WORKSPACE_DIR", "data/agentscope_workspaces"))

# ═══════════════════════════════════════════════════════════════════════
# Agent construction
# ═══════════════════════════════════════════════════════════════════════


def build_agent(
    agent_model,
    user_id: str = "",
    conversation_id: int | None = None,
) -> Agent:
    """Build an AgentScope Agent instance from Django AIAgent model config.

    Args:
        agent_model: AIAgent Django model instance.
        user_id: Authenticated user ID for tool permission checks.
        conversation_id: Optional conversation ID for workspace isolation.

    Returns:
        Configured AgentScope Agent ready for reply_stream().
    """
    # ── 1. Resolve model ──
    api_key = decrypt_key(agent_model.api_key) if agent_model.api_key else ""
    provider_cfg = get_provider_config(agent_model.model_provider, agent_model.base_url)
    gen_params, extra_body = _resolve_generate_params(agent_model)

    model = _build_model(
        provider=agent_model.model_provider,
        model_name=agent_model.model_name,
        api_key=api_key,
        base_url=provider_cfg["base_url"],
        gen_params=gen_params,
        extra_body=extra_body,
    )

    # ── 2. Build toolkit ──
    toolkit = _build_toolkit(agent_model, user_id)

    # ── 3. Build configs ──
    model_config = _build_model_config(agent_model)
    context_config = _build_context_config(agent_model)
    react_config = ReActConfig(
        max_iters=agent_model.max_iters or 10,
        parallel_tool_calls=agent_model.parallel_tool_calls,
    )

    # ── 4. System prompt ──
    system_prompt = agent_model.system_prompt or ""

    # ── 5. Create Agent ──
    agent = Agent(
        name=agent_model.name,
        system_prompt=system_prompt,
        model=model,
        toolkit=toolkit,
        model_config=model_config,
        context_config=context_config,
        react_config=react_config,
    )

    logger.info(
        "Built agent '%s' (id=%s) model=%s/%s tools=%d",
        agent_model.name,
        agent_model.id,
        agent_model.model_provider,
        agent_model.model_name,
        len(toolkit.tool_groups[0].tools) if toolkit.tool_groups else 0,
    )

    return agent


# ═══════════════════════════════════════════════════════════════════════
# Internal helpers
# ═══════════════════════════════════════════════════════════════════════


def _build_model(
    provider: str,
    model_name: str,
    api_key: str,
    base_url: str,
    gen_params: dict | None = None,
    extra_body: dict | None = None,
):
    """Create the appropriate ChatModelBase subclass.

    ``gen_params``（temperature/max_tokens 等已知参数）进入模型 Parameters，
    ``extra_body``（generate_kwargs 中的其余键）附加到 API 请求体。
    """
    gen_params = gen_params or {}
    if provider == "dashscope":
        params_cls = DashScopeChatModel.Parameters
        return DashScopeChatModel(
            credential=DashScopeCredential(api_key=api_key),
            model=model_name,
            parameters=_filter_params(params_cls, gen_params),
        )

    # All other providers use OpenAI-compatible API
    params_cls = OpenAIChatModel.Parameters
    return OpenAIChatModel(
        credential=OpenAICredential(
            api_key=api_key,
            base_url=base_url,
        ),
        model=model_name,
        parameters=_filter_params(params_cls, gen_params),
        extra_body=extra_body or None,
    )


def _filter_params(params_cls, gen_params: dict):
    """仅保留参数类实际存在的字段，避免未知键导致构造失败。"""
    valid = set(getattr(params_cls, "model_fields", {}).keys())
    filtered = {k: v for k, v in gen_params.items() if k in valid}
    return params_cls(**filtered) if filtered else None


# 已知模型参数键（generate_kwargs 中这些键路由进模型 Parameters，其余走 extra_body）
_MODEL_PARAM_KEYS = {
    "max_tokens",
    "temperature",
    "top_p",
    "parallel_tool_calls",
    "thinking_enable",
    "reasoning_effort",
    "voice",
}


def _resolve_generate_params(agent_model) -> tuple[dict, dict]:
    """接线配置页的温度 / 最大Token / 生成参数。

    返回 (gen_params, extra_body)：
      - temperature / max_tokens 专用字段优先；
      - generate_kwargs（JSON 字符串）解析后，已知参数键并入 gen_params，
        其余键作为 extra_body 附加到请求体。
    """
    raw = (agent_model.generate_kwargs or "").strip()
    data: dict = {}
    if raw:
        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Invalid generate_kwargs for agent %s: %r", agent_model.id, raw)
            parsed = {}
        if isinstance(parsed, dict):
            data = parsed

    gen_params: dict = {}
    extra_body: dict = {}
    for k, v in data.items():
        if k in _MODEL_PARAM_KEYS:
            gen_params[k] = v
        else:
            extra_body[k] = v
    # 专用字段显式优先，覆盖 generate_kwargs 中同名键
    gen_params["temperature"] = agent_model.temperature
    gen_params["max_tokens"] = agent_model.max_tokens
    return gen_params, extra_body


def _build_toolkit(agent_model, user_id: str) -> Toolkit:
    """Build Toolkit from agent capability flags and configuration."""
    tools: list = []
    skill_paths: list[str] = []
    mcp_clients: list = []

    # ── Workspace tools (Bash/Edit/Glob/Grep/Read/Write) ──
    if agent_model.enable_workspace_tools:
        workdir = _ensure_workdir(agent_model.id)
        # Use standard paths as backend for workspace tools
        tools.extend(_build_workspace_tools(agent_model, workdir))

    # ── Platform business tools (15 tools from tool_registry) ──
    if agent_model.enable_business_tools:
        enabled = _resolve_enabled_tools(agent_model)
        platform_tools = build_platform_tools(
            user_id=user_id,
            enabled_names=enabled,
            knowledge_sources=list(agent_model.knowledge_sources.keys())
            if agent_model.knowledge_sources
            else None,
        )
        tools.extend(platform_tools)

    # ── MCP tools ──
    if agent_model.enable_mcp_tools:
        mcp_clients = _build_mcp_clients(agent_model)

    # ── Skills ──
    if agent_model.enable_skills:
        skill_paths = _resolve_skill_paths(agent_model)

    return Toolkit(
        tools=tools,
        skills_or_loaders=skill_paths if skill_paths else None,
        mcps=mcp_clients if mcp_clients else None,
    )


def _build_workspace_tools(agent_model, workdir: str) -> list:
    """Build workspace tools filtered by skills_config."""
    # Map AgentScope built-in tool class → name used in skills_config
    _TOOL_CLASS_MAP = {
        Bash: "Bash",
        Edit: "Edit",
        Glob: "Glob",
        Grep: "Grep",
        Read: "Read",
        Write: "Write",
    }

    disabled = set()
    skills_config = agent_model.skills_config or {}
    for name, enabled in skills_config.items():
        if not enabled:
            disabled.add(name)

    tools = []
    for tool_cls, tool_name in _TOOL_CLASS_MAP.items():
        if tool_name not in disabled:
            tools.append(tool_cls(cwd=workdir))
    return tools


def _resolve_enabled_tools(agent_model) -> set[str] | None:
    """Determine which platform tools are enabled for this agent.

    Returns a set of tool names, or None to enable all (default).
    """
    from apps.ai_assistant.agent_scope.tool_registry import TOOL_SCHEMAS

    # Check if agent has per-tool toggles via AITool records
    tool_records = list(agent_model.tools.filter(tool_type="platform"))
    if tool_records:
        enabled = {t.name for t in tool_records if t.enabled}
    else:
        # No per-tool config — default to all read-only tools as safety fallback
        enabled = {t["name"] for t in TOOL_SCHEMAS if t.get("read_only", True)}

    # 知识库开关未开启时，不装配知识库检索工具（开关独立于业务工具清单）
    if not agent_model.enable_knowledge_base:
        enabled.discard("search_knowledge_base")
    return enabled


def _build_mcp_clients(agent_model) -> list:
    """Build MCP clients from agent's AITool records."""
    from agentscope.mcp import MCPClient

    clients = []
    for tool_record in agent_model.tools.filter(tool_type="mcp", enabled=True):
        try:
            config = json.loads(tool_record.config_json)
            client = MCPClient(
                name=tool_record.name,
                transport=config.get("transport", "stdio"),
                command=config.get("command", ""),
                args=config.get("args", []),
                env=config.get("env", {}),
                url=config.get("url", ""),
                headers=config.get("headers", {}),
            )
            clients.append(client)
        except Exception:
            logger.warning(
                "Failed to build MCP client '%s' for agent %s",
                tool_record.name,
                agent_model.id,
                exc_info=True,
            )
    return clients


def _resolve_skill_paths(agent_model) -> list[str]:
    """Resolve skill directories for this agent.

    Toolkit 将每个 str 路径包装为 LocalSkillLoader(scan_subdir=False)，
    只加载目录根下的 SKILL.md —— 因此逐个返回含 SKILL.md 的技能子目录。
    """
    paths = []
    agent_skill_dir = _WORKSPACE_ROOT / "skills" / str(agent_model.id)
    if agent_skill_dir.is_dir():
        for entry in sorted(agent_skill_dir.iterdir()):
            if entry.is_dir() and (entry / "SKILL.md").is_file():
                paths.append(str(entry))
    return paths


def _build_model_config(agent_model) -> ModelConfig:
    """Build ModelConfig from agent settings."""
    model_config = ModelConfig()
    model_config.max_retries = 2
    return model_config


def _build_context_config(agent_model) -> ContextConfig:
    """Build ContextConfig from agent compression settings."""
    cfg = ContextConfig()
    if agent_model.compression_enabled:
        # ContextConfig 约束 trigger_ratio ∈ (0, 0.9)，阈值上限 100000 时夹到 0.89
        cfg.trigger_ratio = min((agent_model.compression_threshold or 10000) / 100000.0, 0.89)
        # compression_keep_recent（条）→ reserve_ratio（比例）粗略换算：
        # 按平均每条约 1500 tokens、128k 上下文窗口估算，夹在 [0.05, 0.5]
        keep = max(agent_model.compression_keep_recent or 1, 1)
        cfg.reserve_ratio = min(max(keep * 1500 / 128_000, 0.05), 0.5)
        if agent_model.compression_prompt:
            cfg.compression_prompt = agent_model.compression_prompt
        if agent_model.compression_template:
            cfg.summary_template = agent_model.compression_template
    return cfg


def _ensure_workdir(agent_id) -> str:
    """Ensure workspace directory exists for agent. Returns path string."""
    workdir = _WORKSPACE_ROOT / "agents" / str(agent_id)
    workdir.mkdir(parents=True, exist_ok=True)
    return str(workdir)
