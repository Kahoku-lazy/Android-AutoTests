## Why

平台目前只有任务侧 `TaskUsageHourly` 聚合，语音侧的 token 仅写 JSONL；没有一张可按厂商、模型分类、时间、UUID 追溯的全局用量账本，仪表盘也无法按 LLM/TTS/Realtime/Embedding/ASR 分类看费用。

## What Changes

- 新增 `backend/apps/usage_ledger` 与表 `ai_usage_records`：
  - 随机 UUID 主键 `usage_id`
  - 唯一 `event_id` 与 `execution_id`，关联事件流与任务/会话
  - `provider` 仅 `deepseek` / `dashscope`
  - `category` 为 `LLM` / `TTS` / `Realtime` / `Embedding` / `ASR`
  - token、字符数、费用、币种、价格快照、时间、来源、metadata
- 官方价目表抽成可编辑 `pricing.json`：DeepSeek 精确价、Sambert 按字符、Qwen-TTS 按字符、Embedding 按 token；未收录模型 `unpriced`。
- 任务事件 `ModelCallEndEvent` 写账本，`event_id=task:<task_id>:<seq>`。
- 语音 `model_usage` / `asr_usage` / `tts_usage` / `embedding_usage` 写账本，事件流与账本共用 `usage_id`。
- 仪表盘新增「模型用量」区：按分类卡片统计 token，卡片副标题显示厂商；最近明细表展示时间/厂商/分类/模型/来源/token/费用。
- 仪表盘统计接口返回 `usage_ledger.today` / `.total` / `.recent`。

## 关联文档

- 已归档 `2026-10-28-add-voice-token-usage`
- 官方价目表来源写在各模型 `pricing.json` 的 `source`

## Capabilities

### New Capabilities

- `model-usage-ledger`: 全局模型用量账本与仪表盘分类统计。

### Modified Capabilities

- `knowledge-assistant-voice`: 语音用量事件写入账本。

## Impact

- 新 App/迁移：`usage_ledger`。
- 任务：`event_store` 写账本。
- 语音：`DialogueLog` 旁路入账；`pipeline` 记录 embedding/TTS/ASR；`events` 记录 Omni。
- 仪表盘：后端汇总 + 前端「模型用量」区。
- 价格表可编辑，不改代码；未收录模型显示 `unpriced`。
