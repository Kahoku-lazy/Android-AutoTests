## Context

现有 `RealtimeVoiceSession` 把音频交给 `RealtimeAgent`，由实时模型同时完成 ASR、回答与 TTS。Pipeline 路线需要把这三步拆开，并让前端按连接选择。`WebSocketAudioTransport` 已提供上行音频、下行 PCM、打断与播放进度，可复用。

## Goals / Non-Goals

**Goals:**

- 前端两条路线按会话选择，默认 Omni。
- Pipeline 支持流式文字回答、TTS 音频、多轮上下文、打断、日志。
- 不改现有 Omni 链路的默认行为。

**Non-Goals:**

- 不做 RAG/平台知识检索；Pipeline 仍是由 DeepSeek 自由回答。
- 不把 livetranslate 当作文本 TTS；它不支持文本输入。
- 不新增 WS 控制消息类型；路线通过握手 query `mode` 传递。

## Decisions

### 1. 新会话类，不把 Pipeline 塞进 RealtimeAgent

`PipelineVoiceSession` 自己消费 ASR 事件，调用 DeepSeek/TTS，并复用 `WebSocketAudioTransport`。`RealtimeVoiceSession` 保持 Omni/LiveTranslate 原逻辑。

### 2. ASR 只取源语转写

`LiveTranslateRealtimeModel` 以 `output_modalities=["text"]`、目标语种 `en` 启动；Pipeline 只处理 `InputTranscriptionEvent`，忽略 `TranscriptDeltaEvent` / `AudioDeltaEvent` / `Response*`。翻译文本不进入 UI 或 DeepSeek。

### 3. DeepSeek 流式 + 本地历史

`pipeline_llm.py` 用 `DeepSeekChatModel(stream=True, thinking_enable=False)`。每轮把 `system + 最近 N 轮 + 当前用户` 送入，累加模型返回的文本；`chunk.content` 是累计文本，按前缀差算增量。

### 4. TTS 用 Qwen-TTS，非 livetranslate

`qwen3.8-livetranslate` 输入模态仅 Audio/Image，`response.create` 会返回非法事件；不能合成任意文本。TTS 使用 `qwen3-tts-flash` HTTP 非流式接口，返回 24kHz WAV；服务端解析为 PCM16 单声道，按 `audio_item` + 二进制帧下发。

### 5. 路由通过握手 query 传递

`/ws/knowledge-assistant/?token=...&mode=omni|pipeline`。consumer 只读取一次，`select_mode()` 校验并替换模型/音色；不改 WS 消息白名单。

## 模块防火墙自检

- Pipeline 代码全部在 `engines/agents/realtime_vocie/`；不 import 后端 App。
- 后端 consumer 只选择会话类，不实现 DeepSeek/TTS 细节。
- 前端只增加路线选择与 `mode` 参数，不直连模型。
- 无数据库、无新 WS 通道。

## Risks / Trade-offs

- [TTS 延迟] → 非流式 Qwen-TTS 首包约 1–3 秒；先上文字，再播音频。
- [TTS 600 字符上限] → 按句子切分多段合成，拼接 PCM。
- [DeepSeek 无平台知识] → 自由回答；需要准确时后续接 RAG/工具。
- [Pipeline ASR 仍依赖服务端 VAD] → 与现有 livetranslate 一致；麦克风问题单独修。
- [前端两条路线的模型标签不同] → ready 事件返回实际 `model`/`voice`，页面按 ready 显示。
