## ADDED Requirements

### Requirement: 调用方式可选且默认实时翻译模型

系统 SHALL 支持两种实时语音调用方式：`livetranslate`（实时翻译）与 `omni`（实时对话）。默认调用方式 MUST 为 `livetranslate`，默认模型 MUST 为 `qwen3.8-livetranslate-flash-realtime`。用户 SHALL 能通过环境变量 `KNOWLEDGE_ASSISTANT_REALTIME_MODE` 显式选择调用方式，或仅设置 `KNOWLEDGE_ASSISTANT_MODEL` 由模型名推断：包含 `omni` 走 `omni`，否则走 `livetranslate`。调用方式与模型名不匹配时，系统 MUST 拒绝启动并在状态接口返回可读原因。

#### Scenario: 默认使用 livetranslate

- **WHEN** 只配置 `DASHSCOPE_API_KEY`
- **THEN** 状态接口返回 `mode=livetranslate`
- **AND** 模型为 `qwen3.8-livetranslate-flash-realtime`

#### Scenario: 显式回退 omni

- **WHEN** 配置 `KNOWLEDGE_ASSISTANT_REALTIME_MODE=omni` 与 `KNOWLEDGE_ASSISTANT_MODEL=qwen3.5-omni-plus-realtime`
- **THEN** 会话使用原有 `DashScopeRealtimeModel`，不加载实时翻译适配器

#### Scenario: 只配模型名自动推断

- **WHEN** 只配置 `KNOWLEDGE_ASSISTANT_MODEL=qwen3.5-omni-plus-realtime`
- **THEN** 调用方式自动推断为 `omni`

#### Scenario: 模式与模型不匹配

- **WHEN** 配置 `KNOWLEDGE_ASSISTANT_REALTIME_MODE=livetranslate` 且模型为 Omni
- **THEN** 状态接口返回 `ready=false` 与可读原因
- **AND** 不创建模型会话

### Requirement: 实时翻译协议适配

`livetranslate` 模式 SHALL 通过 DashScope Realtime WebSocket 建立会话，并发送 `session.output_modalities`、`session.translation.language`、`session.audio.input.turn_detection=speaker_detection`。源语种转写 SHALL 映射为用户消息；译文 SHALL 从 `response.audio_transcript.delta` 或 `response.text.delta` 映射为助手消息；音频 SHALL 从 `response.audio.delta` 按 24kHz PCM16 播放。会话结束前 SHALL 发送 `session.finish`。

#### Scenario: 中文语音翻译成中文

- **WHEN** 用户说“设备管理里怎么连接设备”，目标语种为 `zh`
- **THEN** 页面出现用户源语转写
- **AND** 助手消息出现中文译文

#### Scenario: 目标语种可配

- **WHEN** 配置 `KNOWLEDGE_ASSISTANT_TRANSLATION_LANGUAGE=en`
- **THEN** `session.translation.language` 为 `en`
- **AND** 助手译文为英文

#### Scenario: 就绪事件暴露调用方式

- **WHEN** WS 会话建立完成
- **THEN** `ready` 事件包含 `mode` 与 `translation_language`
- **AND** 页面「模式」行显示实时翻译或语音问答
