## ADDED Requirements

### Requirement: 前端可选双路线

系统 SHALL 在前端提供两条按会话可选的语音路线：

1. `omni`：`qwen3.5-omni-plus-realtime` 直连，音色 `Tina`。
2. `pipeline`：`livetranslate` ASR + `deepseek-flash` 回答 + `qwen3-tts-flash` 播报。

默认路线 MUST 为 `omni`。用户切换路线后，WS 连接 MUST 携带 `mode=omni` 或 `mode=pipeline`；后端 MUST 按该连接选择对应会话实现，不得影响其他连接。页面「模式」行 MUST 显示当前路线。

#### Scenario: 默认 Omni 直连

- **WHEN** 用户只配置 `DASHSCOPE_API_KEY` 并打开页面
- **THEN** 路线默认为 `omni`
- **AND** 模型为 `qwen3.5-omni-plus-realtime`、音色 `Tina`

#### Scenario: 选择 Pipeline

- **WHEN** 用户选择「ASR + DeepSeek Flash + TTS」并开始对话
- **THEN** WS 连接携带 `mode=pipeline`
- **AND** 页面模式显示 ASR + DeepSeek + TTS
- **AND** 另一个 Omni 连接不受影响

#### Scenario: 非法 mode

- **WHEN** WS 携带不支持的 mode
- **THEN** 连接返回可读错误并关闭
- **AND** 不创建任何模型会话

### Requirement: Pipeline 问答链路

`pipeline` 模式 SHALL 按以下顺序处理一轮语音：

1. 把浏览器上行 PCM 送入 `qwen3.8-livetranslate-flash-realtime`，只消费源语转写结果。
2. 把源语文本送入 `deepseek-flash`，流式得到中文回答。
3. 把回答文本送入 `qwen3-tts-flash`，生成 24kHz PCM16 音频并下发浏览器。
4. 在页面上先显示用户源语转写，再显示助手回答文本，并播放 TTS 音频。

ASR 的翻译输出 MUST NOT 被当作助手回答。TTS 失败时 MUST 保留已生成的文字回答，并给出可读提示。

#### Scenario: 用户问，模型答

- **WHEN** 用户说“设备管理里怎么连接设备”
- **THEN** 页面显示用户源语转写
- **AND** 页面显示 DeepSeek 生成的回答
- **AND** 浏览器播放 Qwen-TTS 生成的语音

#### Scenario: 多轮上下文

- **WHEN** 用户在同一会话里连续问两个相关问题
- **THEN** 第二个回答能引用第一轮的用户/助手文本

#### Scenario: 打断

- **WHEN** 助手正在生成或播报时用户点击「打断」
- **THEN** 当前 DeepSeek/TTS 任务被取消
- **AND** 浏览器播放队列被清空
- **AND** 页面回到聆听状态

#### Scenario: TTS 不可用

- **WHEN** `qwen3-tts-flash` 调用失败
- **THEN** 助手文字回答仍显示并落日志
- **AND** 页面提示语音播报失败
- **AND** 会话不中断
