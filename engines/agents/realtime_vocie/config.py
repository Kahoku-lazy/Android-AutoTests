"""
python -m 调试路径: engines.agents.realtime_vocie.config

本模块的业务功能如下：
1. RealtimeVoiceConfig: 保存一次实时语音会话所需的模型与提示词配置。
2. load_config(): 从根 `.env` / 环境变量读取并校验配置。
3. build_runtime_status(): 生成不含密钥的就绪状态字段。
4. create_realtime_model(): 按配置构造 AgentScope 的 DashScope 实时语音模型。
5. select_mode(): 按前端选择的路线生成会话配置（omni / livetranslate / pipeline）。

本模块只读 `DASHSCOPE_API_KEY` 与 `KNOWLEDGE_ASSISTANT_*`，不读取
`temps/realtime_voice_demo/.env`，也不依赖后端 App 或本地日志目录。
"""

from __future__ import annotations

import importlib.util
import os

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from typing import Final

from engines.agents.config.models import DeepSeekModelConfig

from .knowledge import build_system_prompt
from .livetranslate import LIVETRANSLATE_MODEL

LIVETRANSLATE_MODE: Final[str] = "livetranslate"
OMNI_MODE: Final[str] = "omni"
PIPELINE_MODE: Final[str] = "pipeline"
SUPPORTED_MODES: Final[tuple[str, ...]] = (
    OMNI_MODE,
    LIVETRANSLATE_MODE,
    PIPELINE_MODE,
)
DEFAULT_OMNI_MODEL: Final[str] = "qwen3.5-omni-plus-realtime"
DEFAULT_MODE: Final[str] = OMNI_MODE
DEFAULT_MODEL: Final[str] = DEFAULT_OMNI_MODEL
DEFAULT_VOICE: Final[str] = "Tina"
DEFAULT_TRANSLATION_LANGUAGE: Final[str] = "zh"
DEFAULT_PIPELINE_LLM_MODEL: Final[str] = DeepSeekModelConfig.FLASH
DEFAULT_PIPELINE_TTS_PROVIDER: Final[str] = "sambert"
DEFAULT_PIPELINE_TTS_MODEL: Final[str] = "sambert-zhichu-v1"
DEFAULT_PIPELINE_TTS_VOICE: Final[str] = "知厨"
DEFAULT_QWEN_TTS_MODEL: Final[str] = "qwen3-tts-flash"
DEFAULT_QWEN_TTS_VOICE: Final[str] = "Cherry"
SUPPORTED_TTS_PROVIDERS: Final[tuple[str, ...]] = ("sambert", "qwen")
DEFAULT_PIPELINE_ENGINE: Final[str] = "agent"
SUPPORTED_PIPELINE_ENGINES: Final[tuple[str, ...]] = ("agent", "legacy")
DEFAULT_TURN_DETECTION: Final[str] = "server_vad"
DEFAULT_AGENT_NAME: Final[str] = "知识库助手"
SUPPORTED_TURN_DETECTIONS: Final[tuple[str, ...]] = ("server_vad", "semantic_vad")


@dataclass(frozen=True)
class RealtimeVoiceConfig:
    """
    一次实时语音会话的模型与提示词配置。

    Attributes:
        api_key: DashScope API Key；repr 中隐藏，避免误打日志。
        model: 实时语音模型名。
        voice: 音色名。
        turn_detection: 服务端回合检测方式。
        agent_name: 助手名称，出现在提示词与转写事件里。
        system_prompt: 系统提示词。
        vad_threshold: 服务端 VAD 的语音概率阈值，越低越容易触发。
        vad_silence_ms: 服务端 VAD 判定说完所需的静音毫秒数。
        mode: 调用方式：`omni`（直连问答）、`livetranslate`（实时翻译）
            或 `pipeline`（ASR + DeepSeek + TTS）。
        translation_language: 实时翻译模式的目标语种代码。
        pipeline_llm_model: Pipeline 路线的 DeepSeek 模型名。
        pipeline_tts_provider: Pipeline 路线的 TTS 厂商（sambert / qwen）。
        pipeline_tts_model: Pipeline 路线的 TTS 模型名。
        pipeline_tts_voice: Pipeline 路线的 TTS 音色展示名。
        pipeline_engine: Pipeline 回答链路：`agent`（Agent + 中间件）或 `legacy`（直连模型 + 单独合成）。
    """

    api_key: str = field(repr=False)
    model: str
    voice: str
    turn_detection: str
    agent_name: str
    system_prompt: str
    vad_threshold: float = 0.35
    vad_silence_ms: int = 700
    mode: str = DEFAULT_MODE
    translation_language: str = DEFAULT_TRANSLATION_LANGUAGE
    pipeline_llm_model: str = DEFAULT_PIPELINE_LLM_MODEL
    pipeline_tts_provider: str = DEFAULT_PIPELINE_TTS_PROVIDER
    pipeline_tts_model: str = DEFAULT_PIPELINE_TTS_MODEL
    pipeline_tts_voice: str = DEFAULT_PIPELINE_TTS_VOICE
    pipeline_engine: str = DEFAULT_PIPELINE_ENGINE


def _read(environ: Mapping[str, str] | None, name: str, default: str = "") -> str:
    """
    读取一个配置项：显式传入的映射优先，否则读进程环境变量。

    Args:
        environ: 测试注入的配置映射；None 表示读 `os.environ`。
        name: 配置项名。
        default: 未配置时的默认值。

    Returns:
        去掉首尾空白后的配置值；空值也返回空字符串。
    """
    value = environ.get(name) if environ is not None else os.environ.get(name)
    return (value or default).strip()


def _parse_bool(environ: Mapping[str, str] | None, name: str, default: bool) -> bool:
    """
    解析布尔配置，接受 1/true/yes/on 与 0/false/no/off。

    Args:
        environ: 测试注入的配置映射。
        name: 配置项名。
        default: 未配置时的默认值。

    Returns:
        解析后的布尔值。

    Raises:
        RuntimeError: 配置值不在允许集合内。
    """
    raw = _read(environ, name)
    if not raw:
        return default
    normalized = raw.lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise RuntimeError(f"{name} 必须是 true/false 之一，当前为 {raw!r}")


def _parse_float(
    environ: Mapping[str, str] | None,
    name: str,
    default: float,
    minimum: float,
    maximum: float,
) -> float:
    """解析区间内的浮点配置。"""
    raw = _read(environ, name)
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} 必须是数字，当前为 {raw!r}") from exc
    if not minimum <= value <= maximum:
        raise RuntimeError(f"{name} 必须在 {minimum} 到 {maximum} 之间，当前为 {value}")
    return value


def _parse_int(
    environ: Mapping[str, str] | None,
    name: str,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    """解析区间内的整数配置。"""
    raw = _read(environ, name)
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} 必须是整数，当前为 {raw!r}") from exc
    if not minimum <= value <= maximum:
        raise RuntimeError(f"{name} 必须在 {minimum} 到 {maximum} 之间，当前为 {value}")
    return value


def _resolve_mode_and_model(environ: Mapping[str, str] | None) -> tuple[str, str]:
    """
    解析调用方式与模型名，并校验二者匹配。

    Args:
        environ: 测试注入的配置映射。

    Returns:
        `(mode, model)`；mode 为 livetranslate 或 omni。

    Raises:
        RuntimeError: mode 未知，或 mode 与模型名不匹配。
    """
    mode_raw = _read(environ, "KNOWLEDGE_ASSISTANT_REALTIME_MODE").lower()
    model_raw = _read(environ, "KNOWLEDGE_ASSISTANT_MODEL")

    if mode_raw:
        if mode_raw not in SUPPORTED_MODES:
            choices = " / ".join(SUPPORTED_MODES)
            raise RuntimeError(
                f"KNOWLEDGE_ASSISTANT_REALTIME_MODE 只支持 {choices}，当前为 {mode_raw!r}",
            )
        mode = mode_raw
    elif "livetranslate" in model_raw.lower():
        # 只配置实时翻译模型名时自动走翻译适配器。
        mode = LIVETRANSLATE_MODE
    else:
        mode = OMNI_MODE

    if not model_raw:
        model_raw = DEFAULT_OMNI_MODEL if mode == OMNI_MODE else LIVETRANSLATE_MODEL

    if mode in (LIVETRANSLATE_MODE, PIPELINE_MODE) and "livetranslate" not in model_raw:
        raise RuntimeError(
            f"KNOWLEDGE_ASSISTANT_REALTIME_MODE={mode} 时，"
            f"ASR 必须是实时翻译模型，当前为 {model_raw!r}",
        )
    if mode == OMNI_MODE and "livetranslate" in model_raw:
        raise RuntimeError(
            f"KNOWLEDGE_ASSISTANT_REALTIME_MODE=omni 时，不能使用实时翻译模型 {model_raw!r}",
        )
    return mode, model_raw


def dependencies_available() -> bool:
    """判断实时语音依赖是否已安装，供状态接口使用。"""
    try:
        return (
            importlib.util.find_spec("agentscope") is not None
            and importlib.util.find_spec("agentscope.realtime") is not None
        )
    except Exception:
        # 找出依赖元数据时的异常（损坏的安装、缺 transitive 包）等价于不可用；
        # 状态接口只回报未就绪，不把异常抛给前端。
        return False


def load_config(environ: Mapping[str, str] | None = None) -> RealtimeVoiceConfig:
    """
    读取并校验一次实时语音会话的配置。

    Args:
        environ: 测试注入的配置映射；None 表示读 `os.environ`。

    Returns:
        校验完成的配置。

    Raises:
        RuntimeError: 功能被关闭、缺少 API Key 或配置值非法。
    """
    if not _parse_bool(environ, "KNOWLEDGE_ASSISTANT_ENABLED", True):
        raise RuntimeError("知识库助手已关闭（KNOWLEDGE_ASSISTANT_ENABLED=false）")

    api_key = _read(environ, "DASHSCOPE_API_KEY")
    if not api_key:
        raise RuntimeError("缺少 DASHSCOPE_API_KEY，无法连接实时语音模型")

    mode, model = _resolve_mode_and_model(environ)
    voice = _read(environ, "KNOWLEDGE_ASSISTANT_VOICE", DEFAULT_VOICE) or DEFAULT_VOICE
    translation_language = (
        _read(
            environ,
            "KNOWLEDGE_ASSISTANT_TRANSLATION_LANGUAGE",
            DEFAULT_TRANSLATION_LANGUAGE,
        )
        or DEFAULT_TRANSLATION_LANGUAGE
    )
    turn_detection = (
        _read(environ, "KNOWLEDGE_ASSISTANT_TURN_DETECTION", DEFAULT_TURN_DETECTION)
        or DEFAULT_TURN_DETECTION
    )
    if turn_detection not in SUPPORTED_TURN_DETECTIONS:
        choices = " / ".join(SUPPORTED_TURN_DETECTIONS)
        raise RuntimeError(
            f"KNOWLEDGE_ASSISTANT_TURN_DETECTION 只支持 {choices}，当前为 {turn_detection!r}",
        )

    agent_name = _read(environ, "KNOWLEDGE_ASSISTANT_AGENT_NAME", DEFAULT_AGENT_NAME)
    system_prompt = _read(environ, "KNOWLEDGE_ASSISTANT_SYSTEM_PROMPT") or build_system_prompt()
    pipeline_llm_model = (
        _read(
            environ,
            "KNOWLEDGE_ASSISTANT_PIPELINE_LLM_MODEL",
            DEFAULT_PIPELINE_LLM_MODEL,
        )
        or DEFAULT_PIPELINE_LLM_MODEL
    )
    pipeline_tts_provider = (
        _read(
            environ,
            "KNOWLEDGE_ASSISTANT_PIPELINE_TTS_PROVIDER",
            DEFAULT_PIPELINE_TTS_PROVIDER,
        ).lower()
        or DEFAULT_PIPELINE_TTS_PROVIDER
    )
    if pipeline_tts_provider not in SUPPORTED_TTS_PROVIDERS:
        choices = " / ".join(SUPPORTED_TTS_PROVIDERS)
        raise RuntimeError(
            "KNOWLEDGE_ASSISTANT_PIPELINE_TTS_PROVIDER 只支持 "
            f"{choices}，当前为 {pipeline_tts_provider!r}",
        )
    tts_default_model = (
        DEFAULT_QWEN_TTS_MODEL if pipeline_tts_provider == "qwen" else DEFAULT_PIPELINE_TTS_MODEL
    )
    tts_default_voice = (
        DEFAULT_QWEN_TTS_VOICE if pipeline_tts_provider == "qwen" else DEFAULT_PIPELINE_TTS_VOICE
    )
    pipeline_tts_model = (
        _read(
            environ,
            "KNOWLEDGE_ASSISTANT_PIPELINE_TTS_MODEL",
            tts_default_model,
        )
        or tts_default_model
    )
    pipeline_tts_voice = (
        _read(
            environ,
            "KNOWLEDGE_ASSISTANT_PIPELINE_TTS_VOICE",
            tts_default_voice,
        )
        or tts_default_voice
    )
    if pipeline_tts_provider == "sambert" and "sambert" not in pipeline_tts_model:
        raise RuntimeError(
            "KNOWLEDGE_ASSISTANT_PIPELINE_TTS_PROVIDER=sambert 时，"
            f"TTS 模型必须是 Sambert，当前为 {pipeline_tts_model!r}",
        )
    if pipeline_tts_provider == "qwen" and "tts" not in pipeline_tts_model:
        raise RuntimeError(
            "KNOWLEDGE_ASSISTANT_PIPELINE_TTS_PROVIDER=qwen 时，"
            f"TTS 模型必须是 Qwen-TTS，当前为 {pipeline_tts_model!r}",
        )
    if mode == PIPELINE_MODE:
        # Pipeline 的 ready/状态展示的是 TTS 音色，不是 ASR 音色。
        voice = pipeline_tts_voice

    pipeline_engine = (
        _read(
            environ,
            "KNOWLEDGE_ASSISTANT_PIPELINE_ENGINE",
            DEFAULT_PIPELINE_ENGINE,
        ).strip()
        or DEFAULT_PIPELINE_ENGINE
    ).lower()
    if pipeline_engine not in SUPPORTED_PIPELINE_ENGINES:
        choices = " / ".join(SUPPORTED_PIPELINE_ENGINES)
        raise RuntimeError(
            f"KNOWLEDGE_ASSISTANT_PIPELINE_ENGINE 只支持 {choices}，当前为 {pipeline_engine!r}",
        )

    return RealtimeVoiceConfig(
        api_key=api_key,
        model=model,
        voice=voice,
        turn_detection=turn_detection,
        agent_name=agent_name or DEFAULT_AGENT_NAME,
        system_prompt=system_prompt,
        vad_threshold=_parse_float(
            environ,
            "KNOWLEDGE_ASSISTANT_VAD_THRESHOLD",
            0.35,
            0.0,
            1.0,
        ),
        vad_silence_ms=_parse_int(
            environ,
            "KNOWLEDGE_ASSISTANT_VAD_SILENCE_MS",
            700,
            200,
            3000,
        ),
        mode=mode,
        translation_language=translation_language,
        pipeline_llm_model=pipeline_llm_model,
        pipeline_tts_provider=pipeline_tts_provider,
        pipeline_tts_model=pipeline_tts_model,
        pipeline_tts_voice=pipeline_tts_voice,
        pipeline_engine=pipeline_engine,
    )


def select_mode(config: RealtimeVoiceConfig, mode: str) -> RealtimeVoiceConfig:
    """
    按前端选择的路线生成本次连接的配置副本。

    Args:
        config: 基础配置。
        mode: `omni` / `livetranslate` / `pipeline`。

    Returns:
        替换了 mode、模型与音色的新配置；未变化时返回原对象。

    Raises:
        ValueError: mode 不在支持集合内。
    """
    if mode not in SUPPORTED_MODES:
        choices = " / ".join(SUPPORTED_MODES)
        raise ValueError(f"不支持的语音路线: {mode!r}；可选：{choices}")
    if mode == config.mode:
        return config
    if mode == OMNI_MODE:
        return replace(config, mode=mode, model=DEFAULT_OMNI_MODEL, voice=DEFAULT_VOICE)
    if mode == LIVETRANSLATE_MODE:
        return replace(config, mode=mode, model=LIVETRANSLATE_MODEL, voice=DEFAULT_VOICE)
    return replace(
        config,
        mode=mode,
        model=LIVETRANSLATE_MODEL,
        voice=config.pipeline_tts_voice,
    )


def build_runtime_status(environ: Mapping[str, str] | None = None) -> dict:
    """
    生成状态接口的模型/依赖字段，不包含密钥与日志路径。

    Args:
        environ: 测试注入的配置映射；None 表示读 `os.environ`。

    Returns:
        含 enabled / ready / reason / mode / model / voice / agent_name /
        translation_language 的字典。
    """
    try:
        mode, model = _resolve_mode_and_model(environ)
    except RuntimeError:
        # 冲突/非法配置交给下面的 load_config 生成可读原因；这里只保留最佳努力展示值。
        mode = _read(environ, "KNOWLEDGE_ASSISTANT_REALTIME_MODE").lower() or DEFAULT_MODE
        default_model = LIVETRANSLATE_MODEL if mode == LIVETRANSLATE_MODE else DEFAULT_OMNI_MODEL
        model = _read(environ, "KNOWLEDGE_ASSISTANT_MODEL") or default_model
    voice = _read(environ, "KNOWLEDGE_ASSISTANT_VOICE", DEFAULT_VOICE) or DEFAULT_VOICE
    agent_name = _read(environ, "KNOWLEDGE_ASSISTANT_AGENT_NAME", DEFAULT_AGENT_NAME)
    translation_language = (
        _read(
            environ,
            "KNOWLEDGE_ASSISTANT_TRANSLATION_LANGUAGE",
            DEFAULT_TRANSLATION_LANGUAGE,
        )
        or DEFAULT_TRANSLATION_LANGUAGE
    )

    try:
        enabled = _parse_bool(environ, "KNOWLEDGE_ASSISTANT_ENABLED", True)
    except RuntimeError as exc:
        return {
            "enabled": False,
            "ready": False,
            "reason": str(exc),
            "mode": mode,
            "model": model,
            "voice": voice,
            "agent_name": agent_name or DEFAULT_AGENT_NAME,
            "translation_language": translation_language,
        }

    try:
        config = load_config(environ)
    except RuntimeError as exc:
        return {
            "enabled": enabled,
            "ready": False,
            "reason": str(exc),
            "mode": mode,
            "model": model,
            "voice": voice,
            "agent_name": agent_name or DEFAULT_AGENT_NAME,
            "translation_language": translation_language,
        }

    if not dependencies_available():
        return {
            "enabled": enabled,
            "ready": False,
            "reason": "未安装 AgentScope 实时语音依赖",
            "mode": config.mode,
            "model": config.model,
            "voice": config.voice,
            "agent_name": config.agent_name,
            "translation_language": config.translation_language,
            "pipeline_llm_model": config.pipeline_llm_model,
            "pipeline_tts_model": config.pipeline_tts_model,
            "pipeline_tts_voice": config.pipeline_tts_voice,
        }

    return {
        "enabled": enabled,
        "ready": True,
        "reason": "",
        "mode": config.mode,
        "model": config.model,
        "voice": config.voice,
        "agent_name": config.agent_name,
        "translation_language": config.translation_language,
        "pipeline_llm_model": config.pipeline_llm_model,
        "pipeline_tts_model": config.pipeline_tts_model,
        "pipeline_tts_voice": config.pipeline_tts_voice,
    }


def create_realtime_model(config: RealtimeVoiceConfig):
    """
    按配置构造 DashScope 实时语音模型。

    Args:
        config: 已校验的配置。

    Returns:
        实时翻译模式下为 `LiveTranslateRealtimeModel`，
        实时对话模式下为 `DashScopeRealtimeModel`。

    Raises:
        RuntimeError: AgentScope 实时依赖缺失或模型/音色不受支持。
    """
    try:
        from agentscope.credential import DashScopeCredential
    except ImportError as exc:
        raise RuntimeError(
            '缺少 AgentScope 实时语音依赖，请执行：pip install "agentscope[realtime]"',
        ) from exc

    if config.mode == PIPELINE_MODE:
        raise RuntimeError("pipeline 模式请使用 PipelineVoiceSession，而不是 RealtimeAgent")

    credential = DashScopeCredential(api_key=config.api_key)
    try:
        if config.mode == LIVETRANSLATE_MODE:
            from .livetranslate import LiveTranslateRealtimeModel

            return LiveTranslateRealtimeModel(
                model=config.model,
                credential=credential,
                parameters=LiveTranslateRealtimeModel.Parameters(
                    voice=config.voice,
                    translation_language=config.translation_language,
                ),
            )

        from agentscope.realtime import DashScopeRealtimeModel

        return DashScopeRealtimeModel(
            model=config.model,
            credential=credential,
            parameters=DashScopeRealtimeModel.Parameters(
                voice=config.voice,
                turn_detection=config.turn_detection,
                vad_threshold=config.vad_threshold,
                vad_silence_duration_ms=config.vad_silence_ms,
            ),
        )
    except ValueError as exc:
        raise RuntimeError(
            f"实时语音模型或音色配置无效：{exc}。"
            f"当前模式 {config.mode!r}，模型 {config.model!r}，音色 {config.voice!r}。",
        ) from exc
