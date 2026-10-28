## Why

Pipeline 路线目前只能语音输入。用户需要在「ASR + DeepSeek Flash + TTS」模式下直接输入文字提问，跳过 ASR，仍走 DeepSeek + RAG + Sambert TTS。

## What Changes

- 前端在 Pipeline 路线显示文本输入框；支持回车/按钮发送。
- 未开始会话时发送文本会自动建立**纯文本会话**（不申请麦克风，仍建立播放器与 WS）。
- WS 增加 `text` 白名单消息；consumer 只在 Pipeline 会话下转给 `PipelineVoiceSession.submit_text()`。
- `submit_text()` 生成用户消息、取消进行中的回答、调用 DeepSeek（含 RAG）、Sambert TTS 播报。
- 纯文本会话不触发“没有检测到麦克风”提示。

## 关联文档

- 已归档 `2026-10-28-add-pipeline-voice-mode`

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `knowledge-assistant-voice`: 新增 Pipeline 文本输入需求。

## Impact

- 引擎：`PipelineVoiceSession.submit_text()` 与 ready 事件。
- 后端：consumer 处理 `text` 消息；WS 白名单增加一项。
- 前端：`VoiceConsole` 文本输入、`useVoiceSession.sendText()`、纯文本启动。
- 测试：文字提问走 DeepSeek/RAG/Sambert，页面显示用户+助手消息。
