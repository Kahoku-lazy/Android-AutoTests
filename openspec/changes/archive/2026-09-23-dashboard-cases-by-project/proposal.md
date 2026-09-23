## Why

用例管理已改为「按项目组织文档型用例」，但仪表盘「测试资产」里的测试用例区仍按 Android / Web / API / 功能业务四张固定入口卡展示，且前端写死的 `ui_automation` 等键与后端 `app/web/api/func` 对不上，数值长期为 0。现在需要把该区改成与项目列表同源：每个项目一张卡，新建/删除项目后再次打开仪表盘即同步。

## What Changes

- **BREAKING**：`GET /api/dashboard/stats/` 中 `cases.breakdown` 不再按测试类型（`app/web/api/func` 或旧 `ui_automation/...`）拆分，改为当前用户的项目列表（含 0 用例项目）。
- 仪表盘「测试用例」子区去掉 Android / Web / API / 功能业务固定卡；改为按项目渲染 KPI 入口卡（名称 + 用例数），点击进入对应项目工作台。
- 新建项目后，该项目以独立卡片出现；删除项目后卡片消失。同步口径为再次加载仪表盘统计（与现有 stats 拉取一致），不新增实时通道。
- 无项目时不展示类型占位卡，给出可进入用例模块的空态。
- 「测试资产」章节头的用例总数 chip 仍为当前用户全部文档用例合计；元素定位列不变。

## 关联文档

- PRD-需求总纲（仪表盘为 KPI 概览入口；用例管理为 TASK 侧模块）
- PRD-01（仪表盘 KPI 概览；现行无独立子 PRD 正文，以总纲索引与现网仪表盘为准）
- PRD-05（用例管理已落地项目化；现行无独立子 PRD 正文，以现网 `/cases` 项目列表为准）

## Capabilities

### New Capabilities

- `dashboard-case-project-cards`: 仪表盘测试用例子区按项目出 KPI 卡、空态、进入项目工作台、与项目增删同步

### Modified Capabilities

- `dashboard-chapter-boards`: 「测试资产」仍为用例+元素同章；解除「breakdown 字段映射不得变、只能映旧类型拆分」的约束，允许 `cases.breakdown` 改为项目维度且仍走同一只读 stats 接口

## Impact

- 后端：`apps/dashboard/views.py`（`_cases_breakdown` / stats 中 `cases` 块）；跨 App 只读 `case_manager` 项目列表与用例计数（走对方公开 `api.py`，不写库）
- 前端：`frontend/src/modules/dashboard/`（`index.vue`、`DashboardView.logic.ts`、类型与 `useDashboardStats` 映射）；`frontend/src/shared/types/dashboard.ts`
- 不做：用例模块 CRUD、元素定位列、实时 WebSocket、前端二次请求 `/cases/projects/` 拼卡
- 测试：dashboard 前端单测（`useDashboardStats` / `DashboardView.logic`）；dashboard stats 契约或视图单测（若已有则改断言，无则补项目拆分用例）
