## Context

Pipeline 的 `PipelineVoiceSession` 已有 `_answer(text)`、RAG、Sambert TTS。文本输入只需绕过 ASR，复用回答链路。前端现有 `useVoiceSession.start()` 总是启动麦克风；需要支持 `withMic=false`。

## Decisions

### 1. 文本消息走 WS 白名单

浏览器发送 `{"type":"text","text":"..."}`；consumer 持有当前 `PipelineVoiceSession` 引用，调用 `submit_text()`。Omni 会话收到 text 返回可读错误，不做文本注入（实时模型不支持文本输入）。

### 2. submit_text 复用 _answer

`submit_text()`：
1. 等待会话 ready（避免在模型连接前提交）。
2. 取消 finalize/answer。
3. 生成用户 reply_id，发送 `reply_start`/`transcript_delta`/`transcript_final`/`reply_end`。
4. 写用户日志，启动 `_answer(text)`。

### 3. 纯文本会话

`useVoiceSession.start(mode, withMic=false)` 只创建 `AudioPlayer`（点击手势内）和 WS，不调用 `getUserMedia`；等待 `ready` 后再发送文字。`PipelineVoiceSession` 记录 `text_input_used`，watchdog 不提示无麦克风。

### 4. 文本输入只在 Pipeline 显示

`selectedRoute === "pipeline"` 才渲染输入框；Omni 保持纯语音。

## Risks

- [纯文本会话无麦克风] → `stop()`/`dispose()` 对 `mic=null` 安全；watchdog 由 text flag 抑制。
- [ready 前发送] → `submit_text` 等待 `_ready_event`，前端也等 ready。
- [回答中追加文字] → 先取消当前 answer task，再开新用户轮。
