## Why

用户点击「开始对话」后通道已建立、模型已就绪，但页面没有任何“麦克风到底有没有声音”的反馈；现场麦克风静音、默认输入设备选错或 AudioContext 被浏览器挂起时，只能看到长时间无反应，无法判断是设备问题还是服务问题。

## What Changes

- 会话进行中在语音台显示麦克风状态（未采集到音频 / 有信号等待说话 / 有输入）与实时电平条。
- 服务端统计每个会话的上行音频帧数与字节数，写入 `session_end`，用于判断音频是否真的到达后端。
- 就绪后 6 秒内一帧上行音频都没收到时，服务端下发非致命提示；页面显示“检查系统默认输入设备与浏览器麦克风权限”，不关闭会话。
- 调整前端 AudioContext 建立顺序：先在点击手势内创建并恢复，再申请麦克风权限，避免部分浏览器把采集上下文留在 suspended。

## 关联文档

- PRD 五、非功能约束（实时性 / 可观测）
- 已归档变更 `2026-10-28-add-knowledge-assistant-voice`

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `knowledge-assistant-voice`: 新增「麦克风输入可观测且无输入可提示」需求。

## Impact

- 前端：`MicCapture` 增加电平回调；`useVoiceSession` 增加 micLevel / sentFrames / noticeMessage；`VoiceConsole` 增加麦克风状态、电平条与提示；`index.vue` 透传。
- 后端：`WebSocketAudioTransport` 统计 `audio_frames/audio_bytes`；`KnowledgeVoiceSession` 增加 6 秒看门狗与 `session_end` 诊断字段。
- 测试：transport 单测覆盖帧数统计；前端 typecheck / 现有 p0 用例通过。
- 不改变 WebSocket 路径、模型、日志格式或侧栏结构。
