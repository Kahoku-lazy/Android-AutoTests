## Why

「趋势与动态」章节现在同时装着任务类图（助手任务卡、任务执行结果）和 AI 用量类图（每日 Token、每日费用、今日逐小时、Voice 来源），而「AI 用量」章节只有账单卡与智能体卡两张快照。同一件事的成本与用量被拆在两个章节里：看「今天花了多少、走了多少 token」要先看 AI 用量卡、再滚到下一章节看曲线，视线来回跳。需求方要求把 AI 用量相关的统计图移到「AI 用量」章节内。

## What Changes

- 把四张 AI 用量类图表从「趋势与动态」移到「AI 用量」章节：
  - 每日 Token 用量
  - 每日 DeepSeek 费用（元）
  - 今日 Token 与费用（逐小时）
  - Voice 来源 Token 消耗
- 「AI 用量」章节结构变为：账单卡 + 智能体用量卡 →「用量趋势」子标题 → 上述四张图。
- 「趋势与动态」章节保留：助手任务卡、任务执行结果、最近动态；不再包含任何 AI 用量图表。
- 图表组件、取数口径、刷新机制、图例与文案全部不变，只改承载章节与排列位置。

## 关联文档

- 需求来源：需求方直接决策的仪表盘信息架构调整（AI 用量图归入「AI 用量」章节）。
- 受影响主 spec：`dashboard-trend-charts`（图表的章节归属与横轴口径）、`dashboard-ai-usage`（新增区块内容要求）、`model-usage-ledger`（Voice 图表的章节归属）。
- 前序变更：`2026-11-11-dashboard-platform-overview-merge`（三章节架构）。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `dashboard-trend-charts`: 三张按日柱状图与今日折线图不再都在「趋势与动态」；今日折线图的相邻位置改为「AI 用量」章节内的按日图之后。
- `dashboard-ai-usage`: 新增「AI 用量区块承载用量趋势图」要求。
- `model-usage-ledger`: Voice 用量图表的承载章节由「趋势与动态」改为「AI 用量」。

## Impact

- 前端：`frontend/src/modules/dashboard/index.vue`（两章节的模板块）、`frontend/src/modules/dashboard/DashboardView.style.css`（章节内趋势区容器）。
- 后端 / 接口：无改动；`ai_usage`、`charts.*`、activity 接口口径不变。
- 测试：`frontend/tests/dashboard/**` 与 `tests/dashboard/**` 均为数据层测试，不涉及图表所属章节，无需改动。
