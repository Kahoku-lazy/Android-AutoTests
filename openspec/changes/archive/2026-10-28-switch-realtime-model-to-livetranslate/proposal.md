## Why

当前默认使用 `qwen3.5-omni-plus-realtime`，实时对话费用偏高。`qwen3.8-livetranslate-flash-realtime` 的音频输入/输出单价更低，适合先承担语音链路；同时保留原有 Omni 实时对话作为可选调用方式，避免模型能力变化时无法回退。

## What Changes

- 默认调用方式改为 `livetranslate`，默认模型改为 `qwen3.8-livetranslate-flash-realtime`，默认目标语种 `zh`、音色 `Tina`。
- 新增 `KNOWLEDGE_ASSISTANT_REALTIME_MODE`：`livetranslate`（默认）/ `omni`；也可仅配 `KNOWLEDGE_ASSISTANT_MODEL`，按模型名自动推断调用方式。
- 新增 `LiveTranslateRealtimeModel` 适配器：使用 `session.output_modalities`、`session.translation.language`、`speaker_detection`；译文取 `response.audio_transcript.delta` / `response.text.delta`，音频取 `response.audio.delta`，结束前发 `session.finish`。
- 保留原 `DashScopeRealtimeModel`（Omni）作为 `omni` 模式；mode 与模型名不匹配时拒绝启动并给出可读原因。
- 就绪状态与 `ready` 事件新增 `mode`、`translation_language`；页面标题副标题与「模式」行显示当前调用方式。
- 说明：`qwen3.8-livetranslate` 本质是**实时翻译**模型，不会按知识库提示词回答问题；需要问答时切回 `omni`。

## 关联文档

- 已归档变更 `2026-10-28-add-knowledge-assistant-voice`
- 阿里云百炼 `qwen3.8-livetranslate-flash-realtime` 模型说明与实时翻译 WebSocket 接入文档

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `knowledge-assistant-voice`: 新增「调用方式可选且默认实时翻译模型」需求。

## Impact

- 引擎：新增 `engines/agents/realtime_vocie/livetranslate.py`；`config.py` 增加 mode/translation_language 与模型选择；`session.py` ready 事件带 mode。
- 前端：状态/ready 类型增加 mode/translation_language；页面副标题与「模式」行随模式变化。
- 配置：`.env.example` 默认 `livetranslate` 与 `qwen3.8-livetranslate-flash-realtime`，并给出回退 omni 的注释。
- 测试：新增适配器协议映射与模型选择单测；真实 WAV 链路回归。
