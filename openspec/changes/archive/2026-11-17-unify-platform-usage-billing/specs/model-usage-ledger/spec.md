## MODIFIED Requirements

### Requirement: 全局模型用量账本

系统 SHALL 提供独立的模型用量明细表 `ai_usage_records`，每次模型调用一条记录，至少包含：

- 随机 UUID `usage_id`（主键）
- 唯一 `event_id` 与 `execution_id`
- `provider`：`deepseek` / `dashscope` / `govee`
- `category`：`LLM` / `TTS` / `Realtime` / `Embedding` / `ASR`
- `model`、`occurred_at`
- `input_tokens` / `output_tokens` / `cache_input_tokens` / `cache_creation_tokens` / `total_tokens` / `characters`
- `cost_input` / `cost_cache` / `cost_output` / `cost_total` / `currency`
- `pricing_status` / `pricing_snapshot` / `metadata`

`currency` MUST 为 `CNY`。`pricing_snapshot` MUST 含本次使用的模型名或映射目标、三项或字符单价、倍率、原币种与入库汇率。`usage_id` MUST 同时写入对应事件流；任务事件、语音 JSONL 与账本 MUST 可通过 `event_id` / `usage_id` 互相追溯。仪表盘平台账单与任务费用 MUST 只汇总本表，MUST NOT 再从小时表或任务行重算。

#### Scenario: 任务调用入账

- **WHEN** 任务产生一次模型调用结束
- **THEN** 账本新增或更新一条记录
- **AND** `event_id` 为 `task:<task_id>:<seq>`
- **AND** `execution_id` 指向任务

#### Scenario: 语音调用入账

- **WHEN** 语音产生 `model_usage` / `asr_usage` / `tts_usage` / `embedding_usage`
- **THEN** JSONL 与账本使用同一个 `usage_id`
- **AND** `execution_id` 指向语音 session

#### Scenario: 费用不可用

- **WHEN** 模型没有基数，也没有可用映射
- **THEN** token 仍记录
- **AND** `cost_total=0` 且 `pricing_status=unpriced`
- **AND** 该行不进入费用合计

### Requirement: 模型分类与厂商

系统 SHALL 按以下分类统计：`LLM`（对话与工具调用）、`TTS`（文本转语音）、`Realtime`（语音到语音）、`Embedding`（向量化）、`ASR`（语音识别）。`provider` 只标识密钥归属：DeepSeek Key → `deepseek`，DashScope Key → `dashscope`，Govee Key → `govee`。出现其他类型时 MUST 新增分类或厂商条目，不得归入错误分类。计价基数 MUST 按模型名选择，MUST NOT 因 `provider=govee` 改用 DeepSeek 价目。

#### Scenario: 分类统计

- **WHEN** 仪表盘查询今日用量
- **THEN** 返回按 LLM/TTS/Realtime/Embedding/ASR 分组的 token 与费用
- **AND** 每组带 provider 拆分

#### Scenario: Govee 网关不按厂商套价

- **WHEN** 一笔调用的密钥归属为 govee，模型名为 `grok-4.7`
- **THEN** 该笔按 `grok-4.7` 的基数计价，不按 DeepSeek 价目计价

## ADDED Requirements

### Requirement: 账本是平台费用的唯一汇总源

仪表盘的平台 token 与费用、任务清单的任务费用 MUST 汇总 `ai_usage_records` 中对应范围的行。汇总费用 MUST 排除 `pricing_status=unpriced` 的行，并同时返回这些行的 token。历史已写入的费用行在基数变更后 MUST NOT 自动改写；只有显式重算才按当前基数重算，并更新快照。

#### Scenario: 未计价行不进费用

- **WHEN** 今日同时有已计价行和未计价行
- **THEN** 平台费用合计只含已计价行
- **AND** 响应另给出未计价 token

#### Scenario: 改基数不改旧账

- **WHEN** 基数表中的某个单价被替换
- **THEN** 替换前已入账行的 `cost_total` 保持不变
