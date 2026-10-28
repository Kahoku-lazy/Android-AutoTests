## Why

Pipeline 的 TTS 当前用 `qwen3-tts-flash`。用户指定改用 Sambert 中文音色 `sambert-zhichu-v1`：它同样是 Text → Audio，中文播报自然度可接受，价格 1 元/万字符，且当前 DashScope Key 在标准 WebSocket 域名即可调用，不需要 WorkspaceId。

## What Changes

- Pipeline 默认 TTS 改为 `sambert-zhichu-v1`（音色「知厨」），走 `wss://dashscope.aliyuncs.com/api-ws/v1/inference` 的 `run-task` 协议，返回 24kHz PCM16。
- 新增 `KNOWLEDGE_ASSISTANT_PIPELINE_TTS_PROVIDER`：`sambert`（默认）/ `qwen`；Qwen-TTS 保留为可选。
- 配置新增 provider/model/voice；`ready` 事件与页面模型行显示 `deepseek-flash + sambert-zhichu-v1`、音色「知厨」。
- 保留 TTS 失败只剩文字回答、会话不中断的既有行为。

## 关联文档

- 已归档 `2026-10-28-add-pipeline-voice-mode`
- [Sambert 模型与音色列表](https://help.aliyun.com/zh/model-studio/sambert)
- [Sambert WebSocket 接入](https://help.aliyun.com/zh/model-studio/sambert-websocket-api)

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `knowledge-assistant-voice`: Pipeline 的 TTS 从 qwen3-tts-flash 改为 sambert-zhichu-v1，并把 TTS 厂商做成可配置。

## Impact

- 引擎：`pipeline_tts.py` 增加 `SambertTts`；`pipeline.py` 按 provider 选择 TTS；`config.py` 增加 provider 与默认值。
- 前端：不改结构，`ready.model` / `voice` 自动显示新模型。
- 配置：`.env.example` 默认 Sambert，并保留 Qwen-TTS 示例。
- 测试：配置默认值、Sambert WS 真实合成、Pipeline 端到端。
