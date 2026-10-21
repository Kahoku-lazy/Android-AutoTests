## Why

仪表盘入口卡同时在卡片底部渲染一个「进入」小按钮，而整卡本身已经可点跳转——同一个动作给了两个入口，视觉上像两块可点区域，鼠标落到按钮上时还能看到「按钮套卡片」的重复描边。另一侧的「AI 用量」五张卡明明是纯读数指标，却因为带 `path` 而整卡可点、悬停抬升，点一下跳去 AI 助手页，与本区块「只展示信息」的定位不符。

## What Changes

- **BREAKING（组件契约）**：共享 `KpiCard` 的 `entry` 变体删除 `enterLabel` 属性与底部「进入」按钮（含 DOM 与样式），可点性只由 `clickable` 决定；仪表盘 `StatsCard` 同步删除 `showEnter`。
- 「平台运营」五张卡与「测试资产」项目卡：只保留**整卡点击跳转**，不再渲染独立「进入」按钮。
- 「AI 用量」五张 KPI 卡：去掉 `path`，变为**纯展示**——不可点、无 `role="button"`、无悬停抬升，只显示数值与副标题。
- 同步 4 份 spec 的验收条款与 4 条按钮相关单测。

## 关联文档

- PRD-01 仪表盘（入口卡与 AI 用量卡片的交互口径）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `frontend-doodle-kpi-card`: 「Entry variant for dashboard navigation stats」不再要求独立进入控件，改为整卡激活。
- `dashboard-chapter-boards`: 平台运营五张卡 MUST NOT 渲染独立「进入」按钮（原来只对任务数量卡有这条）。
- `dashboard-ai-usage`: AI 用量五张 KPI 卡 MUST 不可点击跳转（原条款是「可通过激活整卡进入智能体页」）。
- `dashboard-case-project-cards`: 项目卡 MUST NOT 渲染独立「进入」按钮，整卡点击进入项目工作台。

## Impact

- 共享件：`frontend/src/shared/components/KpiCard.vue`（删 `enterLabel`、按钮 DOM、3 段样式）
- 仪表盘：`components/StatsCard.vue`（删 `showEnter`）、`index.vue`（删 6 处 `:show-enter`、AI 五张卡删 `path`）
- 测试：`tests/shared/p0/KpiCard.spec.ts`、`tests/dashboard/p0/StatsCard.spec.ts`
- 不涉及：后端、接口、数据表、路由表（跳转目标不变）
