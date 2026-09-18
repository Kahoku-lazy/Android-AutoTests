## Why

仪表盘「趋势数据」第一行（柱状图 +「任务执行结果」）仍绑定已下线的执行引擎，接口恒返回全 0 / 空列表。平台小助手任务卡片（`AITask` / `/ai/agent-tasks`）才是真实任务源。助手页任务卡同时堆了目标全文、设备、时间、结果摘要和删除，用户只要标题与详情入口。

## What Changes

- 仪表盘 `charts.execution` 改为近 12 日平台小助手任务卡按 `created_at` 分日的成功/失败柱（不再写死零）
- `execution_summary` / `recent_tasks` 改为同一批 `AITask` 的成功失败计数与最近卡片
- 「任务执行结果」空态与点击跳转到平台小助手任务详情，不再指向报告/执行引擎
- 助手页任务卡仅保留标题与「详情」；筛选、分组、新建、调试清空仍在区块头
- **BREAKING**：无 HTTP 路径变更；`recent_tasks` 条目语义从用例执行为助手任务卡；点击从 `/reports` 改为 `/ai-assistant/tasks/:id`

## 关联文档

- 仪表盘聚合：`apps/dashboard/AGENTS.md`（只读跨 App Model）
- 任务列表契约：`frontend/src/modules/ai-assistant/api/tasks.ts` → `GET /ai/agent-tasks`
- 无单独 PRD 编号；属仪表盘口径替换 + 助手卡展示收敛

## Capabilities

### New Capabilities

- `dashboard-agent-tasks`：仪表盘趋势第一行与助手任务卡展示口径（`AITask`）

### Modified Capabilities

（无既有主 spec）

## Impact

- 后端：`apps/dashboard/views.py`（及必要时 `ai_usage.py` 只读查询）
- 前端：`dashboard` 的 `TrendBarChart` / `TaskResultPanel` / stats 映射；`ai-assistant/TaskBoard.vue`
- 测试：dashboard 聚合与 TaskBoard 展示
- 不影响：Token/费用图、KPI 入口卡、任务详情页、删除/清空 API
