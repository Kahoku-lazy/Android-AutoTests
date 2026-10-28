## Why

Omni 直连问答质量好但费用高；需要一个更便宜的问答路线，同时不牺牲「我问模型答」的交互。目标链路是：

`livetranslate 做 ASR → DeepSeek Flash 回答 → TTS 播报`

前端需要在「Omni 直连」与「ASR + DeepSeek + TTS」之间按会话选择。

**能力边界**：`qwen3.8-livetranslate-flash-realtime` 的输入模态是 Audio/Image，不支持文本输入，不能把 DeepSeek 的回答文本直接交给它合成语音。因此 TTS 使用百炼的 `qwen3-tts-flash`（文本输入、音频输出），livetranslate 只负责 ASR；这是当前可落地的同价位替代。若后续官方开放 livetranslate 文本输入，可替换 TTS 适配器。

## What Changes

- 新增第三种调用方式 `pipeline`：前端 WS 连接带 `mode=pipeline`，后端使用独立 `PipelineVoiceSession`。
- Pipeline 链路：
  - ASR：`qwen3.8-livetranslate-flash-realtime`，只取源语转写（`output_modalities=["text"]`，忽略译文）。
  - 回答：`deepseek-flash`，流式输出，保留最近多轮上下文。
  - TTS：`qwen3-tts-flash`，`Cherry` 音色，24kHz PCM16 下发浏览器。
- 前端新增「路线」选择：`Omni 直连 · qwen3.5-omni-plus-realtime · Tina` / `ASR + DeepSeek Flash + TTS`；按选择带 `mode` 查询参数，默认 Omni。
- 会话 ready 事件返回实际路线、模型标签、音色与采样率；页面「模式」行显示路线。
- 保留现有 `livetranslate` 纯翻译模式。

## 关联文档

- 已归档 `2026-10-28-default-omni-direct-dialogue`
- DashScope `qwen3.8-livetranslate-flash-realtime` 客户端/服务端事件文档
- DashScope `qwen3-tts-flash` HTTP API 文档

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `knowledge-assistant-voice`: 新增「双路线可选」与「Pipeline 问答链路」需求。

## Impact

- 引擎：`config.py` 增加 `pipeline` 模式与模式切换；新增 `pipeline.py`、`pipeline_llm.py`、`pipeline_tts.py`；复用 `LiveTranslateRealtimeModel` 做 ASR。
- 后端：consumer 读取 `mode` 查询参数，按模式选择 `RealtimeVoiceSession` 或 `PipelineVoiceSession`；WS 白名单不新增消息类型。
- 前端：`useVoiceSession.start(mode)`、路线选择器、模式文案；设备选择器保留。
- 配置：`.env.example` 增加 pipeline 的 LLM/TTS/音色配置。
- 测试：模式选择、TTS WAV 转 PCM、pipeline 事件与 DeepSeek/ TTS 的真实链路。
