## Context

见 proposal.md - Why。现状：

- `assistant.create_voice_agent` 已只负责创建。
- `realtime_vocie/session.py` 仍自己读两张表、调用创建出口、注入 RAG，并跑 `reply_stream(transport)`。
- `backend/apps/knowledge_assistant` 直接 import 该包的 `load_config`、`WebSocketAudioTransport`、`RealtimeVoiceSession`、`build_runtime_status`。
- `knowledge_chat/session.py` 直接 import `TranscriptBridge`。文字会话本期不改产品行为，但若语音包要变成内部实现，这条引用必须改道，否则包外禁令不成立。
- `workflow/single` 已是「清单 + 会话 + 后端只调 workflow」的先例。

## Goals / Non-Goals

**Goals:**

- `workflow/voice` 成为后端唯一语音入口。
- 创建仍只走 `create_voice_agent`。
- 前端协议与对话日志路径不变。

**Non-Goals:**

- 不把 `session.py` 搬进 `assistant/`。
- 不重命名 `realtime_vocie`，不删除其文件。
- 不改文字问答的模型、提示词或 WebSocket 模式。
- 不改 `workflow/single` 的 Android UI 会话。

## Decisions

### 1. 新出口放在 `workflow/voice`，不放在 `assistant`

备选是把会话、传输、事件桥搬进 `assistant`。否决：助手红线是只创建、不启动语音会话。把 `reply_stream` 放进去会把刚切开的边界合回去。

`workflow/voice` 对外导出：打开会话、就绪状态、浏览器音频传输。内部可以继续调用现有 `realtime_vocie` 模块，避免本期搬文件。

### 2. 包外禁令一次收干净

`backend/` 与 `knowledge_chat` 都改为 import `workflow/voice`。`TranscriptBridge` 由 workflow 再导出，文字会话不直接碰语音包。

备选是只改后端、允许文字会话继续引用 `realtime_vocie.events`。否决：那样「包外不再引用」不成立，下次还会从文字侧绕回去。

### 3. 传输仍由后端持有

官方 2.0.9 把音频传输的生命周期交给调用方，智能体只借用。后端继续创建并关闭 WebSocket 传输；workflow 只接收已启动的传输。这样断开连接时不会由 workflow 去关浏览器通道。

### 4. 不改名

`realtime_vocie` 的拼写留到单独变更。本期只改依赖方向。

## 模块防火墙自检

- 新增依赖：`backend/apps/knowledge_assistant` → `engines.agents.workflow.voice`。这是既有的「后端调 engines」方向，不写库，不跨 App import service。
- workflow MUST NOT import `backend.apps` / `django`。
- assistant MUST NOT import workflow。
- 前端不改，仪表盘不涉及。

## Risks / Trade-offs

- [文字会话多一次再导出] → 只再导出转写桥和日志协议，不把文字会话并进语音 workflow。
- [内部仍是旧包] → 包外测试改为经 workflow 导入；内部单测可暂时保留旧路径，但 backend 测试不能再直接引用。
- [就绪状态字段被出口包一层后漂移] → 出口原样返回现有状态字典，单测对拍 `ready` / `text_ready`。
