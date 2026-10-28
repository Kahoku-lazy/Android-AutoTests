## ADDED Requirements

### Requirement: Pipeline 回答链路由 Agent 承担
`pipeline` 路线的回答与语音合成分工 MUST 由 Agent 承担：文本来自 Agent 的文本增量事件，语音来自语音合成中间件产出的音频块。ASR 与传输层 MUST NOT 改变。语音合成适配器 MUST 复用现有 Sambert / Qwen 引擎与音色，MUST NOT 改动默认音色。

#### Scenario: 一轮回答同时产出文本与音频
- **WHEN** 用户在 pipeline 路线说一句话，模型正常返回
- **THEN** 前端按顺序收到 `reply_start`、若干 `transcript_delta`、`transcript_final`、`reply_end`，并在 `reply_end` 之前收到一整段 `audio`

#### Scenario: 音色不变
- **WHEN** 默认配置（sambert / 知厨）下跑一轮回答
- **THEN** 播报仍使用原音色与采样率，不因改为 Agent 而换声音

### Requirement: 音频整段发送
语音合成中间件逐块产出的音频 MUST 由回答器累积成一段 PCM，在 `reply_end` 之前一次性发送；前端音频帧格式 MUST 保持不变。

#### Scenario: 多块音频合并
- **WHEN** 中间件分三次产出三段音频
- **THEN** 前端只收到一次 `audio` 帧，内容是三段按序拼接

### Requirement: 用量口径不变
`model_usage` MUST 取本轮 `ModelCallEndEvent` 的输入、输出与两项缓存 token；`tts_usage` MUST 仍按本轮总字符数记一条，MUST NOT 因改为逐块合成而改变计费口径。

#### Scenario: 一轮回答的用量
- **WHEN** 一轮回答结束
- **THEN** 日志里 `model_usage` 一条（四个 token 字段），`tts_usage` 一条（字符数为整轮文本长度）

### Requirement: 回答链路可回退
回答链路 MUST 由 `KNOWLEDGE_ASSISTANT_PIPELINE_ENGINE` 选择：`agent`（默认）走 Agent，`legacy` 走原直连实现。取值非法时 MUST 拒绝启动并给出可读原因。

#### Scenario: 回退到旧实现
- **WHEN** 配置 `KNOWLEDGE_ASSISTANT_PIPELINE_ENGINE=legacy`
- **THEN** 会话按原直连模型 + 单独合成的方式工作

#### Scenario: 非法取值
- **WHEN** 配置成其它值
- **THEN** 启动失败，报错信息点名该环境变量与可选值
