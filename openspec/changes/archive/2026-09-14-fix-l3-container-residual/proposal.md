## Why

L0–L3 复查发现已归档的 `unify-l3-container` 有两处残留：

1. **一处裸容器覆写被漏掉** —— `frontend/src/modules/dashboard/DashboardView.style.css` 由 `dashboard/index.vue:297` 的 `<style src="./DashboardView.style.css" scoped>` 引入，属于 `<style>` 块的一部分，但 apply 时的核验只扫了 `*.vue`，导致 `openspec/specs/frontend-l3-container/spec.md` 的 Scenario「裸 `.doc-body {` 命中数为 0」**当前为假**。
2. **6 个零消费的 `wb-*` 类** —— `.wb-chip` · `.wb-status-pill` · `.wb-spinner` · `.wb-btn--teal` · `.wb-btn--berry` · `.wb-btn--sky`，全仓除自身定义外 0 命中（含动态拼接），属纯死 CSS。

## What Changes

- **P0 容器口径补漏**：dashboard 页面根补 `dashboard-workbench` modifier；`DashboardView.style.css` 的 `.doc-page` / `.doc-body` 收窄为 `.dashboard-workbench .doc-page` / `.dashboard-workbench .doc-body`；并删除该 `.doc-page` 块中**已确证失效**的 `height:100%` 与 `overflow:hidden`（保留 `display` / `flex-direction` / `background-color`）
- **P1 死 CSS 类清理**：删除上述 6 个 `wb-*` 类及其 hover / active 变体规则
- **BREAKING**：无。一项为口径收敛（行为不变），一项为纯删除（零消费方）→ **无可见行为变化**
- 不改 dashboard 的 `.doc-section*` 块级覆写、不删 `.agent-card`、不动 `.el-message--top`
- 按 schema 约定设 `skip_specs: true`：需求文本未变，本变更只是让 `frontend-l3-container` 的既有 Scenario 实际成立

## 关联文档

- 契约真相源：`openspec/specs/frontend-l3-container/spec.md`（Requirement: Container overrides are scoped by a module modifier）
- 前置变更：`openspec/changes/archive/2026-09-14-unify-l3-container`（本变更为其收尾）
- 复查依据：L0–L3 复查报告（静态扫描 + CSS 权重推算；见对话记录）
- 说明：`dev_docs/文档编号对照表.md` 不存在，本变更无对应编号文档；属口径收敛与死代码清理

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 本变更使 `frontend-l3-container` 的既有 Requirement / Scenario 实际成立，未改写任何 Requirement 文本，故不产生 delta）

## Impact

- 前端：`modules/dashboard/index.vue`（页面根 +1 modifier）· `modules/dashboard/DashboardView.style.css`（2 个选择器收窄 + 删 2 个失效属性）· `shared/styles/workbench-theme.css`（删 `.wb-chip` / `.wb-status-pill`）· `shared/styles/motion.css`（删 `.wb-btn--teal` / `--berry` / `--sky`、`.wb-spinner`）
- 验证：`npm run typecheck` + `npx vite build --mode development` + `vue-frontend-check` + dashboard 三档目视
- 不影响：路由、API、鉴权、其它页面与模块
