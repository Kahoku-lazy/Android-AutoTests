## 1. 前端可观测

- [x] 1.1 `MicCapture` 增加 `onLevel` 与分块 RMS，并在 `start` 中先创建/恢复 AudioContext 再申请麦克风；验证：typecheck 通过，页面电平条随假麦克风 WAV 变化。
- [x] 1.2 `useVoiceSession` 增加 `micLevel` / `sentFrames` / `noticeMessage`，首帧到达时清除无输入提示；验证：typecheck 通过。
- [x] 1.3 `VoiceConsole` 增加麦克风状态文案、电平条与非致命提示区；验证：浏览器截图可见「麦克风：有信号，等待说话」与电平条。
- [x] 1.4 `index.vue` 透传新增 props；验证：`npm run build` 通过。

## 2. 后端诊断

- [x] 2.1 `WebSocketAudioTransport` 统计 `audio_frames` / `audio_bytes`；验证：`test_knowledge_assistant_transport.py` 新增守卫，帧数与字节数正确。
- [x] 2.2 `KnowledgeVoiceSession` 在 `session_end` 写入两个计数字段；验证：真实会话日志出现 `audio_frames` 大于 0。
- [x] 2.3 增加 6 秒无帧看门狗，下发 `notice` 而不关闭会话；验证：无音频连接在 6 秒后收到 `notice`，有音频连接不收到。

## 3. 验证

- [x] 3.1 后端：`ruff check` / `ruff format --check` / 相关 pytest 通过。
- [x] 3.2 前端：`npm run typecheck` / `npx eslint` / 相关 vitest 通过。
- [x] 3.3 真实链路：WAV 假麦克风跑通，`session_end` 记录 `audio_frames=54`、`audio_bytes=172800`；无音频连接收到无输入提示。
- [x] 3.4 `openspec validate add-knowledge-assistant-mic-diagnostics --strict` 通过。
