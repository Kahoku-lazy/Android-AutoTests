## Context

见 `proposal.md` Why。`apps/report_generator/views.py` 的 `list_reports` 在卸执行引擎后写死空 `runs/summary/trend`。仪表盘已用 `AITask` + `filter_agents_for_user` 做成功/失败分日统计（`apps/dashboard/ai_usage.py`），报告 App **不得** import dashboard 内部模块。`/reports/*` 保持平铺信封。前端 `index.vue` 的 `openReport` / `openCaseBreakdown` 仍指向已 404 的详情。

## Goals / Non-Goals

**Goals:**
- 在 `report_generator` 内实现只读查询，填充现有 `GET /api/reports`
- 前端列表列与 KPI 交互对齐任务卡，去掉跳转
- 查询逻辑若撑大 `views.py`，拆到本 App 只读辅助文件，不进 `ai_assistant` 写路径

**Non-Goals:**
- 不复活 Run/用例分解/任务视角报告页
- 不抽仪表盘公共聚合库、不改助手看板契约
- 不把 `/reports/*` 改成 `{status, data}` 信封

## Decisions

1. **数据出口仍是 `GET /api/reports`**  
   报告前端继续只打本模块 `api.ts`。备选（前端直打 `/ai/agent-tasks`）打破模块 HTTP 出口，否决。

2. **可见性与成功口径对齐仪表盘，但不复用其文件**  
   读 `AITask` Model；调用 `apps.ai_assistant.api.filter_agents_for_user` 与 `resolve_assistant_name`（公开 api，只读）。成功集合 `completed`/`success`，失败 `failed`。若 `filter_agents_for_user` 未进 `__all__`，本次补进，避免跨模块走未导出符号。

3. **行 DTO（`runs[]`）**  
   - `run_id`：任务主键字符串（兼容现筛选项 `run_id`，避免前端筛参大改）  
   - `device_serial`：展示用（label 优先）  
   - `task_name`：`title`  
   - `creator`：`assistant_name`  
   - `status` / `duration` / `started_at`  
   去掉 `case_count`/`passed`/`failed`/`rate`。`summary` 保留 `total_runs`/`total_pass`/`total_fail`/`pass_rate`；`total_iterations` 置 0 或与 `total_runs` 相同均可，前端去掉「迭代」展示。`bug_summary` 仍 `{}`。

4. **趋势**  
   沿用现 `chart_range` 7/30/90 与 `_empty_trend` 日期轴；按任务 `created_at` 分日累加 pass/fail（与仪表盘分桶字段一致，天数用报告页的 range）。`trend.rate[i]` = 当日 pass/(pass+fail) 或 0。

5. **筛选**  
   继续 `start_date`/`end_date`/`run_id`/`task_name`/`device_serial`/`creator`。日期滤 `created_at`；`run_id` 精确匹配任务 id；名称/设备/助手名包含匹配。设备同时匹配 `device_label` 与 `device_serial`。

6. **耗时**  
   后端给出已格式化字符串：有 `started_at` 与 `finished_at` 则算差；缺一则 `—`。

7. **前端**  
   删除 `openReport`、`openCaseBreakdown` 及 KPI `@click`。`run_id` 单元格改为 `<code>` 无 `<a>`。列定义只留任务 ID/设备/任务名称/创建人/状态/耗时/时间。页头 subtitle 与空态改文案。不改 `ReportDetail.vue` / `CaseBreakdown.vue` / `TaskReport.vue`（路由可留，本变更不修）。

**备选驳回：** 把聚合放进 `ai_assistant.api` 新 list 函数——报告读路径不必扩写库 api；仪表盘已有自己的统计，强行共用会扩大本次 diff。

## 模块防火墙自检

- 跨 App：只读 `AITask`；只调 `ai_assistant.api` 的只读函数；不 import dashboard/`ai_assistant` 的 service/views
- 无 INSERT/UPDATE/DELETE
- 前端仍经 `report-generator/api.ts` → `/api/reports`，不直打助手任务接口
- `views.py` 只分发；查询堆在本 App 辅助模块（非他 App service）

## Risks / Trade-offs

- [旧书签仍打开 `/reports/:id`] → 保持现有 404 空壳，本变更不修详情（已批准不做）
- [任务很多时全量进内存筛选助手名] → 先 queryset 过滤能下推的字段，助手名在序列化后过滤；量级与看板同级
- [前端仍读 `summary.total_iterations` / 用例 KPI] → 同步改模板，去掉迭代与用例分解入口
- [与仪表盘 12 日 vs 报告 7/30/90] → 有意保持各页自己的 range，口径只对齐成功/失败定义

## Migration Plan

无数据迁移。部署后报告页立刻读现有 `ai_tasks`。回滚：恢复空壳 `list_reports` 与前端列/跳转。

## Open Questions

无。
