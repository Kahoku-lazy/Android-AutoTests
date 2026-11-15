"""
文件名: ➡️ schema.py 🏁
路径: ➡️ engines/agents/models/schema.py 🏁
模块功能：➡️ 模型配置的形状与校验：三个校验类 + 中文报错 🏁
Python 调试：➡️ python -m engines.agents.models.schema 🏁
时间：➡️ 2026-11-11 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-11 🏁
类型: ➡️ 模型配置模块 🏁
简介说明：➡️
1. ModelConfigError: 配置不合法，消息带「文件:短名.字段」定位。
2. ChatModelSchema: 大语言模型参数校验（含能力推导 supports_image）。
3. RealtimeModelSchema: 实时语音与 TTS 共用的参数校验。
4. EmbeddingModelSchema: 向量模型参数校验。
5. validate_chat / validate_voice / validate_embedding / validate_model: 按类校验并返回参数对象。
🏁
关联模块：➡️
1. 无本地依赖：只依赖 pydantic，不 import 引擎内其它模块。
🏁
测试：➡️
1. tests/models/unit/test_models_public_surface.py: 包外不构造模型类、不 import 子模块
🏁
"""

from __future__ import annotations

from typing import Any, ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

__all__ = [
    "FAMILIES",
    "ModelConfigError",
    "ChatModelSchema",
    "RealtimeModelSchema",
    "EmbeddingModelSchema",
    "validate_chat",
    "validate_voice",
    "validate_embedding",
    "validate_model",
]

FAMILIES = ("chat", "realtime", "embedding", "tts")

# provider → 唯一密钥环境变量名。只存名字，不存密钥（密钥由 config 层解析）。
_API_KEY_ENV = {"deepseek": "DEEPSEEK_API_KEY", "dashscope": "DASHSCOPE_API_KEY"}


class ModelConfigError(ValueError):
    """
    模型配置不合法。

    消息面向改配置的人：带「文件:短名.字段」定位，能照着改。

    Attributes:
        无。
    """


# pydantic 的英文默认文案统一翻成中文，文案只有这一处。
_MESSAGES = {
    "extra_forbidden": "未知字段",
    "missing": "必填缺失",
    "string_too_short": "不能为空",
    "string_type": "期望字符串",
    "int_type": "期望整数",
    "int_parsing": "期望整数",
    "int_from_float": "期望整数",
    "greater_than_equal": "必须 ≥ {ge}",
    "greater_than": "必须 > {gt}",
    "literal_error": "只能取 {expected}",
    "tuple_type": "期望字符串列表",
}


def _describe(err: dict[str, Any]) -> str:
    """
    把一条 pydantic 错误翻成中文。

    Args:
        err: ValidationError.errors() 里的一项。

    Returns:
        中文说明；没有对应模板时退回 pydantic 原文（去掉 Value error 前缀）。
    """
    template = _MESSAGES.get(err["type"])
    if template is None:
        return str(err["msg"]).removeprefix("Value error, ")
    try:
        return template.format(**err.get("ctx", {}))
    except (KeyError, IndexError):
        return template


class _ModelSchemaBase(BaseModel):
    """
    三个校验类共用的四个字段与三条跨字段规则。

    只为一件事存在：不让同样四行字段在三个类里各抄一遍。

    Attributes:
        family: 模型类别；由条目自己标记（chat / realtime / embedding / tts）。
        provider: provider 名；大小写不敏感，归一成小写。
        model_name: 厂商正式模型名。
        api_key_env: 密钥环境变量名；必须与 provider 对应。
        api_key: config 注入的密钥对象；本包只要求它提供 `reveal()`。
        base_url: 基础地址；空串表示用 provider 默认。

    Raises:
        ValidationError: 字段类型、枚举取值或跨字段规则不通过。
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    FAMILY: ClassVar[str] = ""

    family: Literal["chat", "realtime", "embedding", "tts"]
    provider: Literal["deepseek", "dashscope"]
    model_name: str = Field(min_length=1)
    api_key_env: Literal["DEEPSEEK_API_KEY", "DASHSCOPE_API_KEY"]
    api_key: Any
    base_url: str = ""

    @field_validator("provider", mode="before")
    @classmethod
    def _normalize_provider(cls, value: object) -> object:
        """把 DeepSeek / DashScope 归一小写，再交给 Literal 判定。

        Args:
            value: YAML 里的原始值。

        Returns:
            小写后的值；不是字符串时原样返回，交给 Literal 报错。
        """
        return value.strip().lower() if isinstance(value, str) else value

    @model_validator(mode="after")
    def _check_api_key_env(self) -> _ModelSchemaBase:
        """校验 api_key_env 与 provider 对应。

        Returns:
            校验通过的自身。

        Raises:
            ValueError: 两者不匹配（如 provider=deepseek 却写 DASHSCOPE_API_KEY）。
        """
        expected = _API_KEY_ENV[self.provider]
        if self.api_key_env != expected:
            raise ValueError(f"api_key_env 必须是 {expected}（provider={self.provider}）")
        return self

    @model_validator(mode="after")
    def _check_family(self) -> _ModelSchemaBase:
        """确认 family 与本类负责的族一致（语音类两个族共用，跳过）。

        Returns:
            校验通过的自身。

        Raises:
            ValueError: 本类负责的族与条目里的 family 不一致。
        """
        if self.FAMILY and self.family != self.FAMILY:
            raise ValueError(f"family 必须是 {self.FAMILY}，收到 {self.family!r}")
        return self

    @field_validator("api_key")
    @classmethod
    def _check_api_key(cls, value: object) -> object:
        """确认密钥对象能 reveal。

        本包不关心密钥怎么加密，只要求它提供 `reveal()`——加解密都在 config 侧。

        Args:
            value: config 注入的密钥对象。

        Returns:
            原样的密钥对象。

        Raises:
            ValueError: 对象没有可调用的 `reveal()`。
        """
        if not callable(getattr(value, "reveal", None)):
            raise ValueError("api_key 必须是 config 注入的密钥对象（需提供 reveal()）")
        return value


class ChatModelSchema(_ModelSchemaBase):
    """
    大语言模型 参数校验。

    Attributes:
        FAMILY: 本类负责的族标识；与条目里的 family 对齐。
        input_types: 接受的输入 MIME 类型；含 image/* 即走视觉档。
        output_types: 产出的 MIME 类型。
        context_size: 上下文窗口；0 表示用 provider 默认。
        output_size: 最大输出 token；0 表示不限制。
        max_retries: API 级重试次数。
        formatter: 格式化器名，只能取 chat / multi_agent。
        parameters: 传给框架 Parameters 的默认值。

    Raises:
        ValidationError: 字段或跨字段规则不通过。
    """

    FAMILY: ClassVar[str] = "chat"

    input_types: tuple[str, ...] = ("text/plain",)
    output_types: tuple[str, ...] = ("text/plain",)
    context_size: int = Field(default=0, ge=0, strict=True)
    output_size: int = Field(default=0, ge=0, strict=True)
    max_retries: int = Field(default=1, ge=0, strict=True)
    formatter: Literal["chat", "multi_agent"] = "chat"
    parameters: dict[str, Any] = Field(default_factory=dict)

    @property
    def supports_image(self) -> bool:
        """是否接受图片输入。

        Returns:
            任一输入类型属于 image/* 时为 True。
        """
        return any(item.split("/", 1)[0] == "image" for item in self.input_types)


class RealtimeModelSchema(_ModelSchemaBase):
    """
    实时语音与 TTS 音色模型共用的参数校验。

    一个类服务两个创建入口：create_realtime（实时语音）与 create_tts（语音合成）。

    Attributes:
        voice: 音色；空串表示用框架默认。

    Raises:
        ValidationError: 字段或跨字段规则不通过。
    """

    voice: str = ""


class EmbeddingModelSchema(_ModelSchemaBase):
    """
    向量模型 参数校验。

    Attributes:
        FAMILY: 本类负责的族标识；与条目里的 family 对齐。
        dimensions: 向量维度；必填且必须为正（缺了请求会用错维度）。

    Raises:
        ValidationError: 字段或跨字段规则不通过。
    """

    FAMILY: ClassVar[str] = "embedding"

    dimensions: int = Field(gt=0, strict=True)


def _validate(cls: type[BaseModel], raw: object, *, source: str) -> Any:
    """
    跑一次校验，把 pydantic 错误整理成一条可读消息。

    Args:
        cls: 目标校验类。
        raw: YAML 里的一条模型条目。
        source: 报错定位前缀，如 models.yaml:deepseek_flash。

    Returns:
        已校验的参数对象。

    Raises:
        ModelConfigError: 条目不是映射表，或结构 / 跨字段规则不通过。
    """
    if not isinstance(raw, dict):
        raise ModelConfigError(f"{source}: 必须是映射表，收到 {type(raw).__name__}")
    try:
        return cls.model_validate(raw)
    except ValidationError as exc:
        problems: list[str] = []
        for err in exc.errors():
            parts = [str(part) for part in err["loc"]]
            where = f"{source}.{'.'.join(parts)}" if parts else source
            problems.append(f"{where}: {_describe(err)}")
        raise ModelConfigError("；".join(problems)) from exc


def validate_chat(raw: object, *, source: str = "models.yaml") -> ChatModelSchema:
    """
    校验一条聊天模型配置。

    Args:
        raw: YAML 里的一条模型条目。
        source: 报错定位前缀。

    Returns:
        已校验的聊天模型参数。

    Raises:
        ModelConfigError: 校验不通过。
    """
    return _validate(ChatModelSchema, raw, source=source)


def validate_voice(raw: object, *, source: str = "models.yaml") -> RealtimeModelSchema:
    """
    校验一条语音模型配置（实时语音与 TTS 共用）。

    Args:
        raw: YAML 里的一条模型条目。
        source: 报错定位前缀。

    Returns:
        已校验的语音模型参数。

    Raises:
        ModelConfigError: 校验不通过。
    """
    return _validate(RealtimeModelSchema, raw, source=source)


def validate_embedding(raw: object, *, source: str = "models.yaml") -> EmbeddingModelSchema:
    """
    校验一条向量模型配置。

    Args:
        raw: YAML 里的一条模型条目。
        source: 报错定位前缀。

    Returns:
        已校验的向量模型参数。

    Raises:
        ModelConfigError: 校验不通过。
    """
    return _validate(EmbeddingModelSchema, raw, source=source)


def validate_model(family: str, raw: object, *, source: str = "models.yaml") -> Any:
    """
    按族选择校验方法：需要配哪类模型就调这里。

    Args:
        family: chat / realtime / tts / embedding。
        raw: YAML 里的一条模型条目。
        source: 报错定位前缀。

    Returns:
        已校验的参数对象（三个类之一）。

    Raises:
        ModelConfigError: 族名未知，或校验不通过。
    """
    validators = {
        "chat": validate_chat,
        "realtime": validate_voice,
        "tts": validate_voice,
        "embedding": validate_embedding,
    }
    validator = validators.get(family)
    if validator is None:
        raise ModelConfigError(
            f"{source}: 未知的族 {family!r}；可选：{', '.join(FAMILIES)}",
        )
    return validator(raw, source=source)
