## MODIFIED Requirements

### Requirement: 前端可选双路线

系统 SHALL 在前端提供两条按会话可选的语音路线：

1. `omni`：`qwen3.5-omni-plus-realtime` 直连，音色 `Tina`。
2. `pipeline`：`livetranslate` ASR + `deepseek-flash` 回答 + `sambert-zhichu-v1`（知厨）播报。

默认路线 MUST 为 `omni`。用户切换路线后，WS 连接 MUST 携带 `mode=omni` 或 `mode=pipeline`；后端 MUST 按该连接选择对应会话实现，不得影响其他连接。页面「模式」行 MUST 显示当前路线。未开始会话时，页面「模型」行 MUST 按当前所选路线显示：`omni` 显示后端默认模型，`pipeline` 显示 pipeline 的 LLM/TTS 模型与音色；会话开始后 MUST 以 `ready` 事件返回的实际 `model`/`voice` 为准。

#### Scenario: 默认 Omni 直连

- **WHEN** 用户只配置 `DASHSCOPE_API_KEY` 并打开页面
- **THEN** 路线默认为 `omni`
- **AND** 模型为 `qwen3.5-omni-plus-realtime`、音色 `Tina`

#### Scenario: 选择 Pipeline

- **WHEN** 用户选择「ASR + DeepSeek Flash + TTS」并开始对话
- **THEN** WS 连接携带 `mode=pipeline`
- **AND** 页面模式显示 ASR + DeepSeek + TTS
- **AND** 模型行显示 `deepseek-flash + sambert-zhichu-v1` 与「知厨」
- **AND** 另一个 Omni 连接不受影响

#### Scenario: 非法 mode

- **WHEN** WS 携带不支持的 mode
- **THEN** 连接返回可读错误并关闭
- **AND** 不创建任何模型会话
