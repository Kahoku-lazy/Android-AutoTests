## Why

仪表盘打开要等 12 秒才出数。实测 `/api/dashboard/stats/` 单请求 1.9–3.5s、52 条 SQL，再叠加前端两个 5 秒轮询定时器（同一页面被注册两遍）与无在途保护的 `setInterval`，请求越堆越慢；根因还包括每次统计把含 6.5MB 头像的智能体整行读 4 遍、用量汇总被调用 5 次且每次对每个分类再查一次厂商。

## What Changes

- **前端只保留一个轮询**：删除 `index.vue` 里重复注册的 `useDashboardAutoRefresh`；间隔由 5s 调到 30s（与文件注释一致），并加在途守卫，上一轮没回来就跳过本轮。
- **静默刷新不叠加**：`refreshSilently` 在已有静默请求在跑时直接返回，避免慢请求堆叠。
- **智能体只取一次且不读头像**：仪表盘新增「可见智能体」装载入口，按需列（`id/name/status/owner_id/route_configs/updated_at/model_provider/model_name`）读取，**排除 `avatar` 大字段**；一次请求只加载一次，传给全部统计函数。
- **用量汇总一次算完**：`usage_summary` 改为「一次按 category+provider 分组聚合」，仪表盘用一次批量入口产出 today / total / voice_today / voice_total / recent 五个结果；响应结构保持不变。
- **补回归测试与性能预算**：断言只挂一个轮询、在途跳过、统计接口 SQL 条数上限与首屏耗时目标。
- 不改：接口路径、响应字段、页面视觉、统计口径（仍按全平台小时用量合计）。

## 关联文档

- PRD：`PRD-平台总需求` 一、1.4 产品边界 第 7 条（观测：仪表盘趋势与模型费用）——本变更不改看板内容，只把「看一次要等 12 秒」修到可用。
- 既有规格：`openspec/specs/dashboard-ai-usage`、`dashboard-trend-charts`、`dashboard-activity-timeline`（响应结构与口径保持不变，本变更新增性能约束）。

## Capabilities

### New Capabilities

- `dashboard-load-performance`: 仪表盘的加载与轮询预算——单轮询、不叠加、统计接口查询预算、用量汇总单次聚合。

### Modified Capabilities

（无）

## Impact

- 前端：`frontend/src/modules/dashboard/{index.vue, DashboardView.logic.ts}`、`composables/useDashboardAutoRefresh.ts`、`composables/useDashboardStats.ts`；`frontend/tests/dashboard/p1/dashboardAutoRefresh.spec.ts`。
- 后端：`backend/apps/dashboard/{views.py, ai_usage.py}`、`backend/apps/usage_ledger/api.py`；新增/扩展 `tests/graybox/unit/test_dashboard_*`。
- 接口：响应结构不变；`/api/dashboard/stats/` 与 `/api/dashboard/activities/` 的 SQL 条数与耗时下降。
- 非目标：头像存储改造（6.5MB base64 落库）另开变更；不拆接口、不改页面版式、不做缓存层。
