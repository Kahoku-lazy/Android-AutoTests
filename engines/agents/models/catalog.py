"""
文件名: ➡️ catalog.py 🏁
路径: ➡️ engines/agents/models/catalog.py 🏁
模块功能：➡️ 现成命名模型目录：内置默认加可选 YAML 覆盖，按短名取模型与图片能力 🏁
Python 调试：➡️ python -m engines.agents.models.catalog 🏁
时间：➡️ 2026-11-03 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-03 🏁
类型: ➡️ 模型配置模块 🏁
简介说明：➡️
1. TextModelReady / RealtimeModelReady / EmbeddingModelReady: 目录项，保存连接参数并提供建模型便捷方法
2. TEXT_MODELS / REALTIME_MODELS / EMBEDDING_MODELS + get_text / get_realtime / get_embedding: 按短名取目录项
3. _builtin_catalog / _load_catalog_from_yaml: 内置默认；config/data/config.yaml 存在时以文件覆盖
4. DeepSeekModelConfig: DeepSeek 短名兼容层（计费与角色共用 FLASH / PRO）
5. model_supports_image: 按 provider 与模型名判断是否支持图片输入
🏁
关联模块：➡️
1. engines.agents.models.types: 导入 ModelConfig，目录项转聊天连接参数
2. engines.agents.models.chat_model: 延迟导入 ChatModelFactory，目录项可直接建聊天模型
3. engines.agents.models.realtime_model: 延迟导入 build_realtime_model，目录项可直接建实时模型
🏁
测试：➡️
1. tests/engines/agents/test_billing_eight_decimals.py: 计费档名取自本目录的 DeepSeekModelConfig
2. tests/graybox/unit/test_rag_store.py: 嵌入模型默认值经 get_embedding 取
🏁
"""

from __future__ import annotations

import os

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar, Final

import yaml

from .types import ModelConfig

__all__ = [
    "DEEPSEEK_MODELS",
    "DeepSeekModelConfig",
    "EMBEDDING_MODELS",
    "EmbeddingModelReady",
    "REALTIME_MODELS",
    "RealtimeModelReady",
    "TEXT_MODELS",
    "TextModelReady",
    "deepseek_flash",
    "deepseek_pro",
    "get_embedding",
    "get_realtime",
    "get_text",
    "model_supports_image",
    "omni",
    "text_embedding_v4",
]

# 目录覆盖文件：模型数据归 config/data，本包内不放数据文件。
_CONFIG_YAML: Final[Path] = Path(__file__).resolve().parents[1] / "config" / "data" / "config.yaml"


@dataclass(frozen=True)
class TextModelReady:
    """
    文本聊天模型的现成连接参数。

    Attributes:
        name: 目录短名，如 deepseek_flash。
        provider: 模型提供商。
        model_name: 正式模型名。
        base_url: 基础 URL。
        api_key_env: 取密钥的环境变量名。
        multimodal: 是否支持图片输入。

    Raises:
        FrozenInstanceError: 目录项不可变。
    """

    name: str
    provider: str
    model_name: str
    base_url: str
    api_key_env: str
    multimodal: bool = False

    def resolve_api_key(self, environ: Mapping[str, str] | None = None) -> str:
        """从环境（或给定 mapping）解析 API Key。

        Args:
            environ: 测试注入的环境映射；None 读进程环境变量。

        Returns:
            去掉首尾空白的密钥；未设置时为空串。
        """
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
        """组装连接字段（model_name / api_key / base_url 等）。

        Args:
            environ: 测试注入的环境映射。
            model_name: 覆盖目录项里的模型名。
            api_key: 覆盖环境变量解析出的密钥。

        Returns:
            provider / model_name / base_url / api_key 四个字段。
        """
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
        """转为 ModelConfig。

        Args:
            environ: 测试注入的环境映射。
            model_name: 覆盖目录项里的模型名。
            api_key: 覆盖环境变量解析出的密钥。
            stream: 是否流式输出。
            vision: 是否多模态；None 用目录项的 multimodal。

        Returns:
            可直接交给 ChatModelFactory 的连接参数。
        """
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
        """创建对应的 Chat 模型实例。

        Args:
            stream: 是否流式输出。
            vision: 是否按多模态建模型；None 用目录项的 multimodal。
            environ: 测试注入的环境映射。
            model_name: 覆盖目录项里的模型名。
            api_key: 覆盖环境变量解析出的密钥。

        Returns:
            对应的聊天模型实例。

        Raises:
            RuntimeError: 环境里取不到该目录项要求的 API Key。
        """
        from .chat_model import ChatModelFactory

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
    """
    实时语音模型的现成连接参数（仅 Omni）。

    Attributes:
        name: 目录短名，如 omni。
        model: 正式模型名。
        api_key_env: 取密钥的环境变量名。
        ws_url: 旧版直连地址；非空即视为已移除的模型。

    Raises:
        FrozenInstanceError: 目录项不可变。
    """

    name: str
    model: str
    api_key_env: str
    ws_url: str | None = None

    def resolve_api_key(self, environ: Mapping[str, str] | None = None) -> str:
        """从环境（或给定 mapping）解析 API Key。

        Args:
            environ: 测试注入的环境映射；None 读进程环境变量。

        Returns:
            去掉首尾空白的密钥；未设置时为空串。
        """
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
        """创建 Omni/实时语音模型实例。

        Args:
            environ: 测试注入的环境映射。
            api_key: 覆盖环境变量解析出的密钥。
            parameters: 已构造好的框架 Parameters；与关键字参数互斥。
            parameter_kwargs: 直接传给框架 Parameters 的关键字（如 voice）。

        Returns:
            实时语音模型实例。

        Raises:
            TypeError: `parameters` 与关键字参数同时传入。
            RuntimeError: 缺少该目录项要求的 API Key、模型已移除，或模型/音色不受支持。
        """
        from .realtime_model import build_realtime_model

        if parameters is not None and parameter_kwargs:
            raise TypeError("create_realtime_model 不能同时传 parameters 与关键字参数")
        key = self.resolve_api_key(environ) if api_key is None else api_key
        if not str(key).strip():
            raise RuntimeError(f"缺少 {self.api_key_env}，无法创建实时语音模型")
        if bool(self.ws_url) or self.name == "livetranslate":
            raise RuntimeError(
                f"实时模型 {self.name!r}（livetranslate）已移除，请使用 omni",
            )
        try:
            return build_realtime_model(
                api_key=key,
                model_name=self.model,
                parameters=parameters,
                **parameter_kwargs,
            )
        except ValueError as exc:
            raise RuntimeError(
                f"实时语音模型或音色配置无效：{exc}。当前配置 {self.name!r}，模型 {self.model!r}。",
            ) from exc


@dataclass(frozen=True)
class EmbeddingModelReady:
    """
    嵌入模型的现成命名配置。

    Attributes:
        name: 目录短名，如 text_embedding_v4。
        model: 正式模型名。
        dimensions: 向量维度。
        api_key_env: 取密钥的环境变量名。

    Raises:
        FrozenInstanceError: 目录项不可变。
    """

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


def _load_catalog_from_yaml(
    path: Path,
) -> (
    tuple[
        dict[str, TextModelReady],
        dict[str, RealtimeModelReady],
        dict[str, EmbeddingModelReady],
    ]
    | None
):
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
    """按名称取出已登记的文本模型就绪配置。

    Args:
        name: 目录短名，如 deepseek_flash。

    Returns:
        对应的文本模型目录项。

    Raises:
        KeyError: 名称未登记，报错会列出可选短名。
    """
    try:
        return TEXT_MODELS[name]
    except KeyError as exc:
        raise KeyError(f"未知文本模型配置: {name!r}；可选：{' / '.join(TEXT_MODELS)}") from exc


def get_realtime(name: str) -> RealtimeModelReady:
    """按名称取出已登记的实时模型就绪配置。

    Args:
        name: 目录短名，如 omni。

    Returns:
        对应的实时模型目录项。

    Raises:
        KeyError: 名称未登记，报错会列出可选短名。
    """
    try:
        return REALTIME_MODELS[name]
    except KeyError as exc:
        raise KeyError(f"未知实时模型配置: {name!r}；可选：{' / '.join(REALTIME_MODELS)}") from exc


def get_embedding(name: str) -> EmbeddingModelReady:
    """按名称取出已登记的 Embedding 模型就绪配置。

    Args:
        name: 目录短名，如 text_embedding_v4。

    Returns:
        对应的嵌入模型目录项。

    Raises:
        KeyError: 名称未登记，报错会列出可选短名。
    """
    try:
        return EMBEDDING_MODELS[name]
    except KeyError as exc:
        raise KeyError(f"未知嵌入模型配置: {name!r}；可选：{' / '.join(EMBEDDING_MODELS)}") from exc


def _deepseek_models() -> dict[str, bool]:
    """DeepSeek 正式模型名 → 是否支持图片输入。"""
    return {
        cfg.model_name: cfg.multimodal for cfg in TEXT_MODELS.values() if cfg.provider == "deepseek"
    }


class _DeepSeekModelsProxy(dict):
    """兼容旧 DEEPSEEK_MODELS[model] 访问的只读字典代理。"""

    def __getitem__(self, key):
        """按键取图片支持能力。

        Args:
            key: 正式模型名。

        Returns:
            是否支持图片输入。
        """
        return _deepseek_models()[key]

    def __contains__(self, key):
        """模型名是否已登记。

        Args:
            key: 正式模型名。

        Returns:
            已登记返回 True。
        """
        return key in _deepseek_models()

    def get(self, key, default=None):
        """按键取图片支持能力，未登记时返回默认值。

        Args:
            key: 正式模型名。
            default: 未登记时的返回值。

        Returns:
            是否支持图片输入，或默认值。
        """
        return _deepseek_models().get(key, default)

    def keys(self):
        """列出已登记的模型名。

        Returns:
            模型名视图。
        """
        return _deepseek_models().keys()

    def values(self):
        """列出图片支持能力。

        Returns:
            能力值视图。
        """
        return _deepseek_models().values()

    def items(self):
        """列出「模型名 → 图片支持能力」。

        Returns:
            键值对视图。
        """
        return _deepseek_models().items()

    def __iter__(self):
        """遍历已登记的模型名。

        Returns:
            模型名迭代器。
        """
        return iter(_deepseek_models())

    def __len__(self):
        """已登记模型的数量。

        Returns:
            条目数。
        """
        return len(_deepseek_models())


DEEPSEEK_MODELS = _DeepSeekModelsProxy()
"""DeepSeek 模型名到图片支持能力的映射（兼容旧字典访问）。"""


def model_supports_image(provider: str, model_name: str) -> bool | None:
    """按 provider + 模型名是否支持图片输入。

    Args:
        provider: 模型提供商（只认 deepseek）。
        model_name: 模型名（只认 `DEEPSEEK_MODELS` 已登记的名字）。

    Returns:
        True / False 表示已登记模型的图片输入能力；非 deepseek 或未登记的模型名返回 None。
    """
    if str(provider or "").strip().lower() != "deepseek":
        return None
    name = str(model_name or "").strip().lower()
    return DEEPSEEK_MODELS.get(name)


@dataclass(frozen=True)
class DeepSeekModelConfig:
    """
    DeepSeek 连接参数兼容层（计费用 FLASH / PRO 常量）。

    Attributes:
        FLASH: Flash 档模型名（默认档）。
        PRO: Pro 档模型名。
        MODELS: 已登记的两个档名。
        provider: 模型提供商。
        base_url: 基础 URL。
        model_name: 默认模型名（FLASH）。
    """

    FLASH: ClassVar[str] = deepseek_flash.model_name
    PRO: ClassVar[str] = deepseek_pro.model_name
    MODELS: ClassVar[tuple[str, ...]] = (FLASH, PRO)

    provider: str = deepseek_flash.provider
    base_url: str = deepseek_flash.base_url
    model_name: str = FLASH
