# model-usage-ledger Specification

## Purpose
TBD - created by archiving change add-model-usage-ledger. Update Purpose after archive.

## Requirements

### Requirement: 全局模型用量账本

系统 SHALL 提供独立的模型用量明细表 `ai_usage_records`，每次模型调用一条记录，至少包含：

- 随机 UUID `usage_id`（主键）
- 唯一 `event_id` 与 `execution_id`
- `provider`：仅 `deepseek` / `dashscope`
- `category`：`LLM` / `TTS` / `Realtime` / `Embedding` / `ASR`
- `model`、`occurred_at`
- `input_tokens` / `output_tokens` / `cache_input_tokens` / `cache_creation_tokens` / `total_tokens` / `characters`
- `cost_input` / `cost_cache` / `cost_output` / `cost_total` / `currency`
- `pricing_status` / `pricing_snapshot` / `metadata`

`usage_id` MUST 同时写入对应事件流；任务事件、语音 JSONL 与账本 MUST 可通过 `event_id` / `usage_id` 互相追溯。

#### Scenario: 任务调用入账

- **WHEN** 任务产生一次 `ModelCallEndEvent`
- **THEN** 账本新增一条记录
- **AND** `event_id=task:<task_id>:<seq>`
- **AND** `execution_id` 指向任务

#### Scenario: 语音调用入账

- **WHEN** 语音产生 `model_usage` / `asr_usage` / `tts_usage` / `embedding_usage`
- **THEN** JSONL 与账本使用同一个 `usage_id`
- **AND** `execution_id` 指向语音 session

#### Scenario: 费用不可用

- **WHEN** 模型不在价目表或价格标记为 unpriced
- **THEN** token 仍记录
- **AND** `cost_total=0` 且 `pricing_status=unpriced`

### Requirement: 模型分类与厂商

系统 SHALL 按以下分类统计：`LLM`（对话与工具调用）、`TTS`（文本转语音）、`Realtime`（语音到语音）、`Embedding`（向量化）、`ASR`（语音识别）。`provider` 按 Key 归属：DeepSeek Key → `deepseek`，DashScope Key → `dashscope`。出现其他类型时 MUST 新增分类条目，不得归入错误分类。

#### Scenario: 分类统计

- **WHEN** 仪表盘查询今日用量
- **THEN** 返回按 LLM/TTS/Realtime/Embedding/ASR 分组的 token 与费用
- **AND** 每组带 provider 拆分

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
