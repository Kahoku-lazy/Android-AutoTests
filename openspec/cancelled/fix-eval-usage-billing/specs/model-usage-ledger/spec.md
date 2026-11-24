# model-usage-ledger Delta

## ADDED Requirements

### Requirement: 逐次模型归属优先

账行的 `model` MUST 取自该次调用自身的用量记录；运行级（run 级）模型名 MUST 仅在逐次记录缺失模型时作兜底。双角色/双模型运行中，各账行 MUST 保留各自实际使用的模型并按各自价目计价，MUST NOT 被运行级单一模型覆盖。

#### Scenario: 双模型任务各行其价

- **WHEN** 一次任务运行中执行者用模型 A、验收者用模型 B，逐次用量各带其模型名
- **THEN** 账本中执行者账行 model=A、按 A 价目计价，验收者账行 model=B、按 B 价目计价
- **AND** 任务费用合计与账本合计一致，不分叉

#### Scenario: 逐次缺失时运行级兜底

- **WHEN** 某条逐次用量记录未携带模型名，运行级模型名为 A
- **THEN** 该账行 model=A