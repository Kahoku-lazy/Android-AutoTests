## Context

任务链路已有 `TaskEvent`（含 token/费用）和 `TaskUsageHourly`（小时聚合），但只覆盖任务；语音链路只有 JSONL。新账本作为明细真相源，小时聚合保留用于旧图表。

## Decisions

### 1. 表与 UUID

`ModelUsage.usage_id` 为 UUID 主键；`event_id` 唯一用于幂等。任务事件把 UUID 写进 `TaskEvent.payload`，语音 JSONL 直接写 `usage_id`，两边同值。

### 2. 价格表配置化

`pricing.json` 存官方单价与 `pricing_status`；未收录模型 `unpriced`。DeepSeek 复用 `DeepSeekBilling`（高峰倍率、缓存），DashScope 按 `input_per_million` / `per_10k_chars`。金额统一 CNY，保留 8 位。

### 3. 写入路径

- 任务：`TaskEventSink._add_usage` 在事件落库后写账本，`event_id=task:<id>:<seq>`。
- 语音：`DialogueLog` 生成 `usage_id` 并旁路入账；ORM 写入通过 `run_in_executor` 避免 async consumer 同步 DB 限制。
- 嵌入：包装 `DashScopeEmbeddingModel` 抓 `EmbeddingResponse.usage.tokens`。

### 4. 仪表盘

`/api/dashboard/stats/` 增加 `usage_ledger`；前端新增「模型用量」卡片 + 明细表，不改旧 AI 用量卡。

## Risks

- DashScope 真实价目随地域/模型变化：`pricing.json` 可覆盖，未知为 unpriced。
- 语音 TTS 在用户提前结束时可能来不及入账；不影响文字回答与已有 token。
- 旧任务事件没有 `usage_id`：只对新事件生效，不回填。
