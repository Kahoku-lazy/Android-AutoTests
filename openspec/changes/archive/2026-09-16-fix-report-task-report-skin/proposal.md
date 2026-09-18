## Why

`/reports/task/{taskId}`（TaskReport.vue）的样式层与模板严重脱节：模板引用约 40 个类，其中约 25 个在本组件作用域内**没有任何 CSS 规则**，导致用例卡片、步骤条、性能指标块、任务信息条全部退化为无样式裸文本；执行历史表的通过率进度条因缺少高度与底色**完全不可见**；"任务未找到"分支不套骨架，页头与主题作用域双双缺失。这些均为 `frontend-l2-page-region` 与 `frontend-l4-data-surface` **既有要求**的实现违约，而非新增行为，因此本变更不含 spec delta。

## What Changes

- 用例明细 / 失败分析两 Tab 的卡片与步骤样式就地补齐，严格取设计令牌（不对称圆角、扁平 0 模糊阴影、字号不低于 `--app-size-xs`）
- 性能统计 5 个指标块改用共享 `KpiCard` —— 现状借用了 `KpiCard` 的 scoped 类 `.kpi-card`，因 `[data-v-*]` 隔离**跨组件无效**；落实 `frontend-l4-data-surface`「指标行 MUST 复用共享 KpiCard」
- 执行历史表的通过率改用共享 `RateBar`（现状三段式 `.progress-bar/.p-pass/.p-fail` 无定义 → 进度条不可见），与同模块 `index.vue:338` 的唯一正确范式一致
- 任务信息条类名对齐到本文件**已定义**的 `.task-meta-card` / `.meta-item`（现状模板写 `.task-meta-bar` / `.task-meta-item`，与样式名不匹配），并补 `.full-width` / `.conclusion-text`
- 用例明细空态与 `.step-empty` 之外的零散缺失样式（`.mono` / `.time-text`）补齐；整页空态改用共享 `EmptyState`
- "任务未找到"分支改为 `.doc-page .wb-shell .task-report-page` + `WorkbenchHeader` + `.doc-body` + 共享 `EmptyState`，回到共享骨架与主题作用域内
- **BREAKING**：无。纯前端渲染修复，不涉及接口、路由、鉴权或数据

## 关联文档

- `dev_docs/DEV_TEST/前端UI风格一致性分析-2026-09.md` §3.2（P0-2）与 §八·批次 A
- `dev_docs/DEV_TEST/前端UI一致性整改计划.md` 阶段 1 · `fix-report-task-report-skin`
- 既有要求（本变更的判据，非新行为）：`openspec/specs/frontend-l2-page-region/spec.md`「No L2 declaration without a consumer」「L2 page roots reuse the shared page skeleton」「Every L2 page root provides the workbench theme scope」；`openspec/specs/frontend-l4-data-surface/spec.md`「Cards and grids reuse shared parts」
- 既有正确范式：`modules/report-generator/index.vue:338`（RateBar）、`index.vue:356`（EmptyState）、`ReportDetail.vue` 的 `.task-meta-card` 同构命名

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 本变更把代码修复到既有要求，不改变任何 spec 级行为；`.openspec.yaml` 已置 `skip_specs: true`）

## Impact

- 主要：`frontend/src/modules/report-generator/TaskReport.vue`（模板复用共享件 + 补齐样式层），并新增对 `RateBar` / `EmptyState` 的 import
- 不改：`api.ts` / `constants.ts` / 路由 / 后端接口 / `AppTable` 与 `AppTabs` 的皮肤（后者属变更 7 / 9 范围）
- 测试范围：`npm run lint:styles`、`npm run typecheck`、`npx vite build --mode development`，以及本页三个 Tab 与未找到分支的浏览器确认
- 观感变化：该页首次呈现完整皮肤（此前用例/步骤/性能/信息条为裸文本，进度条不可见）

## 登记为后续变更的输入（本变更不做）

- 用例/步骤卡片跨页面共享化（TaskReport 与 CaseBreakdown 结构不同，需先统一数据形状）→ 变更 9 `unify-card-surfaces`
- 本页 `.detail-tabs` 重写 `AppTabs` 皮肤、`constants.ts` 死常量、`.doc-section` 口径 → 变更 7 / 14