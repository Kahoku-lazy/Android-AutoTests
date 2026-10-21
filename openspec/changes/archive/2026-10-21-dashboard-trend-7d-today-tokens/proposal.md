## Why

「趋势与动态」的三张图现在铺满 12 天，最近两天以外的柱子几乎全是 0，横轴被无效日期占满，用户看不出「这一周花了多少」；同时「今天的用量走到哪了」只能靠两张按天的图去猜。把横轴收成一周，再补一张按 4 小时切分的当日用量折线（token + 费用），才能同时回答「这周」和「今天此刻」。

## What Changes

- 三张统计图（助手任务卡 / 每日 Token 用量 / 每日 DeepSeek 费用）横轴由近 12 天收为**近 7 天（含当天）**，标签仍为 `MM/DD`。
- 统计接口 `charts` 新增 `today_usage`：当天按 4 小时切分的用量序列，含 token 与费用两条。
  - `labels` 固定 7 个刻度：`00:00`、`04:00`、`08:00`、`12:00`、`16:00`、`20:00`、`24:00`。
  - `tokens` 等长 7 项：首项（`00:00`）为 `null`，表示当天起点没有前序 4 小时窗口；其余 6 项为对应 4 小时窗口内「输入 token + 输出 token」的消耗量（不是累计值）。
  - `cost` 等长 7 项：同样的分桶规则，值为该窗口的 DeepSeek 费用（元，8 位小数），首项同为 `null`。
- 「趋势与动态」新增一张整行宽度的「今日 Token 与费用（每 4 小时）」**折线图**卡，位于「每日 Token 用量 / 每日 DeepSeek 费用」那一行之后；token 走左轴、费用走右轴，两条折线。
- 该卡 MUST NOT 画缓存命中线。
- 接口文档与两份既有 spec 的「近 12 日」条款同步为「近 7 日」。
- 不新增数据表、不迁移、不改既有图表的数据字段名；**非 BREAKING**。

## 关联文档

- PRD-01 仪表盘（趋势与动态区块的图表口径）

## Capabilities

### New Capabilities

- `dashboard-trend-charts`: 「趋势与动态」内三张柱状图与新增折线图的横轴口径、卡片位置、折线形态（token + 费用双轴）与空态。

### Modified Capabilities

- `dashboard-ai-usage`: 「仪表盘提供 AI 用量统计接口」中「近 12 日」的 Token/费用曲线口径改为近 7 日；新增一天内 4 小时槽返回当天 token 与费用的要求。
- `dashboard-agent-tasks`: 「Dashboard execution chart uses agent task cards」中近 12 个自然日改为近 7 个自然日。

## Impact

- 后端：`apps/dashboard/ai_usage.py`（默认 `days` 12→7，新增当日 4h 槽聚合）、`apps/dashboard/views.py`（`charts` 增 `today_usage`）
- 前端：`frontend/src/shared/types/dashboard.ts`、`modules/dashboard/composables/useDashboardStats.ts`、`DashboardView.logic.ts`、`index.vue`、新增 `components/TodayUsageChart.vue`
- 测试：`tests/graybox/unit/test_dashboard_agent_tasks.py` 与新增当日槽单测、`frontend/tests/dashboard/p1/DashboardView.logic.spec.ts`
- 文档：`dev_docs/DEV_TEST/接口文档/API-仪表盘.md`
- 不涉及：数据表、迁移、路由、鉴权
