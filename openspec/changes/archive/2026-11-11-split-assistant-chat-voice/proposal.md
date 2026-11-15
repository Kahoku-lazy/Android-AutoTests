## Why

`assistant.create_agent` 先造模型，再看实例类型决定造 `Agent` 还是 `RealtimeAgent`。调用方拿到的返回类型不稳定，语音角色节里的 `context` / `react` / `stream` 也没有意义。新结构还没切开这一刀，后面每多一个调用方接到这个混合出口，拆的时候就要再改一次。

## What Changes

- assistant 拆成两个出口：`create_chat_agent` 只造 `Agent`，`create_voice_agent` 只造 `RealtimeAgent`。
- 聊天出口拒绝 `realtime` / `embedding` / `tts`；语音出口拒绝非 `realtime`，并拒绝 `context`、`react`、中间件与 `stream`。选错族在创建时失败，消息带角色键和实际 `family`。
- **BREAKING**（引擎内部）：公共 `create_agent` 不再按实例类型分支。`agent_builders.build_*` 只转调聊天出口；`realtime_vocie` 会话只转调语音出口。
- TTS 仍是聊天 Agent 上的中间件，嵌入仍只给 RAG。两者不进 assistant。
- workflow 编排不动，仍只接收聊天助手。旧包 `engines.agents.models` 本期不删。

## 关联文档

无关联 PRD。原因：这是智能体创建层的结构对齐，不改变任务、用例、语音会话或前端可观察行为。

## Capabilities

### New Capabilities

- `assistant-chat-voice`: 由 config 传入的角色表与模型表，按角色键分别创建聊天助手或语音助手；族不对即拒绝。

### Modified Capabilities

- `agent-harness`: 可运行角色的创建入口从「一个 `create_agent` 按实例类型分派」改为「聊天与语音两个出口；旧名字只转调对应出口」。

## Impact

- 代码：`engines/agents/assistant/`、`agent_builders.py`、`realtime_vocie_agent.py`、`realtime_vocie/session.py`。
- 依赖方向不变：assistant → models_new；MUST NOT import 旧包 `engines.agents.models`、workflow、apps、django。
- 测试：改 assistant 单测；既有角色装配、workflow 边界、知识库文字与语音配置单测应保持通过。
- 非目标：不改 workflow 每步新建，不删 `agent_builders.py`，不迁移 RAG / TTS / 模型画廊，不改事件落库。
