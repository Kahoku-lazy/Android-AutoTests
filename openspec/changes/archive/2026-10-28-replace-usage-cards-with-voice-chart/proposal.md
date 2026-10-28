## Why

模型用量目前是独立卡片 + 明细表，占一整块区域；用户希望把它做成图表放进「趋势与动态」，只关注 Voice 来源，并区分当天总用量与累计用量。

## What Changes

- 移除仪表盘独立「模型用量」卡片/明细表区块。
- 在「趋势与动态」新增「Voice 来源 Token 消耗」图表。
- 图表 x 轴为模型分类（LLM/TTS/Realtime/Embedding/ASR），两个系列：
  - 当天总用量
  - 累计用量
- 图表上方显示两类汇总值。
- `/api/dashboard/stats/` 的 `usage_ledger` 增加 `voice_today` / `voice_total`（`source=voice` 过滤）。
- `usage_summary` 支持 `source` 参数。

## Capabilities

### Modified Capabilities

- `model-usage-ledger`: 模型用量从卡片/表格改为趋势区 Voice 图表。

## Impact

- 前端：移除用量区块与表格样式，新增趋势图表。
- 后端：只增加 source 过滤与两个汇总字段，账本表不变。
