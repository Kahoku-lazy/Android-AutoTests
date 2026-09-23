## Context

- 仪表盘「测试资产」左栏用写死的 `CASE_BREAKDOWN`（`ui_automation` / `web_automation` / `api_testing` / `storage`）去对 `stats.cases.breakdown`；后端 `_cases_breakdown` 实际按 `TestDefinition.test_type` 的 `app/web/api/func` 计数。键不一致，卡上长期为 0。
- `apps.case_manager.api.list_projects` 已按 `created_by` 返回项目，并带 `case_count`；仪表盘 `GET /api/dashboard/stats/` 已只读聚合、无写操作。
- 动机见 `proposal.md`；可见行为见 `specs/dashboard-case-project-cards/spec.md` 与 `specs/dashboard-chapter-boards/spec.md`。

## Goals / Non-Goals

**Goals:**

- 同一条 stats 响应内给出项目维度 `cases.breakdown`，前端按该数组出卡
- 入口卡 `path` 指向 `/cases/projects/{id}`
- 无项目时空态，不画四张类型卡
- 单测与类型与新 breakdown 形状对齐

**Non-Goals:**

- 不改用例模块创建/删除 API
- 不给仪表盘加 WebSocket 或轮询间隔
- 不改元素定位列、章节钉板结构、其它 KPI
- 不在仪表盘页调用 `GET /cases/projects/`

## Decisions

### 1. 在 stats 内替换 breakdown，不另开端点、不前端拼卡

- **选择**：`_cases_breakdown` 改为调用 `apps.case_manager.api.list_projects(user_id=str(user_id))`，映射为 `{project_id, name, total}`（`total` ← `case_count`）。`cases.total` / `cases.enabled` 仍为各项目 `total` 之和（文档用例无独立 enabled，enabled 与 total 同值，避免前端合计字段空窗）。
- **理由**：规格要求只走既有 stats；`list_projects` 是公开 api，计数与项目列表页同源。
- **备选**：仪表盘并行请求 `/cases/projects/` —— 违反「禁止前端拼卡」且多一次鉴权往返。不采用。
- **备选**：dashboard 自己 `CaseProject.objects` + annotate —— 可读 Model，但会与 `serialize_project` 的 `case_count` 分叉。不采用。

### 2. 前端以 breakdown 数组为卡列表，删除固定 CASE_BREAKDOWN

- **选择**：`v-for` 直接遍历 `stats.cases.breakdown`；`label` 用 `name`，`value` 用 `total`，`path` 为 `` `/cases/projects/${project_id}` ``；色板在 `deep/sage/cream/dust` 上按 index 轮换，图标沿用现有 Layers/Target 一类共享图标即可。
- **理由**：项目是动态集合，不能再按四类型 lookup。
- **备选**：保留类型卡再叠项目卡 —— 与需求冲突。不采用。

### 3. 空态用现有 ErrorState/空文案模式的轻量块，不新建空态组件

- **选择**：无 breakdown 项且非 loading 时，子区内一段说明 + 链到 `/cases`。
- **理由**：只服务一个子区，不新增共享空态组件。

### 4. 同步语义 = 下次 stats 成功

- **选择**：用户建项目后回到 `/dashboard`（`onMounted` `loadData`）或点刷新即看见新卡。
- **理由**：与现网其它 KPI 一致；规格明确不新增实时通道。

## 模块防火墙自检

- 跨 App import：dashboard 只读调用 `apps.case_manager.api.list_projects`（公开 `api.py`）。MUST NOT import `api_projects` / views / serializers。
- 禁止跨 App import service/runner/consumer/state_machine：本设计不引入。
- 写库：本变更无 INSERT/UPDATE/DELETE。
- 前端不直连数据库；仪表盘仍只读 `fetchDashboardStats` / activities。
- 现有 `_user_cases_q` 对 `TestDefinition` 的 Model 只读若被 `_cases_breakdown` 替换后不再需要，则删除该路径，避免两套计数。

## Risks / Trade-offs

- [N+1] `list_projects` 对每个项目 `case_count` 单独 count → 项目量级为人工文档库，可接受；若后续变慢再在 `list_projects` 一次性 annotate，仪表盘跟着受益。
- [未登录 user_id 空] 现网 stats 已用 `_user_id`；无用户时 `list_projects` 应得到空列表、total=0，MUST NOT 用全站项目。
- [前端旧单测仍断言 `ui_automation`] → 任务中同步 `useDashboardStats.spec.ts` 与 `DashboardView.logic.spec.ts`。

## Migration Plan

- 前后端同一变更交付：先改 stats 形状再改前端消费，避免短暂四张 0 卡。
- 回滚：恢复 `_cases_breakdown` 按 `test_type` 与前端 `CASE_BREAKDOWN`；无需数据迁移。
