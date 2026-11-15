## MODIFIED Requirements

### Requirement: Voice 用量图表

仪表盘 SHALL 把 Voice 来源的模型用量展示为「AI 用量」章节「用量趋势」区中的图表，而不是独立卡片或明细表。

- 图表标题 MUST 为「Voice 来源 Token 消耗」。
- 图表 x 轴 MUST 为模型分类：`LLM` / `TTS` / `Realtime` / `Embedding` / `ASR`。
- 图表 MUST 包含两个系列：「当天总用量」与「累计用量」。
- 图表上方 MUST 同时显示当天总用量与累计用量两个汇总值。
- 统计 MUST 只包含 `source=voice` 的记录。
- Token 展示 MUST 使用紧凑单位（K/M）。

#### Scenario: Voice 图表

- **WHEN** 今日存在 Voice 的 LLM 与 Embedding 用量
- **THEN** 「AI 用量」章节的用量趋势区出现「Voice 来源 Token 消耗」
- **AND** x 轴包含 LLM、Embedding
- **AND** 图例包含当天总用量与累计用量

#### Scenario: 来源过滤

- **WHEN** 同时存在 task 与 voice 用量
- **THEN** 图表只统计 voice 记录
- **AND** task 记录不影响图表数值
