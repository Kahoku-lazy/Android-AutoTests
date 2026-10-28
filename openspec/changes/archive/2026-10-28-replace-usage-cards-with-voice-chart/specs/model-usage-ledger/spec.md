## REMOVED Requirements

### Requirement: 仪表盘模型用量

**Reason**: 模型用量不再使用独立卡片与明细表，改为趋势区的 Voice 图表。

**Migration**: 使用新增的「Voice 用量图表」要求；账本表与 `usage_summary` 不变。

## ADDED Requirements

### Requirement: Voice 用量图表

仪表盘 SHALL 把 Voice 来源的模型用量展示为「趋势与动态」中的图表，而不是独立卡片或明细表。

- 图表标题 MUST 为「Voice 来源 Token 消耗」。
- 图表 x 轴 MUST 为模型分类：`LLM` / `TTS` / `Realtime` / `Embedding` / `ASR`。
- 图表 MUST 包含两个系列：「当天总用量」与「累计用量」。
- 图表上方 MUST 同时显示当天总用量与累计用量两个汇总值。
- 统计 MUST 只包含 `source=voice` 的记录。
- Token 展示 MUST 使用紧凑单位（K/M）。

#### Scenario: Voice 图表

- **WHEN** 今日存在 Voice 的 LLM 与 Embedding 用量
- **THEN** 趋势区出现「Voice 来源 Token 消耗」
- **AND** x 轴包含 LLM、Embedding
- **AND** 图例包含当天总用量与累计用量

#### Scenario: 来源过滤

- **WHEN** 同时存在 task 与 voice 用量
- **THEN** 图表只统计 voice 记录
- **AND** task 记录不影响图表数值

### Requirement: 用量来源过滤

`usage_summary` SHALL 支持按 `source` 过滤；仪表盘 SHALL 用该能力提供 `voice_today` / `voice_total`。

#### Scenario: 查询 Voice 汇总

- **WHEN** 调用 `usage_summary("today", source="voice")`
- **THEN** 只返回 `source=voice` 的调用、token 与费用
