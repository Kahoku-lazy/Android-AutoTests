## Context

现有 `RealtimeVoiceSession` 只依赖 `RealtimeModelBase`，因此可以按配置替换模型适配器而不改 WS、传输与前端消息。`qwen3.8-livetranslate-flash-realtime` 与 Omni 共用 DashScope Realtime WebSocket 地址与 `input_audio_buffer.append`，但会话配置和返回事件不同。

## Goals / Non-Goals

**Goals:**

- 默认走更便宜的实时翻译模型，同时保留 Omni 回退。
- 适配器只做协议映射，不改会话/传输/日志边界。
- 页面能看出当前是实时翻译还是语音问答。

**Non-Goals:**

- 不把翻译结果再送 LLM 做知识问答；本期只替换语音模型。
- 不改前端音频采集、WS 路径或日志字段。
- 不引入 AOQ/WebRTC SDK；仍用服务端 WebSocket 桥接。

## Decisions

### 1. 用子类适配器，不复制整套会话

`LiveTranslateRealtimeModel(DashScopeRealtimeModel)` 复用 `push_audio`、`_read`、`_send`、事件队列；只覆盖 `connect` / `_session_update` / `_parse` / `commit_turn` / `request_response` / `cancel_response`。

- 模型卡显式传入（`LIVETRANSLATE_CARD`），因为 AgentScope 2.0.9 未内置该模型卡。
- `connect` 等待 `session.updated` 再放行音频，避免会话配置未生效就推流。
- `close` 先发 `session.finish` 再关闭，尽量收完最后一段译文。

### 2. 调用方式由 mode + 模型名共同决定

`KNOWLEDGE_ASSISTANT_REALTIME_MODE` 显式优先；未设置时，模型名含 `omni` 推断为 `omni`，否则 `livetranslate`。显式 mode 与模型名冲突直接拒绝，避免把 Omni 模型交给翻译适配器。

### 3. 默认目标语种 zh

知识库助手面向中文用户，默认 `translation.language=zh`；需要英文/日文时用 `KNOWLEDGE_ASSISTANT_TRANSLATION_LANGUAGE` 覆盖。默认音色 `Tina`（该模型不接受 Omni 默认的 `Chelsie`）。

### 4. 明确产品语义

实时翻译模型不会回答问题，只会把语音翻译成目标语种。页面副标题与「模式」行显示「实时翻译」，避免用户误以为仍是知识问答；需要问答时切回 `omni`。

## 模块防火墙自检

- 适配器在 `engines/agents/realtime_vocie/`，只依赖 AgentScope 与标准库；不 import 后端 App。
- 后端仍只做 consumer/runtime/日志；前端只增加字段展示。
- 无数据库写入、无新增 WS 通道。

## Risks / Trade-offs

- [翻译模型不回答问题] → 页面显示「实时翻译」；`.env.example` 给出 omni 回退注释，最终答复中明确说明。
- [模型音色限制] → 默认 `Tina`；`Chelsie` 会 1007 关闭。
- [翻译模式不支持工具] → 不装配工具，`supports_text_input=False`。
- [session.finish 后立即断开可能丢尾音] → `close` 等待 200ms；尾部丢字由下一轮或日志接受。
- [AgentScope 版本升级后私有接口变化] → 适配器集中在一个文件，单测覆盖 `_parse` 与 session.update，升级时只改这一处。
