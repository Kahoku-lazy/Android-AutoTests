# assistant-live-eval Delta

## MODIFIED Requirements

### Requirement: 评测用量按次入账且失败不阻断

评测中的每次模型调用 MUST 单独入账，来源标签 MUST 与知识库评测区分。入账 MUST 携带该次调用的真实 token 用量与模型名，MUST NOT 以 0 token 占位入账真实发生的模型调用。重复提交同一轮次 MUST NOT 使金额翻倍。入账失败 MUST 只记录日志，MUST NOT 阻断评测或发布判定。

#### Scenario: 入账失败仍给出过程

- **WHEN** 一次模型调用的入账失败
- **THEN** 评测继续
- **AND** 已完成样本的过程仍可查看

#### Scenario: 真模型调用按真实 token 入账

- **WHEN** 评测探针完成一轮真模型调用并产生用量
- **THEN** 对应账行的 input_tokens / output_tokens 为该次调用的真实值（非 0 占位），model 为该次实际使用的模型名
- **AND** 账行按该模型价目计价

#### Scenario: 重复轮次不翻倍

- **WHEN** 同一评测轮次被重复提交入账
- **THEN** 账本按 event_id 幂等，金额不翻倍