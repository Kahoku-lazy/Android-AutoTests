## ADDED Requirements

### Requirement: 语音模型 Token 用量记录

系统 SHALL 在对话日志中记录每次语音模型调用的 token 用量：

- `omni`：消费 AgentScope `ModelCallEndEvent`，记录 `input_tokens`、`output_tokens`、`cache_input_tokens`、`cache_creation_input_tokens`。
- `pipeline`：记录 DeepSeek `ChatResponse.usage`；ASR 的 `ResponseDoneEvent` 有 token 时也记录。
- `session_end` MUST 带上本次会话的 token 汇总。

记录 MUST 写入 `logs/knowledge_assistant/YYYY-MM-DD.jsonl` 的 `model_usage` 事件，不向前端暴露密钥。

#### Scenario: Omni 记录每次模型调用

- **WHEN** Omni 完成一次模型回复
- **THEN** JSONL 出现 `model_usage` 事件
- **AND** 包含 input/output tokens
- **AND** `session_end` 包含汇总

#### Scenario: Pipeline 记录 DeepSeek 用量

- **WHEN** Pipeline 完成一次 DeepSeek 回答
- **THEN** JSONL 出现 `model_usage` 事件，`provider="deepseek"`
- **AND** 包含 input/output tokens
- **AND** `session_end` 包含汇总

#### Scenario: 没有 usage 字段

- **WHEN** 模型返回没有 usage
- **THEN** 不写伪造的 0 值事件
- **AND** 会话正常结束
