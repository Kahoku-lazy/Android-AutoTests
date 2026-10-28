## Why

页面路线切到「ASR + DeepSeek Flash + TTS」后，`模型` 行仍显示后端默认的 `qwen3.5-omni-plus-realtime · Tina`，与实际路线不一致，容易让用户误以为选择没有生效。

## What Changes

- 状态接口增加 pipeline 的 LLM/TTS 模型与音色字段。
- 前端未开始会话时，`模型` 行按当前所选路线显示：Omni 显示后端 `model`，Pipeline 显示 `deepseek-flash + sambert-zhichu-v1 · 知厨`。
- 会话开始后仍以 `ready` 事件的实际 `model`/`voice` 为准。

## 关联文档

- 已归档 `2026-10-28-add-pipeline-voice-mode`
- 已归档 `2026-10-28-switch-pipeline-tts-to-sambert`

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `knowledge-assistant-voice`: 补充「模型行跟随所选路线」的展示要求。

## Impact

- 后端：`build_runtime_status()` 增加 pipeline 字段。
- 前端：状态类型与 `modelLabel` 计算；不改语音链路。
- 测试：状态字段单测、页面路线切换检查。
