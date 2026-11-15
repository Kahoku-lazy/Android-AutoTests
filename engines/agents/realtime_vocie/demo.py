"""
文件名: ➡️ demo.py 🏁
路径: ➡️ engines/agents/realtime_vocie/demo.py 🏁
模块功能：➡️ 本地麦克风语音演示：只转调语音创建出口 🏁
Python 调试：➡️ python -m engines.agents.realtime_vocie.demo 🏁
时间：➡️ 2026-10-30 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.1.0 🏁
修改时间: ➡️ 2026-11-11 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. build_realtime_vocie_agent: 按 OMNI_ROLE_CONFIG 创建 RealtimeAgent。
2. run_local_s2s: 本地麦克风演示，不在本模块构造实时语音智能体。
🏁
关联模块：➡️
1. engines.agents.assistant: 导入 create_voice_agent，只转调语音出口
2. engines.agents.config.config: 导入 load_agent_config / load_model_config，读两张表
🏁
测试：➡️
1. tests/engines/agents/unit/test_voice_workflow_exit.py: 演示入口不直接构造实时语音智能体
🏁
"""

from __future__ import annotations

import asyncio
import os

from pathlib import Path

from engines.agents.assistant import create_voice_agent
from engines.agents.config.config import load_agent_config, load_model_config

# 仓库根 .env（engines/agents/realtime_vocie/本文件 → parents[3]）
_REPO_ROOT = Path(__file__).resolve().parents[3]
try:
    from dotenv import load_dotenv

    load_dotenv(_REPO_ROOT / ".env")
except ImportError:
    # python-dotenv 是可选依赖：未安装时跳过 .env 加载，改由调用方自行 export 环境变量
    pass

__all__ = ["build_realtime_vocie_agent", "main", "run_local_s2s"]


def build_realtime_vocie_agent() -> tuple[object, object]:
    """按 OMNI_ROLE_CONFIG 创建 RealtimeAgent 与底层实时模型。

    Returns:
        (RealtimeAgent, DashScopeRealtimeModel)。

    Raises:
        RuntimeError: 未安装 agentscope[realtime]。
        ValueError: YAML / 环境变量不合法，或未设置 DASHSCOPE_API_KEY。
    """
    if not (os.getenv("DASHSCOPE_API_KEY") or "").strip():
        raise ValueError(
            "未设置 DASHSCOPE_API_KEY：请在仓库根 .env 写入该键，"
            "或先 export / 设置环境变量（需要 python-dotenv 时请 pip install python-dotenv）"
        )
    agent = create_voice_agent(load_agent_config(), load_model_config(), "OMNI_ROLE_CONFIG")
    return agent, agent.model


async def run_local_s2s() -> None:
    """本地麦克风 S2S 演示：对齐 AgentScope speech-to-speech 教程（DashScope Omni）。

    Raises:
        RuntimeError: 未安装 agentscope[realtime]，无法使用本地音频传输。
    """
    try:
        from agentscope.realtime import LocalAudioTransport
    except ImportError as exc:
        raise RuntimeError(
            '本地音频传输需要 agentscope realtime 额外依赖：pip install "agentscope[realtime]"'
        ) from exc

    agent, model = build_realtime_vocie_agent()
    transport = LocalAudioTransport(
        input_sample_rate=model.input_sample_rate,
        output_sample_rate=model.output_sample_rate,
    )
    print(
        f"[realtime_vocie_agent] model={model.model!r} "
        f"name={agent.name!r} — 开始本地语音会话（Ctrl+C 结束）"
    )
    async with agent, transport:
        async for event in agent.reply_stream(transport):
            text = getattr(event, "text", None)
            if text:
                print(text, end="", flush=True)
            elif getattr(event, "type", None):
                # 非文本事件仅作轻量提示，避免刷屏
                et = getattr(event, "type", "")
                if et in {"audio", "AudioEvent"}:
                    continue
                print(f"\n[{et}]", flush=True)


def main() -> None:
    """同步入口：跑本地 S2S 演示。"""
    try:
        asyncio.run(run_local_s2s())
    except KeyboardInterrupt:
        print("\n[realtime_vocie_agent] 已结束")


if __name__ == "__main__":
    main()
