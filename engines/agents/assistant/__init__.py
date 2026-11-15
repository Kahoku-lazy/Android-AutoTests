"""
文件名: ➡️ __init__.py 🏁
路径: ➡️ engines/agents/assistant/__init__.py 🏁
模块功能：➡️ 智能体创建门面：聊天出口与语音出口 🏁
Python 调试：➡️ python -m engines.agents.assistant 🏁
时间：➡️ 2026-11-11 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-11 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. create_chat_agent: 只接受 chat 族，返回新的 Agent。
2. create_voice_agent: 只接受 realtime 族，返回新的 RealtimeAgent。
3. 本包只创建：不 reply、不跑 SOP、不跑语音会话。
4. 本包与 agent_builders 并存：前者是创建目标，后者只转调聊天出口。
🏁
关联模块：➡️
1. engines.agents.assistant.create: 两个出口的实现。
2. engines.agents.assistant.schema: AgentConfigError。
3. engines.agents.config.config: load_agent_config / load_model_config（调用方使用，本包不调用）。
4. engines.agents.models: create_model，按短名造模型。
🏁
测试：➡️
1. tests/engines/agents/unit/test_assistant_create.py: 分派、校验、空工具包与覆盖参数
🏁
"""

from __future__ import annotations

from .create import clear_chat_model_cache, create_chat_agent, create_voice_agent
from .schema import AgentConfigError

__all__ = ["AgentConfigError", "clear_chat_model_cache", "create_chat_agent", "create_voice_agent"]
