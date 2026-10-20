## Why

仪表盘上的 Token 和费用还在按任务表重算，和已经落库的小时用量对不上。需要让 AI 用量卡片直接读库，并把一个智能体的缓存命中、输入、输出和总费用合成一份。

## What Changes

- 仪表盘 AI 用量的输入、输出、缓存命中和 DeepSeek 费用改为按小时用量合计，今日按统计日，不再用任务上的 token 列或四位小数重算。
- 任务数量仍按当前用户可见任务计数。平均每任务 Token 用上述合计除以任务数。
- 每个可见智能体多一张卡：缓存命中、输入、输出、总费用。同一智能体跨角色、跨模型加总，不拆开。总费用显示小数点后 8 位。没有用量的可见智能体仍出现，四项为 0。
- 近 12 日的 Token 与费用曲线与卡片同一来源，按统计日合计。
- **BREAKING**：`ai_usage` 增加 `agents`。统计接口里的对话计数字段不再作为本区块口径；本区块使用任务数与每任务平均 Token。

## 关联文档

- PRD-01 仪表盘
- PRD-08 AI 助手

## Capabilities

### New Capabilities

### Modified Capabilities

- `dashboard-ai-usage`: 用量卡片与曲线改读小时用量；每个可见智能体一张整份合计卡

## Impact

- `apps/dashboard/ai_usage.py`：只读聚合，不写库
- `frontend/src/modules/dashboard/index.vue`：AI 用量章节下的智能体卡
- `frontend/src/shared/types/dashboard.ts`、`frontend/src/modules/dashboard/composables/useDashboardStats.ts`
- 测试：`tests/api/test_dashboard_agent_usage.py`
- 角色计费函数与任务卡费用不改
