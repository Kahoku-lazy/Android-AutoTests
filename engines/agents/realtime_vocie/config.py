"""
文件名: ➡️ config.py 🏁
路径: ➡️ engines/agents/realtime_vocie/config.py 🏁
模块功能：➡️ 2. load_config(): 从根 `.env` / 环境变量读取并校验配置 🏁
Python 调试：➡️ python -m engines.agents.realtime_vocie.config 🏁
时间：➡️ 2026-10-30 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-10-30 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. RealtimeVoiceConfig: 保存一次 Omni 实时语音 + 知识库问答会话所需的模型与提示词配置。
2. load_config(): 从根 `.env` / 环境变量读取并校验配置。
3. build_runtime_status(): 生成不含密钥的就绪状态字段。
4. create_realtime_model(): 按配置构造 AgentScope 的 DashScope Omni 实时语音模型。
🏁
关联模块：➡️
1. 暂无本地 engines/utils 依赖
🏁
测试：➡️
1. tests/graybox/unit/test_knowledge_assistant_config.py: 知识库助手 Omni 配置单测：不联网
2. tests/graybox/unit/test_realtime_vocie_models.py: Omni realtime 模型工厂单测：不联网
🏁
"""

from __future__ import annotations

import importlib.util
import os

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from typing import Final

# 目录可能因缺 config.yaml 不可用；本包仍应能用硬编码默认 + 环境变量跑 Omni。
try:
    from engines.agents.config.models import DEFAULT_OMNI_MODEL as _CATALOG_OMNI
    from engines.agents.config.models import get_realtime as _get_realtime
except Exception:  # pragma: no cover - 缺目录时的兜底
    _CATALOG_OMNI = "qwen3.5-omni-plus-realtime"
    _get_realtime = None  # type: ignore[assignment]

from .knowledge import build_system_prompt

OMNI_MODE: Final[str] = "omni"
DEFAULT_MODE: Final[str] = OMNI_MODE
DEFAULT_OMNI_MODEL: Final[str] = _CATALOG_OMNI
DEFAULT_MODEL: Final[str] = DEFAULT_OMNI_MODEL
DEFAULT_VOICE: Final[str] = "Tina"
DEFAULT_TURN_DETECTION: Final[str] = "server_vad"
DEFAULT_AGENT_NAME: Final[str] = "知识库助手"
SUPPORTED_TURN_DETECTIONS: Final[tuple[str, ...]] = ("server_vad", "semantic_vad")


@dataclass(frozen=True)
class RealtimeVoiceConfig:
    """
    一次 Omni 实时语音会话的模型与提示词配置。

    Attributes:
        api_key: DashScope API Key；repr 中隐藏，避免误打日志。
        model: Omni 实时语音模型名。
        voice: 音色名。
        turn_detection: 服务端回合检测方式。
        agent_name: 助手名称，出现在提示词与转写事件里。
        system_prompt: 系统提示词（含知识库问答指引）。
        vad_threshold: 服务端 VAD 的语音概率阈值，越低越容易触发。
        vad_silence_ms: 服务端 VAD 判定说完所需的静音毫秒数。
        mode: 固定为 `omni`（兼容 ready 事件与日志字段）。
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


def _read(environ: Mapping[str, str] | None, name: str, default: str = "") -> str:
    """读取一个配置项：显式传入的映射优先，否则读进程环境变量。"""
    value = environ.get(name) if environ is not None else os.environ.get(name)
    return (value or default).strip()


def _parse_bool(environ: Mapping[str, str] | None, name: str, default: bool) -> bool:
    """解析布尔配置，接受 1/true/yes/on 与 0/false/no/off。"""
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


def _resolve_api_key(environ: Mapping[str, str] | None) -> str:
    """解析 DashScope API Key（优先目录 api_key_env，否则 DASHSCOPE_API_KEY）。"""
    if _get_realtime is not None:
        try:
            return _read(environ, _get_realtime("omni").api_key_env)
        except Exception:
            pass
    return _read(environ, "DASHSCOPE_API_KEY")


def _resolve_model(environ: Mapping[str, str] | None) -> str:
    """解析 Omni 模型名；拒绝 livetranslate / 非 omni 模式。"""
    model_raw = _read(environ, "KNOWLEDGE_ASSISTANT_MODEL") or DEFAULT_OMNI_MODEL
    if "livetranslate" in model_raw.lower():
        raise RuntimeError(
            f"知识库助手仅支持 Omni 实时模型，不能使用 {model_raw!r}",
        )
    mode_raw = _read(environ, "KNOWLEDGE_ASSISTANT_REALTIME_MODE").lower()
    if mode_raw and mode_raw != OMNI_MODE:
        raise RuntimeError(
            f"知识库助手仅支持 omni 模式，当前为 {mode_raw!r}",
        )
    return model_raw


def dependencies_available() -> bool:
    """判断实时语音依赖是否已安装，供状态接口使用。"""
    try:
        return (
            importlib.util.find_spec("agentscope") is not None
            and importlib.util.find_spec("agentscope.realtime") is not None
        )
    except Exception:
        return False


def load_config(environ: Mapping[str, str] | None = None) -> RealtimeVoiceConfig:
    """
    读取并校验一次 Omni 实时语音会话的配置。

    Args:
        environ: 测试注入的配置映射；None 表示读 `os.environ`。

    Returns:
        校验完成的配置。

    Raises:
        RuntimeError: 功能被关闭、缺少 API Key 或配置值非法。
    """
    if not _parse_bool(environ, "KNOWLEDGE_ASSISTANT_ENABLED", True):
        raise RuntimeError("知识库助手已关闭（KNOWLEDGE_ASSISTANT_ENABLED=false）")

    api_key = _resolve_api_key(environ)
    if not api_key:
        raise RuntimeError("缺少 DASHSCOPE_API_KEY，无法连接实时语音模型")

    model = _resolve_model(environ)
    voice = _read(environ, "KNOWLEDGE_ASSISTANT_VOICE", DEFAULT_VOICE) or DEFAULT_VOICE
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
        mode=OMNI_MODE,
    )


def build_runtime_status(environ: Mapping[str, str] | None = None) -> dict:
    """
    生成状态接口的模型/依赖字段，不包含密钥与日志路径。

    Args:
        environ: 测试注入的配置映射；None 表示读 `os.environ`。

    Returns:
        含 enabled / ready / reason / mode / model / voice / agent_name 的字典。
    """
    model = _read(environ, "KNOWLEDGE_ASSISTANT_MODEL") or DEFAULT_OMNI_MODEL
    voice = _read(environ, "KNOWLEDGE_ASSISTANT_VOICE", DEFAULT_VOICE) or DEFAULT_VOICE
    agent_name = _read(environ, "KNOWLEDGE_ASSISTANT_AGENT_NAME", DEFAULT_AGENT_NAME)

    try:
        enabled = _parse_bool(environ, "KNOWLEDGE_ASSISTANT_ENABLED", True)
    except RuntimeError as exc:
        return {
            "enabled": False,
            "ready": False,
            "reason": str(exc),
            "mode": OMNI_MODE,
            "model": model,
            "voice": voice,
            "agent_name": agent_name or DEFAULT_AGENT_NAME,
        }

    try:
        config = load_config(environ)
    except RuntimeError as exc:
        return {
            "enabled": enabled,
            "ready": False,
            "reason": str(exc),
            "mode": OMNI_MODE,
            "model": model,
            "voice": voice,
            "agent_name": agent_name or DEFAULT_AGENT_NAME,
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
        }

    return {
        "enabled": enabled,
        "ready": True,
        "reason": "",
        "mode": config.mode,
        "model": config.model,
        "voice": config.voice,
        "agent_name": config.agent_name,
    }


def create_realtime_model(config: RealtimeVoiceConfig):
    """
    按配置构造 DashScope Omni 实时语音模型。

    Args:
        config: 已校验的配置。

    Returns:
        `DashScopeRealtimeModel` 实例。

    Raises:
        RuntimeError: AgentScope 实时依赖缺失，或模型/音色不受支持。
    """
    from agentscope.realtime import DashScopeRealtimeModel

    parameters = DashScopeRealtimeModel.Parameters(
        voice=config.voice,
        turn_detection=config.turn_detection,
        vad_threshold=config.vad_threshold,
        vad_silence_duration_ms=config.vad_silence_ms,
    )

    if _get_realtime is not None:
        try:
            ready = _get_realtime("omni")
            ready_for_call = (
                ready if ready.model == config.model else replace(ready, model=config.model)
            )
            return ready_for_call.create_realtime_model(
                api_key=config.api_key,
                parameters=parameters,
            )
        except Exception:
            pass

    try:
        from agentscope.credential import DashScopeCredential
    except ImportError as exc:
        raise RuntimeError(
            '缺少 AgentScope 实时语音依赖，请执行：pip install "agentscope[realtime]"',
        ) from exc

    return DashScopeRealtimeModel(
        model=config.model,
        credential=DashScopeCredential(api_key=config.api_key),
        parameters=parameters,
    )
