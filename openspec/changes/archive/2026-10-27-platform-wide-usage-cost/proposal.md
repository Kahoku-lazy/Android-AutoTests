# 平台用量与费用按全平台统计并自动刷新

## Why

仪表盘的用量与费用目前按「当前用户可见智能体」过滤小时用量。Agent-02（家电用例编写）这类新智能体只要不在查看者的可见集合里（或用量行的 `agent_id` 为 0），它的 token 与费用就不进「今日 Token 与费用」「每日 DeepSeek 费用」「当天费用」；平台的真实花费被低估。

另外，仪表盘只在进入页面时取一次数，之后只有手动「刷新」或跨零点才更新。一次任务在页面打开之后才开始烧 token 时，图表会一直停在 0，看起来像「这个模型没被统计」。

平台用量与费用是对全平台模型调用的计量，不应随查看者的智能体可见范围变化；当日曲线也应随时间推进自动跟进。

## What Changes

- 后端 `ai_usage_stats` / `ai_daily_series` / `ai_today_usage_slots` 的 token、缓存命中与费用合计改为统计 `task_usage_hourly` 全表，不再按可见智能体过滤；`agent_id = 0` 的用量行同样计入。
- `ai_usage.agents` 仍是「每个可见智能体一份」的拆分，保持不变；平台合计与拆分之和可以不等（不可见智能体只进合计）。
- 任务数量、任务结果、活动流仍按可见任务/智能体口径，不改。
- 前端新增 30 秒静默轮询：页面可见时自动刷新统计数据；页面隐藏时暂停；重新可见时立即刷新一次；卸载时清理定时器。静默刷新不点亮「刷新」按钮的 loading。
- 更新 `dashboard-ai-usage` 与 `dashboard-trend-charts` 两份规格。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `dashboard-ai-usage`：用量与费用合计从「当前用户可见智能体」改为「平台全部小时用量」。
- `dashboard-trend-charts`：仪表盘统计在页面可见期间每 30 秒自动刷新，当日折线随用量推进。

## Impact

- 后端：`backend/apps/dashboard/ai_usage.py`（查询口径与注释）。
- 前端：`frontend/src/modules/dashboard/composables/useDashboardStats.ts`（静默刷新）、新增 `composables/useDashboardAutoRefresh.ts`、`DashboardView.logic.ts`（接线）。
- 测试：`tests/graybox/unit/test_dashboard_platform_usage.py`（新增）、`frontend/tests/dashboard/p1/dashboardAutoRefresh.spec.ts`（新增）、`useDashboardStats.spec.ts`（补静默刷新）。
- 无数据库迁移，无接口字段变更（响应结构不变，仅数值口径变化）。
