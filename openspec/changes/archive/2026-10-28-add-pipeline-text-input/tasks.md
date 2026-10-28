## 1. 后端

- [x] 1.1 `PipelineVoiceSession.submit_text()` + ready event + text flag
- [x] 1.2 consumer 处理 `text`，持有 Pipeline 会话引用
- [x] 1.3 更新 WS 白名单与 AGENTS

## 2. 前端

- [x] 2.1 `useVoiceSession.sendText()` 与 `start(mode, withMic=false)`
- [x] 2.2 `VoiceConsole` 文本输入框（仅 pipeline）
- [x] 2.3 页面接线与错误处理

## 3. 验证

- [x] 3.1 纯文本提问“长按开关按键 3 秒”返回 RAG 回答 + 音频
- [x] 3.2 语音会话中追加文字正常
- [x] 3.3 ruff / pytest / typecheck / build
- [x] 3.4 `openspec validate add-pipeline-text-input --strict` 并归档
