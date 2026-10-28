## Context

已归档的 `2026-10-28-add-knowledge-assistant-voice` 建立了语音链路；现场反馈「点击开始对话没有反应」时，服务端只看到会话建立后无消息，无法判断是麦克风没采到、设备静音还是 VAD 没识别。音频帧计数与前端电平能把这三类情况分开。

## Goals / Non-Goals

**Goals:**

- 让用户和排障者能直接看到“有没有音频帧”“电平是否变化”。
- 无音频帧时给出非致命、可操作的提示。
- 不改变会话协议、WS 路径与日志主字段。

**Non-Goals:**

- 不做设备选择器或系统音频设置页面。
- 不做音频文件回放或录音上传。
- 不改变模型、VAD 参数或日志按日分文件策略。

## Decisions

### 1. 电平在前端算，帧数在后端算

前端 `MicCapture` 每 100ms 分块算 RMS，驱动 UI 电平；服务端在 `push_audio` 累加 `audio_frames/audio_bytes`，会话结束时写入 `session_end`。前者回答“麦克风有没有声音”，后者回答“音频有没有真的到后端”，两者缺一不可。

### 2. 6 秒看门狗只提示、不失败

看门狗在 `ready` 后启动；6 秒内 `audio_frames == 0` 才下发 `notice`。它不关闭会话，因为用户可能正在切换默认输入设备；页面收到提示后仍保持「聆听中」。若提示后开始有帧，前端在首帧发送时清除提示。

### 3. AudioContext 先建后授权

`MicCapture.start` 先在点击手势内 `new AudioContext()` 并 `resume()`，再 `await getUserMedia`；`useVoiceSession.start` 先起播放器再起麦克风。这样避免部分浏览器在授权等待后把采集上下文留在 suspended，导致一帧都不产生。

## 模块防火墙自检

- 只在 `backend/apps/knowledge_assistant` 内改传输/会话，在前端知识库助手模块内改采集/状态；无跨 App import、无数据库写入。
- WS 仍只走 `/ws/knowledge-assistant/`，不接 channel layer。

## Risks / Trade-offs

- [6 秒看门狗在用户迟迟不开口时误报] → 只在“一帧都没有”时触发；有帧但静音只显示「有信号，等待说话」。
- [电平条频繁刷新增加渲染] → 每 100ms 一次且只更新一个 `ref`，可接受。
- [诊断字段改变日志行结构] → 只给 `session_end` 增加两个字段，既有必填字段不变，读取方按 JSON 解析不受影响。
