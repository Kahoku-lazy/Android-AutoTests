## 1. 行数 7 → 12

- [x] 1.1 模块常量：`DEFAULT_PAGE_SIZE` 与 `PAGE_SIZE_OPTIONS` 同步为 12。验证：`frontend/src/modules/device-inspector/` 内检索不到第二处行数字面量，`npx vue-tsc --noEmit` 通过
- [x] 1.2 面板分页注释同步（`StructureAnalysisPanel.vue` 的「每页固定 7 行」改为 12 行）。验证：注释取值与常量一致
- [x] 1.3 新增挂载用例 `frontend/tests/device-inspector/p0/StructureAnalysisPanel.spec.ts`：以 27 条元素挂载面板，断言首屏表格收到 12 行、分页文案为「第 1 / 3 页 · 共 27 条」。验证：`npx vitest run` 中该用例通过

## 2. 门禁

- [x] 2.1 前端关单门禁：`npm run lint:styles`、`npx vue-tsc --noEmit`、`npx vite build`、`npx vitest run`。验证：全绿（仓库既有的无关报错按现状如实记录）
