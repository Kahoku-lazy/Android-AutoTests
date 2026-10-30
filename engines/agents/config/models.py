"""
文件名: ➡️ models.py 🏁
路径: ➡️ engines/agents/config/models.py 🏁
模块功能：➡️ 模型角色 🏁
Python 调试：➡️python -m engines.agents.config.models 🏁
时间：➡️ 2026-10-29 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-10-30 🏁
类型: ➡️ 模型配置模块 🏁
简介说明：➡️
1. ModelConfig: 模型配置（提供商、模型名、API 密钥、基础 URL、vision、stream）
2. RealtimeModelConfig / omni_realtime_model: DashScope Omni 实时语音（agent_config OMNI_ROLE_CONFIG）
3. apply_forced_handover_kwargs / bind_forced_handover: 强制交卷时关闭思考
4. ChatModelFactory: 按 provider 创建 DeepSeek / DashScope / OpenAI 模型
5. load_role_config / ui_* / case_*_role_config: 从 agent_config.yaml 装 ModelConfig+四分段
6. executor_model / verifier_model: 仅构建 ChatModelFactory
🏁
关联模块：➡️
1. engines.agents.config.config: load_agent_config，读取 agent_config.yaml
2. engines.agents.config.role_types: RoleConfig / ToolsConfig / ContextConfig / ReActConfig，角色装配配置类型
3. engines.agents.role_sys_prompts: resolve_system_prompt，解析系统提示词
4. utils.logs: agent_event_log，Agent 事件日志
🏁
测试：➡️
1. tests/engines/agents/test_models.py: executor/verifier 模型连通性（e2e）
2. tests/graybox/unit/test_forced_handover_thinking.py: 强制交卷关闭思考
3. tests/graybox/unit/test_case_authoring_roles.py: 经 load_role_config 装配用例编写角色
4. tests/engines/agents/test_agents.py: 经 ui_*_role_config 装配 Agent 连通性
🏁
"""
from __future__ import annotations

import os

from dataclasses import MISSING, dataclass, fields
from pathlib import Path

from agentscope.credential import DashScopeCredential, DeepSeekCredential, OpenAICredential
from agentscope.model import (
    ChatModelBase,
    DashScopeChatModel,
    DeepSeekChatModel,
    OpenAIChatModel,
)
from agentscope.tool import Toolkit
from pydantic import SecretStr

from engines.agents.config.config import load_agent_config
from engines.agents.config.role_types import (
    ContextConfig,
    ReActConfig,
    RoleConfig,
    ToolsConfig,
)
from utils.logs import agent_event_log

# 框架在自由推理用尽后，会把工具选择强制成这个名字。
_FORCED_HANDOVER_TOOL = "GenerateStructuredOutput"


@dataclass(frozen=True)
class ModelConfig:
    """
    模型配置：提供商、模型名称、API 密钥、基础 URL，以及 vision / stream。

    Attributes:
        provider: 模型提供商，可选 deepseek、openai、dashscope。
        model_name: 模型名称，如 deepseek-chat、gpt-4o、qwen-plus。
        api_key: API 密钥，字符串或 SecretStr 类型。
        base_url: 基础 URL，可选。
        vision: 是否多模态（需截图输入时为 True）。
        stream: 是否流式输出。

    Raises:
        FrozenInstanceError: 模型配置不可变。
    """

    provider: str = ""
    model_name: str = ""
    api_key: str | SecretStr = ""
    base_url: str = ""
    vision: bool = False
    stream: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.api_key, SecretStr):
            object.__setattr__(self, "api_key", SecretStr(self.api_key))
        object.__setattr__(self, "vision", bool(self.vision))
        object.__setattr__(self, "stream", bool(self.stream))


def apply_forced_handover_kwargs(model: object, tool_choice: object, kwargs: dict) -> dict:
    """强制交卷时关闭思考，并保留额外体里的其他键。其余请求原样返回。"""
    if getattr(tool_choice, "mode", None) != _FORCED_HANDOVER_TOOL:
        return kwargs
    base = dict(getattr(model, "extra_body", None) or {})
    incoming = dict(kwargs.get("extra_body") or {})
    thinking = dict(base.get("thinking") or {})
    thinking.update(dict(incoming.get("thinking") or {}))
    thinking["type"] = "disabled"
    merged = {**base, **incoming, "thinking": thinking}
    return {**kwargs, "extra_body": merged}


def bind_forced_handover(model: ChatModelBase) -> ChatModelBase:
    """挂到模型调用上：只有强制结构化交卷的那一次关闭思考。"""
    original = model._call_api

    async def _call_api(*args, **kwargs):
        kwargs = apply_forced_handover_kwargs(model, kwargs.get("tool_choice"), kwargs)
        return await original(*args, **kwargs)

    model._call_api = _call_api
    return model


class ChatModelFactory:
    """按 provider 创建 DeepSeek、DashScope 或 OpenAI 模型。"""

    def __init__(self, config: ModelConfig):
        """
        创建模型工厂：根据模型配置创建模型。

        Args:
            config: 模型配置（含 stream / vision）。
        """

        self.log = agent_event_log
        self.config = config
        self.stream = config.stream
        self.vision = config.vision

    def _credential(self, credential_cls):
        """凭证：base_url 原样传入（DeepSeek 与 OpenAI 兼容档的现有口径）。"""
        return credential_cls(api_key=self.config.api_key, base_url=self.config.base_url)

    def _credential_default_endpoint(self, credential_cls):
        """凭证：base_url 为空时不传，交给框架默认地址（DashScope 的现有口径）。"""
        if self.config.base_url:
            return credential_cls(api_key=self.config.api_key, base_url=self.config.base_url)
        return credential_cls(api_key=self.config.api_key)

    def deepseek_model(self) -> ChatModelBase:
        """创建 DeepSeek。vision 时走 OpenAI 兼容客户端，才能把截图当图片传入。"""
        config = self.config
        if self.vision:
            return OpenAIChatModel(
                credential=self._credential(OpenAICredential),
                model=config.model_name,
                parameters=OpenAIChatModel.Parameters(thinking_enable=True),
                stream=self.stream,
                extra_body={"thinking": {"type": "enabled"}},
            )
        return DeepSeekChatModel(
            credential=self._credential(DeepSeekCredential),
            model=config.model_name,
            parameters=DeepSeekChatModel.Parameters(thinking_enable=True),
            stream=self.stream,
        )

    def openai_model(self) -> OpenAIChatModel:
        """创建 OpenAI 模型。"""
        config = self.config
        return OpenAIChatModel(
            credential=self._credential(OpenAICredential),
            model=config.model_name,
            stream=self.stream,
        )

    def dashscope_model(self) -> DashScopeChatModel:
        """创建 DashScope 模型。base_url 为空时使用框架默认地址。"""
        config = self.config
        return DashScopeChatModel(
            credential=self._credential_default_endpoint(DashScopeCredential),
            model=config.model_name,
            stream=self.stream,
        )

    def create(self) -> ChatModelBase:
        """按 provider 创建模型。

        Returns:
            该 provider 对应的聊天模型实例。

        Raises:
            ValueError: provider 不在支持集合内（deepseek / openai / dashscope），
                报错会列出可选厂商。
        """
        config = self.config
        builders = {
            "deepseek": self.deepseek_model,
            "openai": self.openai_model,
            "dashscope": self.dashscope_model,
        }
        builder = builders.get(config.provider)
        if builder is None:
            raise ValueError(f"不支持的模型提供商: {config.provider}；可选：{', '.join(builders)}")
        return bind_forced_handover(builder())


def _get_api_key(env_name: str) -> SecretStr:
    """从环境变量读取 API 密钥；config 里存的是变量名。"""
    value = os.getenv(env_name)
    if not value:
        raise ValueError(f"环境变量未设置: {env_name}")
    return SecretStr(value)


def _is_empty_section(value: object) -> bool:
    """YAML 节缺失 / null / 空映射 / 空白字符串视为空。"""
    if value is None:
        return True
    if isinstance(value, dict) and not value:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def _resolve_system_prompt(raw: object, *, where: str) -> str:
    """把 RoleConfig.system_prompt 解析成正文（委托 role_sys_prompts.resolve_system_prompt）。"""
    from engines.agents.role_sys_prompts import resolve_system_prompt

    return resolve_system_prompt(raw, where=f"{where}.system_prompt")


def _merge_dataclass(cls, raw: object, *, where: str):
    """用 YAML 部分字段覆盖 dataclass 默认值；空节则全默认。"""
    if _is_empty_section(raw):
        return cls()
    if not isinstance(raw, dict):
        raise ValueError(f"{where} 必须是映射表或空")
    kwargs: dict = {}
    for f in fields(cls):
        if f.name in raw and raw[f.name] is not None:
            kwargs[f.name] = raw[f.name]
        elif f.default is not MISSING:
            kwargs[f.name] = f.default
        elif f.default_factory is not MISSING:  # type: ignore[truthy-function]
            kwargs[f.name] = f.default_factory()
        else:
            raise ValueError(f"{where}.{f.name} 缺失且无默认值")
    return cls(**kwargs)


def _build_model_config(section: dict, *, config_key: str) -> ModelConfig:
    raw_model_config = section.get("ModelConfig")
    if not isinstance(raw_model_config, dict):
        raise ValueError(f"{config_key}.ModelConfig 缺失或不是映射表")

    model_fields = dict(raw_model_config)
    env_name = model_fields.get("api_key")
    if not isinstance(env_name, str) or not env_name.strip():
        raise ValueError(f"{config_key}.ModelConfig.api_key 必须是环境变量名字符串")
    model_fields["api_key"] = _get_api_key(env_name.strip())
    if "vision" in model_fields:
        model_fields["vision"] = bool(model_fields["vision"])
    if "stream" in model_fields:
        model_fields["stream"] = bool(model_fields["stream"])
    return ModelConfig(**model_fields)


def _build_role_config(raw: object, *, where: str):

    if _is_empty_section(raw):
        raise ValueError(f"{where}.RoleConfig 为空，无法构造角色（需要 name 与 system_prompt）")
    if not isinstance(raw, dict):
        raise ValueError(f"{where}.RoleConfig 必须是映射表")
    name = raw.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"{where}.RoleConfig.name 缺失或为空")
    system_prompt = _resolve_system_prompt(raw.get("system_prompt"), where=f"{where}.RoleConfig")
    return RoleConfig(name=name.strip(), system_prompt=system_prompt)


def _build_tools_config(raw: object, *, where: str):
    """ToolsConfig 为空时默认 Toolkit()（空工具包）；不在此硬编码设备工具。

    需要执行/验收工具的调用方应在装好 ToolsConfig 后自行注入 toolkit，
    或后续扩展 YAML 以外的装配路径。
    """
    if _is_empty_section(raw):
        return ToolsConfig(toolkit=Toolkit())
    if not isinstance(raw, dict):
        raise ValueError(f"{where}.ToolsConfig 必须是映射表或空")
    toolkit = raw.get("toolkit")
    if toolkit is None:
        return ToolsConfig(toolkit=Toolkit())
    if isinstance(toolkit, Toolkit):
        return ToolsConfig(toolkit=toolkit)
    raise ValueError(
        f"{where}.ToolsConfig.toolkit 无法从 YAML 反序列化；"
        "请留空以使用 Toolkit()，或在代码中注入工具包"
    )


def load_role_config(
    config_key: str,
) -> tuple[ModelConfig, RoleConfig, ToolsConfig, ContextConfig, ReActConfig]:

    """从 agent_config.yaml 装一整包：ModelConfig + Role/Tools/Context/ReAct。

    RoleConfig / ToolsConfig / ContextConfig / ReActConfig：
    - 节缺失、null、空映射时用 dataclass 默认（ToolsConfig → Toolkit()）。
    - RoleConfig 完全为空会报错（无法臆造 name）。
    - RoleConfig.system_prompt 为 prompts 目录下的 token 时读 md 原文。

    Returns:
        五元组，可直接交给 AgentRoleFactory(...).create()。
    """
    section = load_agent_config(config_key) or {}
    if not isinstance(section, dict) or not section:
        raise ValueError(f"agent_config 缺少节 {config_key!r}")

    model_config = _build_model_config(section, config_key=config_key)
    role_cfg = _build_role_config(section.get("RoleConfig"), where=config_key)
    tools_cfg = _build_tools_config(section.get("ToolsConfig"), where=config_key)
    ctx = _merge_dataclass(
        ContextConfig, section.get("ContextConfig"), where=f"{config_key}.ContextConfig"
    )
    react = _merge_dataclass(
        ReActConfig, section.get("ReActConfig"), where=f"{config_key}.ReActConfig"
    )
    return model_config, role_cfg, tools_cfg, ctx, react


# 兼容旧名
load_role_spec = load_role_config


def _build_chat_model_factory(config_key: str) -> ChatModelFactory:
    """从 agent_config.yaml 节的 ModelConfig 建工厂。"""
    section = load_agent_config(config_key) or {}
    if not isinstance(section, dict) or not section:
        raise ValueError(f"agent_config 缺少节 {config_key!r}")
    return ChatModelFactory(_build_model_config(section, config_key=config_key))


def executor_model() -> ChatModelFactory:
    """UI 控制执行角色模型工厂（UI_EXECUTOR_ROLE_CONFIG.ModelConfig）。"""
    return _build_chat_model_factory("UI_EXECUTOR_ROLE_CONFIG")


def verifier_model() -> ChatModelFactory:
    """UI 控制验收角色模型工厂（UI_VERIFIER_ROLE_CONFIG.ModelConfig）。"""
    return _build_chat_model_factory("UI_VERIFIER_ROLE_CONFIG")


def ui_executor_role_config() -> tuple[ModelConfig, RoleConfig, ToolsConfig, ContextConfig, ReActConfig]:
    """装 UI_EXECUTOR_ROLE_CONFIG（UI 控制执行）。"""
    return load_role_config("UI_EXECUTOR_ROLE_CONFIG")


def ui_verifier_role_config() -> tuple[ModelConfig, RoleConfig, ToolsConfig, ContextConfig, ReActConfig]:
    """装 UI_VERIFIER_ROLE_CONFIG（UI 控制验收）。"""
    return load_role_config("UI_VERIFIER_ROLE_CONFIG")


def case_writer_role_config() -> tuple[ModelConfig, RoleConfig, ToolsConfig, ContextConfig, ReActConfig]:
    """装 CASE_WRITER_ROLE_CONFIG（用例编写执行）。"""
    return load_role_config("CASE_WRITER_ROLE_CONFIG")


def case_verifier_role_config() -> tuple[ModelConfig, RoleConfig, ToolsConfig, ContextConfig, ReActConfig]:
    """装 CASE_VERIFIER_ROLE_CONFIG（用例编写验收）。"""
    return load_role_config("CASE_VERIFIER_ROLE_CONFIG")


# 兼容旧名
executor_role_config = ui_executor_role_config
verifier_role_config = ui_verifier_role_config


@dataclass(frozen=True)
class RealtimeModelConfig:
    """
    DashScope Omni 实时语音模型配置（与聊天 ModelConfig 分离）。

    Attributes:
        provider: 提供商，当前仅支持 dashscope。
        model_name: 实时模型名，如 qwen3.5-omni-plus-realtime。
        api_key: API 密钥（SecretStr）。
        base_url: 可选；空则交给框架默认地址。
        voice: Parameters.voice 音色名。

    Raises:
        FrozenInstanceError: 配置不可变。
    """

    provider: str = "dashscope"
    model_name: str = "qwen3.5-omni-plus-realtime"
    api_key: str | SecretStr = ""
    base_url: str = ""
    voice: str = "Tina"

    def __post_init__(self) -> None:
        if not isinstance(self.api_key, SecretStr):
            object.__setattr__(self, "api_key", SecretStr(self.api_key))


def _import_dashscope_realtime():
    """延迟导入 agentscope realtime；缺额外依赖时给出安装提示。"""
    try:
        from agentscope.realtime import DashScopeRealtimeModel
    except ImportError as exc:
        raise RuntimeError(
            "创建实时语音模型需要 agentscope realtime 额外依赖："
            'pip install "agentscope[realtime]"'
        ) from exc
    return DashScopeRealtimeModel


def _build_realtime_model_config(section: dict, *, config_key: str) -> RealtimeModelConfig:
    raw = section.get("ModelConfig")
    if not isinstance(raw, dict):
        raise ValueError(f"{config_key}.ModelConfig 缺失或不是映射表")
    fields_map = dict(raw)
    env_name = fields_map.get("api_key")
    if not isinstance(env_name, str) or not env_name.strip():
        raise ValueError(f"{config_key}.ModelConfig.api_key 必须是环境变量名字符串")
    fields_map["api_key"] = _get_api_key(env_name.strip())
    base_url = fields_map.get("base_url", "")
    if base_url is None:
        fields_map["base_url"] = ""
    elif not isinstance(base_url, str):
        raise ValueError(f"{config_key}.ModelConfig.base_url 必须是字符串")
    for chat_only in ("vision", "stream"):
        fields_map.pop(chat_only, None)
    allowed = {f.name for f in fields(RealtimeModelConfig)}
    unknown = set(fields_map) - allowed
    if unknown:
        raise ValueError(f"{config_key}.ModelConfig 含未知字段: {sorted(unknown)}")
    return RealtimeModelConfig(**fields_map)


def load_omni_role_spec(config_key: str = "OMNI_ROLE_CONFIG") -> tuple[RealtimeModelConfig, RoleConfig]:
    """从 agent_config.yaml 装 Omni 实时角色：RealtimeModelConfig + RoleConfig。"""
    section = load_agent_config(config_key) or {}
    if not isinstance(section, dict) or not section:
        raise ValueError(f"agent_config 缺少节 {config_key!r}")
    model_config = _build_realtime_model_config(section, config_key=config_key)
    role_cfg = _build_role_config(section.get("RoleConfig"), where=config_key)
    return model_config, role_cfg


def omni_role_config() -> tuple[RealtimeModelConfig, RoleConfig]:
    """装 OMNI_ROLE_CONFIG 整包。"""
    return load_omni_role_spec("OMNI_ROLE_CONFIG")


def omni_realtime_model(config: RealtimeModelConfig | None = None):
    """按 RealtimeModelConfig 创建 DashScopeRealtimeModel（教程直连 Omni）。

    Args:
        config: 实时模型配置；None 时读 OMNI_ROLE_CONFIG.ModelConfig。

    Returns:
        agentscope.realtime.DashScopeRealtimeModel 实例。

    Raises:
        RuntimeError: 未安装 agentscope[realtime]。
        ValueError: provider 不是 dashscope，或 YAML/环境变量不合法。
    """
    DashScopeRealtimeModel = _import_dashscope_realtime()
    if config is None:
        section = load_agent_config("OMNI_ROLE_CONFIG") or {}
        if not isinstance(section, dict) or not section:
            raise ValueError("agent_config 缺少节 'OMNI_ROLE_CONFIG'")
        config = _build_realtime_model_config(section, config_key="OMNI_ROLE_CONFIG")
    if config.provider != "dashscope":
        raise ValueError(
            f"Omni 实时路径仅支持 provider=dashscope，收到: {config.provider!r}"
        )
    if config.base_url:
        credential = DashScopeCredential(api_key=config.api_key, base_url=config.base_url)
    else:
        credential = DashScopeCredential(api_key=config.api_key)
    return DashScopeRealtimeModel(
        model=config.model_name,
        credential=credential,
        parameters=DashScopeRealtimeModel.Parameters(voice=config.voice),
    )

# ── 现成命名目录（可选 config.yaml；缺失时用与 agent_config 对齐的内置默认）──

from collections.abc import Mapping
from typing import Any, ClassVar, Final

import yaml

_CONFIG_YAML: Final[Path] = Path(__file__).with_name("config.yaml")


@dataclass(frozen=True)
class TextModelReady:
    """文本聊天模型的现成连接参数。"""

    name: str
    provider: str
    model_name: str
    base_url: str
    api_key_env: str
    multimodal: bool = False

    def resolve_api_key(self, environ: Mapping[str, str] | None = None) -> str:
        if environ is not None:
            return (environ.get(self.api_key_env) or "").strip()
        return os.environ.get(self.api_key_env, "").strip()

    def connection_fields(
        self,
        *,
        environ: Mapping[str, str] | None = None,
        model_name: str | None = None,
        api_key: str | None = None,
    ) -> dict[str, str]:
        return {
            "provider": self.provider,
            "model_name": model_name or self.model_name,
            "base_url": self.base_url,
            "api_key": self.resolve_api_key(environ) if api_key is None else api_key,
        }

    def to_model_config(
        self,
        *,
        environ: Mapping[str, str] | None = None,
        model_name: str | None = None,
        api_key: str | None = None,
        stream: bool = True,
        vision: bool | None = None,
    ) -> ModelConfig:
        return ModelConfig(
            provider=self.provider,
            model_name=model_name or self.model_name,
            base_url=self.base_url,
            api_key=self.resolve_api_key(environ) if api_key is None else api_key,
            vision=self.multimodal if vision is None else bool(vision),
            stream=bool(stream),
        )

    def create_chat_model(
        self,
        *,
        stream: bool = True,
        vision: bool | None = None,
        environ: Mapping[str, str] | None = None,
        model_name: str | None = None,
        api_key: str | None = None,
    ):
        key = self.resolve_api_key(environ) if api_key is None else api_key
        if not str(key).strip():
            raise RuntimeError(f"缺少 {self.api_key_env}，无法创建聊天模型")
        return ChatModelFactory(
            self.to_model_config(
                api_key=key,
                model_name=model_name,
                stream=stream,
                vision=vision,
                environ=environ,
            ),
        ).create()


@dataclass(frozen=True)
class RealtimeModelReady:
    """实时语音模型的现成连接参数（仅 Omni）。"""

    name: str
    model: str
    api_key_env: str
    ws_url: str | None = None

    def resolve_api_key(self, environ: Mapping[str, str] | None = None) -> str:
        if environ is not None:
            return (environ.get(self.api_key_env) or "").strip()
        return os.environ.get(self.api_key_env, "").strip()

    def create_realtime_model(
        self,
        *,
        environ: Mapping[str, str] | None = None,
        api_key: str | None = None,
        parameters: Any = None,
        **parameter_kwargs: Any,
    ):
        if parameters is not None and parameter_kwargs:
            raise TypeError("create_realtime_model 不能同时传 parameters 与关键字参数")
        try:
            from agentscope.credential import DashScopeCredential
        except ImportError as exc:
            raise RuntimeError(
                '缺少 AgentScope 实时语音依赖，请执行：pip install "agentscope[realtime]"',
            ) from exc
        key = self.resolve_api_key(environ) if api_key is None else api_key
        if not str(key).strip():
            raise RuntimeError(f"缺少 {self.api_key_env}，无法创建实时语音模型")
        if bool(self.ws_url) or self.name == "livetranslate":
            raise RuntimeError(
                f"实时模型 {self.name!r}（livetranslate）已移除，请使用 omni",
            )
        credential = DashScopeCredential(api_key=key)
        try:
            from agentscope.realtime import DashScopeRealtimeModel

            params = parameters
            if params is None:
                params = (
                    DashScopeRealtimeModel.Parameters(**parameter_kwargs)
                    if parameter_kwargs
                    else DashScopeRealtimeModel.Parameters()
                )
            return DashScopeRealtimeModel(
                model=self.model,
                credential=credential,
                parameters=params,
            )
        except ValueError as exc:
            raise RuntimeError(
                f"实时语音模型或音色配置无效：{exc}。当前配置 {self.name!r}，模型 {self.model!r}。",
            ) from exc


@dataclass(frozen=True)
class EmbeddingModelReady:
    """嵌入模型的现成命名配置。"""

    name: str
    model: str
    dimensions: int
    api_key_env: str = "DASHSCOPE_API_KEY"


def _builtin_catalog() -> tuple[
    dict[str, TextModelReady],
    dict[str, RealtimeModelReady],
    dict[str, EmbeddingModelReady],
]:
    """与 agent_config.yaml / 计费别名对齐的内置目录（不依赖 config.yaml）。"""
    text = {
        "deepseek_flash": TextModelReady(
            name="deepseek_flash",
            provider="deepseek",
            model_name="deepseek-flash",
            base_url="https://api.deepseek.com/v1",
            api_key_env="DEEPSEEK_API_KEY",
            multimodal=True,
        ),
        "deepseek_pro": TextModelReady(
            name="deepseek_pro",
            provider="deepseek",
            model_name="deepseek-v4-pro",
            base_url="https://api.deepseek.com/v1",
            api_key_env="DEEPSEEK_API_KEY",
            multimodal=False,
        ),
    }
    realtime = {
        "omni": RealtimeModelReady(
            name="omni",
            model="qwen3.5-omni-plus-realtime",
            api_key_env="DASHSCOPE_API_KEY",
        ),
    }
    embedding = {
        "text_embedding_v4": EmbeddingModelReady(
            name="text_embedding_v4",
            model="text-embedding-v4",
            dimensions=1024,
            api_key_env="DASHSCOPE_API_KEY",
        ),
    }
    return text, realtime, embedding


def _load_catalog_from_yaml(path: Path) -> tuple[
    dict[str, TextModelReady],
    dict[str, RealtimeModelReady],
    dict[str, EmbeddingModelReady],
] | None:
    """若存在 config.yaml 则装载；失败或缺失返回 None。"""
    if not path.is_file():
        return None
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(raw, dict):
        return None
    text_models: dict[str, TextModelReady] = {}
    for name, row in (raw.get("text") or {}).items():
        if not isinstance(row, dict):
            continue
        text_models[str(name)] = TextModelReady(
            name=str(name),
            provider=str(row.get("provider") or "").strip(),
            model_name=str(row.get("model_name") or "").strip(),
            base_url=str(row.get("base_url") or "").strip(),
            api_key_env=str(row.get("api_key_env") or "").strip(),
            multimodal=bool(row.get("multimodal", False)),
        )
    realtime_models: dict[str, RealtimeModelReady] = {}
    for name, row in (raw.get("realtime") or {}).items():
        if not isinstance(row, dict):
            continue
        ws = row.get("ws_url")
        realtime_models[str(name)] = RealtimeModelReady(
            name=str(name),
            model=str(row.get("model") or "").strip(),
            api_key_env=str(row.get("api_key_env") or "DASHSCOPE_API_KEY").strip(),
            ws_url=str(ws).strip() if isinstance(ws, str) and ws.strip() else None,
        )
    embedding_models: dict[str, EmbeddingModelReady] = {}
    for name, row in (raw.get("embedding") or {}).items():
        if not isinstance(row, dict):
            continue
        dims = row.get("dimensions")
        if not isinstance(dims, int) or dims <= 0:
            continue
        embedding_models[str(name)] = EmbeddingModelReady(
            name=str(name),
            model=str(row.get("model") or "").strip(),
            dimensions=dims,
            api_key_env=str(row.get("api_key_env") or "DASHSCOPE_API_KEY").strip(),
        )
    if not text_models or not realtime_models:
        return None
    return text_models, realtime_models, embedding_models


_loaded = _load_catalog_from_yaml(_CONFIG_YAML)
if _loaded is None:
    TEXT_MODELS, REALTIME_MODELS, EMBEDDING_MODELS = _builtin_catalog()
else:
    TEXT_MODELS, REALTIME_MODELS, EMBEDDING_MODELS = _loaded

deepseek_flash: Final[TextModelReady] = TEXT_MODELS["deepseek_flash"]
deepseek_pro: Final[TextModelReady] = TEXT_MODELS["deepseek_pro"]
omni: Final[RealtimeModelReady] = REALTIME_MODELS["omni"]
text_embedding_v4: Final[EmbeddingModelReady] = EMBEDDING_MODELS["text_embedding_v4"]

DEFAULT_OMNI_MODEL: Final[str] = omni.model


def get_text(name: str) -> TextModelReady:
    try:
        return TEXT_MODELS[name]
    except KeyError as exc:
        raise KeyError(f"未知文本模型配置: {name!r}；可选：{' / '.join(TEXT_MODELS)}") from exc


def get_realtime(name: str) -> RealtimeModelReady:
    try:
        return REALTIME_MODELS[name]
    except KeyError as exc:
        raise KeyError(f"未知实时模型配置: {name!r}；可选：{' / '.join(REALTIME_MODELS)}") from exc


def get_embedding(name: str) -> EmbeddingModelReady:
    try:
        return EMBEDDING_MODELS[name]
    except KeyError as exc:
        raise KeyError(f"未知嵌入模型配置: {name!r}；可选：{' / '.join(EMBEDDING_MODELS)}") from exc


@dataclass(frozen=True)
class DeepSeekModelConfig:
    """DeepSeek 连接参数兼容层（计费用 FLASH / PRO 常量）。"""

    FLASH: ClassVar[str] = deepseek_flash.model_name
    PRO: ClassVar[str] = deepseek_pro.model_name
    MODELS: ClassVar[tuple[str, ...]] = (FLASH, PRO)

    provider: str = deepseek_flash.provider
    base_url: str = deepseek_flash.base_url
    model_name: str = FLASH
