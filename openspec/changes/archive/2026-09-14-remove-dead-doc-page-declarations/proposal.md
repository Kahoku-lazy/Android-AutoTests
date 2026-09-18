## Why

`frontend/AGENTS.md` L2 速查 §⑥ 与 L2 现状复盘都把「模块 scoped `.doc-page { height:100% }` 是死声明」列为已知缺口，但**清单不准确、也一直没清**。复查后确认：

- **真正失效的只有 5 处**：它们的 `.doc-page` 是**单类选择器**，scope 后为 `.doc-page[data-v-x]` = 权重 2，恒被 `App.vue` 的 `.main-content__body :deep(.doc-page)`（编译为 `.main-content__body[data-v] .doc-page` = 权重 3）压过 —— 与 CSS 顺序无关。
- **`ai-assistant/TaskDetailPage.vue:225` 不是死声明**：它的选择器是复合的 `.task-detail-page.doc-page`，且 `height` / `overflow` 都带 `!important` → 权重与顺序均无法压过，**两条声明实际全程生效**。原清单把「ai-assistant」列为死声明持有者是**误判**。
- `device-pool` 同样被误列：该模块**没有**任何 `.doc-page` 覆写。

残留的 5 处死声明不影响运行，但会持续误导后续读者（读 CSS 会误判滚动归属）。

## What Changes

- 删除 5 处 `.doc-page` 中的**失效声明**：
  - `device-inspector/index.vue` → 删 `height: 100%`、`overflow: hidden`
  - `report-generator/TaskReport.vue` → 删 `height:100%`、`overflow-y:auto`
  - `report-generator/ReportDetail.vue` → 删 `height:100%`、`overflow-y:auto`
  - `report-generator/CaseBreakdown.vue` → 删 `height: 100%`、`overflow-y: auto`
  - `report-generator/index.vue` → **只删 `height:100%`**；`overflow:hidden!important` 实际生效，**保留**
- 同步修正 `frontend/AGENTS.md` L2 速查 §⑥ 的已知缺口表述（去掉已清项，并纠正 ai-assistant / device-pool 的误列）
- **BREAKING**：无。删除项均已被更高权重规则覆盖 → **无可见行为变化**
- 按 schema 约定设 `skip_specs: true`（需求文本不变，本变更只是让既有事实与文档一致）

## 关联文档

- 契约真相源：`openspec/specs/frontend-l2-page-region/spec.md`（页面根复用骨架 + `height/overflow` 由外壳承担）
- 前置变更：`openspec/changes/archive/2026-09-14-unify-l3-container`（`.doc-body` 口径，本次为 P4 收尾）· `archive/2026-09-14-fix-l3-container-residual`
- 说明：`dev_docs/文档编号对照表.md` 不存在，本变更无对应编号文档；属死声明清理

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 不改写任何 Requirement 文本，故无 delta）

## Impact

- 前端：`modules/device-inspector/index.vue` · `modules/report-generator/index.vue` · `TaskReport.vue` · `ReportDetail.vue` · `CaseBreakdown.vue`（各删 1–2 条失效声明）
- 文档：`frontend/AGENTS.md` L2 速查 §⑥
- 验证：`npm run typecheck` + `npx vite build --mode development` + `vue-frontend-check`；**不做浏览器核验**（见 design 决策 4 的静态证明）
- 不影响：路由、API、鉴权、任何页面的实际渲染
