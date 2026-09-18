## Why

`frontend-l4-data-surface` spec 已把「分页唯一实现」定成契约，但 `report-generator/ReportDetail.vue` 仍保留一套手写分页状态机（`pageSize` / `currentPage` / `totalPages` / `pagedCases` / `goPage` / `setPageSize`），是全仓唯一的登记例外；同一模块的 `report-generator/index.vue` 与 `device-pool` 都已走共享 `usePagination`。同时 `shared/composables/usePagination.ts` 的 JSDoc 示例引用了**不存在的 `AnimalButton`**，接手者照注释写会找不到组件。本变更退役该例外并修正注释。

## What Changes

- `report-generator/ReportDetail.vue`：删除手写分页状态机（6 个符号），改用共享 `usePagination(allCases, { pageSize: 20, options: PAGE_SIZE_OPTIONS })`；`pagedCases` 由 `pagedItems` 重命名映射
- 该页 `tableScrollY` 继续消费 `usePagination` 返回的 `pageSize`，行高联动不变；`watch(runId)` 重置到第 1 页的语义不变（`currentPage` 为 composable 返回的 ref）
- **模板、分页文案与选项集零改动**：默认 20 行、可选 10 / 20 / 50 / 100、「第 X / Y 页 · 共 N 条」+ 上一页 / 下一页全部保持
- `shared/composables/usePagination.ts`：修正 JSDoc 示例里不存在的 `AnimalButton`，改为真实用法（`el-button` 上一页 / 下一页 + 页码文案）
- `openspec/specs/frontend-l4-data-surface`：以 MODIFIED 收回「`ReportDetail` 手写分页是登记例外」，改为「全仓分页实现唯一，不存在手写状态机」
- `frontend/AGENTS.md` L4 速查：§④.3 的例外、§⑤ 的判据、§⑥ 的已知缺口相应退役
- **BREAKING**：无。不动 props / emits / 路由 / 后端接口；分页行为逐项保持一致

## 关联文档

- `openspec/specs/frontend-l4-data-surface/spec.md`：本变更修改的需求所在（Single pagination implementation）
- `frontend/AGENTS.md` L4 速查 §④ / §⑤ / §⑥：例外与已知缺口的登记处
- `dev_docs/05-开发与测试/设计方案与报告/报告-前端区域层级与L4-L5现状复盘.html` §三：该手写分页的现状出处
- 说明：`dev_docs/文档编号对照表.md` 不存在；本变更为前端实现收敛，不改业务需求

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `frontend-l4-data-surface`: 「Single pagination implementation」需求收回 `ReportDetail` 的登记例外，改为全仓无手写分页状态机

## Impact

- `frontend/src/modules/report-generator/ReportDetail.vue`
- `frontend/src/shared/composables/usePagination.ts`（仅 JSDoc）
- `openspec/specs/frontend-l4-data-surface/spec.md`（归档时更新）· `frontend/AGENTS.md`（L4 速查 3 处）
- 测试与门禁：`vue-tsc --noEmit`；`vue-frontend-check` 过 `ReportDetail.vue`；报告详情页分页目视（本环境无浏览器，记录为待补）
- 不影响：`device-pool` 与 `report-generator/index` 的分页（已合规）、后端接口、路由表、其他模块
