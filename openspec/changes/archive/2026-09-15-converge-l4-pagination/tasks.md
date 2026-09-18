## 1. ReportDetail 分页收敛

- [x] 1.1 删除 `ReportDetail.vue` 的手写分页状态机（`pageSize` / `currentPage` ref、`totalPages` / `pagedCases` computed、`setPageSize` / `goPage` 函数），改用 `const { pageSize, currentPage, totalPages, pagedItems: pagedCases, setPageSize, goPage } = usePagination(allCases, { pageSize: 20, options: PAGE_SIZE_OPTIONS })`；验证：`vue-tsc --noEmit` 该文件零错误，模板引用的 6 个符号全部由 composable 提供
- [x] 1.2 确认 `tableScrollY` 与 `watch(runId)` 的 `currentPage.value = 1` 仍生效；验证：静态确认 `pageSize` 来自解构、`currentPage` 为 composable 返回的 ref
- [x] 1.3 全仓复核不再存在手写分页状态机；验证：`rg -n "Math.ceil\(.*pageSize|function goPage|const totalPages = computed" frontend/src` 仅命中 `shared/composables/usePagination.ts`

## 2. usePagination JSDoc 修正

- [x] 2.1 把 `usePagination.ts` JSDoc 示例中不存在的 `AnimalButton` 改为真实用法（`el-button` 上一页 / 下一页 + 「第 X / Y 页 · 共 N 条」文案）；验证：`rg -n "AnimalButton" frontend/src` 命中 0

## 3. 规格与速查同步

- [x] 3.1 以 MODIFIED 改写 `specs/frontend-l4-data-surface/spec.md` 的「Single pagination implementation」：第二个场景由「例外不扩散」改为「全仓无手写状态机」；验证：`openspec validate --strict` 通过
- [x] 3.2 更新 `frontend/AGENTS.md` L4 速查：§④.3 删除 ReportDetail 例外、§⑤ 分页判据改为「全仓唯一实现」、§⑥ 移除该例外并补记「本地 `PAGE_SIZE_OPTIONS` / `TABLE_*` 与 `constants.ts` 取值漂移」为新的已知缺口；验证：速查与 spec 无冲突

## 4. 门禁与归档

- [x] 4.1 `cd frontend && npm run typecheck`；验证：全仓 34 个既有错误，`ReportDetail.vue` 与 `usePagination.ts` 零错误
- [x] 4.2 用 `vue-frontend-check` 过 `ReportDetail.vue`；验证：calibration §7 强制扫描在改动行上无新增违规（字号 / 硬编码色 / 禁项 / fetch / catch 体 / 信封别名全部 0 处）
- [x] 4.3 归档（经 `openspec-archive-change`）；验证：`openspec/specs/frontend-l4-data-surface/spec.md` 已更新，变更进入 archive
