## Why

需求方按截图要求把页面上的手绘虚线收成实线：侧栏分隔与仪表盘章节板是先要换的两处，而 KPI 指标卡仍要保留虚线，作为「可读数小卡」的手绘语义。现状里侧栏线型由一个共享组件令牌 `--comp-sidebar-dash` 代持，仪表盘章节板则在 `.doc-section--board` 里把全局实线覆写成虚线，不改这两处所有权就无法只换「线」而不动「卡」。

## What Changes

- 侧栏：右分隔线、品牌区底线、激活项描边、子导航左引导线、报尾顶线与底部用户卡描边全部由虚线改为 2.5px 墨色实线；线型改由侧栏作用域令牌 `--sidebar-line` 自持，移除共享 `--comp-sidebar-dash`。
- 仪表盘：四个章节板（平台运营 / AI 用量 / 测试资产 / 趋势与动态）不再覆写描边线型，回到全局 `.doc-section` 的墨色实线；章节头分隔线与子标题分隔线同步改实线。
- 保留虚线：KPI 指标卡（在线设备、累计用量等）、智能体用量卡、趋势 `AppCard`、活动时间线等「卡 / 数据块」继续使用 doodle 虚线，不改其组件皮肤。
- 登录页继续保留自有虚线（`--login-line: dashed`），本变更不波及。
- 同步 `frontend-sidebar-hand-drawn`、`dashboard-chapter-boards`、`frontend-login-hand-drawn-hero`、`frontend-l0-design-tokens` 四个能力中仍把「虚线」写成硬约束的表述，并登记 doodle-craft 参考文档。

## 关联文档

- PRD-平台总需求 §7（观测：仪表盘）

## Capabilities

### New Capabilities

### Modified Capabilities

- `frontend-sidebar-hand-drawn`: 侧栏分隔、品牌区与底栏、激活项描边由虚线改为实线，且线型改由侧栏作用域令牌自持
- `dashboard-chapter-boards`: 章节板与章节头分隔线由虚线改为实线，KPI 卡继续虚线
- `frontend-login-hand-drawn-hero`: 「共享线型变化不波及登录页」的场景不再引用已删除的共享令牌，改用侧栏自有线型令牌验证
- `frontend-l0-design-tokens`: 「线型不跨边界借用」的检索场景去掉已删除的 `--comp-sidebar-dash`，改为检查登录页不引用任何共享组件线型令牌

## Impact

- `frontend/src/shared/styles/tokens.css`：删除 `--comp-sidebar-dash`
- `frontend/src/shared/components/AppSidebar.style.css`：新增 `--sidebar-line` / `--sidebar-border`，六处描边改引用
- `frontend/src/views/LoginView.style.css`：仅更新说明性注释
- `frontend/src/modules/dashboard/DashboardView.style.css`：章节板去掉虚线覆写，章节头与子标题分隔线改实线
- `.agents/skills/doodle-craft/references/{tokens.md,components/layout.md}`：登记侧栏 / 章节板线型新口径
- 无接口、数据模型与依赖变化；无单测需改（现有测试不校验 CSS 线型）
