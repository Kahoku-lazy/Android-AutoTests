## Why

仪表盘、任务清单和小时表各自计价，同一笔消耗会得到三个费用；未登记模型还会被记成「已计价、费用 0」。平台需要一本逐次账和一条通用公式，之后换单价、倍率或汇率只改基数。

## What Changes

- 每次模型调用结束只写一次 `ai_usage_records`。仪表盘与任务清单只汇总这本账，不再各自调用价目表。
- 计价公式固定为：未命中输入、缓存命中、输出、字符数分别乘对应单价，再乘高峰倍率，再按该模型原币种折成人民币。单价、倍率、长上下文门槛、汇率和模型名映射都是基数。
- 基数按模型名选择，不按厂商名选择。没有基数的调用只记 token，状态为未计价，费用不进合计。
- 高峰按该次调用的起点判断，不再按任务结束时刻整段计价。
- **BREAKING** 仪表盘「DeepSeek 账单」改为平台全部已入账模型的消耗；`task_usage_hourly` 退出账单与趋势。
- **BREAKING** 任务清单费用改为该任务逐次账的合计，字段不再表示「仅 DeepSeek」。
- 展示层提供人民币 / 美元一键切换。库存金额保持人民币 8 位，切换不回写费用。
- 试看基数：`grok-4.6` / `grok-4.7` 用 xAI 官方美元价与 20 万 token 分档；`deepseek-v4.1-flash` 映射到 `deepseek-flash`；`qwen3.5-omni-plus-realtime` 暂用北京音频单价。这些基数可替换，不改变公式。
- 历史三套费用不重算、不合并。切换点之前的小时表与任务行费用标为归档。

## 关联文档

PRD-平台总需求。本次只收口其中「任务事件与费用可回看、仪表盘展示模型费用」；不新增独立 PRD 编号。

## Capabilities

### New Capabilities

- `platform-usage-billing`: 平台逐次用量的唯一入账、通用计价公式、基数表、人民币库存与展示币种切换。

### Modified Capabilities

- `model-usage-ledger`: 账本成为仪表盘与任务费用的唯一汇总源；补齐原币种、汇率与基数快照；未知模型不得记为已计价。
- `dashboard-ai-usage`: 账单、近 7 日与今日逐小时改为读账本全模型，不再读小时表，不再把合计标成 DeepSeek。
- `agent-task-event-store`: 任务费用改为按执行 ID 汇总逐次账；小时表不再参与账单。
- `agent-role-billing`: 实验角色的 4 位 DeepSeek 展示口径保持不变；平台入账不再复用「非 DeepSeek 三项为 0」这条规则。

## Impact

- 后端：`backend/apps/usage_ledger/`、`backend/apps/dashboard/`、`backend/apps/task_list/`。任务收口不再调用 `price_usage`。
- 引擎：`engines/backend_bridge/` 继续只交逐次用量，不写库、不新增价目副本。
- 前端：仪表盘 AI 用量区、任务清单费用列、对应 API 字段与测试。
- 数据：不新建用量表，不迁移历史金额。`task_usage_hourly` 停止作为账单源，表本身本变更不删除。
- 测试：账本入账、仪表盘聚合、任务费用汇总、币种展示；不跑全量回归。
