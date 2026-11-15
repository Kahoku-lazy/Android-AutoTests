## Why

语音助手的创建已经收进 `create_voice_agent`，但使用还留在 `realtime_vocie`，并且被 `backend/apps/knowledge_assistant` 直接 import。这和「助手只创建、workflow 才是交给前后端的出口」不一致。文字会话也有同类绕路，本期不并入。

## What Changes

- 新增 `engines/agents/workflow/voice`，作为语音助手的唯一对外出口：会话、浏览器音频传输、转写桥、就绪状态。
- 该出口只调用 `assistant.create_voice_agent`，不自己构造 `RealtimeAgent`，不持有模型连接参数。
- **BREAKING**（引擎内部）：`backend/apps/knowledge_assistant` MUST NOT 再 import `engines.agents.realtime_vocie`。配置、传输、会话都改经 `workflow/voice`。
- `realtime_vocie` 本期不改名、不搬进 `assistant/`。它降为 workflow 的内部实现，包外不再引用。
- 前端 WebSocket 路径、事件类型、鉴权与对话日志位置不变。

## 关联文档

无关联 PRD。原因：这是语音助手使用出口的结构对齐，不改变用户可见的语音问答行为。

## Capabilities

### New Capabilities

- `voice-workflow-exit`: 语音助手经 workflow 出口交给后端；后端不直接使用语音引擎包。

### Modified Capabilities

- `knowledge-assistant-voice`: 引擎接入点从 `realtime_vocie` 改为 `workflow/voice`。会话行为、日志与 WebSocket 契约不变。

## Impact

- 代码：新增 `engines/agents/workflow/voice/`；`backend/apps/knowledge_assistant` 的 consumer / runtime / views 改 import。
- 测试：知识库助手配置、传输、事件桥、consumer 单测改经新出口。
- 非目标：不改 `assistant` 的两个创建出口，不改文字会话 `knowledge_chat`，不改前端协议，不重命名 `realtime_vocie`。
