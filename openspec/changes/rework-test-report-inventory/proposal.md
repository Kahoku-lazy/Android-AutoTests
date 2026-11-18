# Proposal: rework-test-report-inventory

## Why

现有测试报告模块把「所有任务」（含未执行/执行中）当报告展示，与事实不符：报告只在执行完成后才生成（SOP 落 `logs/agents/backend_bridge/`，智能体对话落 `logs/agents/assistants/`），且前端 `/reports` 页早已从路由与侧栏摘除、实际不可达。需求方要求把测试报告重建为「已生成报告的台账」，统计报告数量，并在侧栏 BUG单管理 之后恢复入口。

## What Changes

- 重建 `GET /api/reports`：数据源从「可见任务卡」改为「已生成的报告」——SOP 报告取带 `report_run/report_name` 定位的终态任务；智能体报告取带 `report_id` 的助手消息（仅正常完成的轮次）。**BREAKING**：响应从 `{summary, trend, runs}` 任务卡信封改为 `{summary, total, items}` 报告台账信封，移除通过率与每日趋势。
- 统计口径改为**报告数量**：KPI 三卡 = 报告总数 / SOP 报告数 / 智能体报告数。
- 报告行按来源携带业务身份：SOP 行带**用例名称**（`case_identity` 冻结身份口径，与 BUG 单一致）与**关联任务 ID**；智能体行带**助手 ID 与名称**。
- 未执行、执行中、取消、中断的任务/轮次 MUST NOT 进入报告列表（由「完成时才登记报告定位」的既有机制天然保证，不新增过滤逻辑）。
- 查看报告复用两条现有读取通道，不新增读取端点：SOP 走 `GET /api/ai/agent-reports/{run}/{name}/`；智能体走对话栏日志一次性 ticket 通道。
- 侧栏「AI任务」分组新增「测试报告」入口，位于 BUG单管理 之后，四项依次为：任务清单、用例管理、BUG单管理、测试报告。路由保留 `/reports` 单路由，页面按 Doodle Craft 既有套件重建为报告台账（来源筛选 + 关键字 + 日期）。
- **BREAKING** 退役旧执行引擎遗产：`/api/reports/{filename}` 与 `/api/reports/{filename}/content`（csv/md 文件端点）、`rg_reports` / `rg_report_templates` 死表、`ReportGenerator` / `save_report` 死代码、`task_list/task_reports.py` 旧聚合（`build_report_list` 被替换，`build_task_flow` / `report_cache_meta` 全仓无调用方）。
- 退役孤儿前端模块 `agent-reports`（路由未挂载、所调列表接口后端不存在）及其测试。
- 对齐受牵连的旧规格表述：`task-list-module` 的详情报告/报告行点击条款（详情报告端点已随 retire-engines-agents 下线，规格未同步）、`task-execution-lifecycle` 的报告通过/失败与「已中断」筛选条款、`frontend-l3-content-block` 的 `/reports` 图表分区场景。

## 关联文档

无关联 PRD 编号：本变更为需求方直接提出的需求变更（2026-11-18，侧栏位置 + 报告台账口径），现有 PRD 中「测试报告」仅为观测面概述、无编号条目；需求口径以本提案与 delta 规格为准。

## Capabilities

### New Capabilities

（无——报告台账语义落在现有 `report-ai-task-list` 能力内改写，不新增能力路径。）

### Modified Capabilities

- `report-ai-task-list`: 列表数据源、KPI 口径、行字段、筛选方式、行点击行为整体改写为报告台账；旧文件下载/查看端点需求移除；单路由约束保留。
- `frontend-sidebar-nav`: 「AI任务分组提供 BUG 单管理入口」的分组顺序改为 任务清单/用例管理/BUG单管理/测试报告；新增「测试报告入口」需求（路径、模块色、图标登记、折叠态）。
- `ai-task-list`: 「Sidebar AI task group exposes task list first」的侧栏顺序与路径集合同步为四项。
- `task-execution-lifecycle`: 「中断不计入通过与失败」移除测试报告汇总/趋势口径（报告不再统计任务通过/失败）；「中断状态在界面上可见」移除测试报告列表与「已中断」筛选条款（中断任务不产生报告）。
- `task-list-module`: 详情报告条款对齐已下线事实；「测试报告列表行点击进 `/tasks/:id`」改为「报告行打开对应报告文件」。
- `frontend-l3-content-block`: 「Nested composition is bounded」的 `/reports` 分区场景从「数据图表 + 测试报告」改为「报告概览（KPI）+ 测试报告（表格）」。

## Impact

- **后端**：`backend/apps/report_generator/`（views 重写、新增只读聚合模块、models/service/api 死代码与迁移退役）；`backend/apps/task_list/task_reports.py` 退役（`case_identity.py` 保留复用）。跨 App 只读 `task_list.Task` 与 `ai_assistant` 三张 Model（bug_manager 已有 `case_identity` 复用先例），不写库、不 import service/views。
- **引擎**：`engines/` 零改动——报告生成与落盘路径（`REPORT_ROOT` / `ASSISTANT_LOG_ROOT`）维持现状。
- **前端**：`modules/report-generator/` 重建并挂回 `router.ts`；`shared/components/sidebarNavConfig.ts` 增项；`modules/agent-reports/` 退役；查看报告复用 `task-list/api/tasks.ts` 的 `fetchTaskReport` 与 `ai-assistant/api/assistants.ts` 的 `issueLogTicket/threadLogUrl`。
- **API 契约**：`GET /api/reports` 响应结构破坏性变更（前端同批切换，无外部消费方）；`/api/reports/{filename}*` 两端点移除后返回 404。`platform-load-budget` 的扫描上限（≤1000）与返回上限（≤500）约束继续适用，不改该规格。
- **测试**：新增后端报告台账单测/接口测（`tests/report/`）与前端 report-generator 测试重写；退役 `frontend/tests/agent-reports/`；侧栏导航测试更新顺序断言。
- **文档**：`report_generator` 与 `report-generator` 前后端 AGENTS.md 的契约段随实现同步（实现阶段执行）。
