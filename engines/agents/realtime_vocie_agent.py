"""
文件名: ➡️ realtime_vocie_agent.py 🏁
路径: ➡️ engines/agents/realtime_vocie_agent.py 🏁
模块功能：➡️ Voice agents：DashScope Omni 实时语音角色（教程直连） 🏁
Python 调试：➡️ python -m engines.agents.realtime_vocie_agent 🏁
时间：➡️ 2026-10-30 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-10-30 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. build_realtime_vocie_agent: 按 agent_config.yaml OMNI_ROLE_CONFIG 组装 RealtimeAgent
2. run_local_s2s: LocalAudioTransport + reply_stream 本地麦克风演示（AgentScope S2S 教程）
🏁
关联模块：➡️
1. engines.agents.models: 导入 get_realtime_model，取 Omni 实时语音模型实例
2. engines.agents.config.role_loader: 导入 load_role_spec，取 OMNI_ROLE_CONFIG 的角色名与提示词
🏁
测试：➡️
1. 暂无专门单测
🏁
"""

from __future__ import annotations

import asyncio
import os

from pathlib import Path

from agentscope.agent import RealtimeAgent

from engines.agents.config.role_loader import load_role_spec
from engines.agents.models import get_realtime_model

# 仓库根 .env（engines/agents/本文件 → parents[3]）
_REPO_ROOT = Path(__file__).resolve().parents[2]
try:
    from dotenv import load_dotenv

    load_dotenv(_REPO_ROOT / ".env")
except ImportError:
    pass


def build_realtime_vocie_agent() -> tuple[RealtimeAgent, object]:
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
    role_config = load_role_spec("OMNI_ROLE_CONFIG").role
    model = get_realtime_model(role_key="OMNI_ROLE_CONFIG")
    agent = RealtimeAgent(
        name=role_config.name,
        system_prompt=role_config.system_prompt,
        model=model,
    )
    return agent, model


async def run_local_s2s() -> None:
    """本地麦克风 S2S 演示：对齐 AgentScope speech-to-speech 教程（DashScope Omni）。"""
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
