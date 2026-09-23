## 1. 行数 12 → 14

- [x] 1.1 模块常量：`DEFAULT_PAGE_SIZE` 与 `PAGE_SIZE_OPTIONS` 同步为 14，注释里的行数同步。验证：`frontend/src/modules/device-inspector/` 内检索不到第二处行数字面量，`npx vue-tsc --noEmit` 通过
- [x] 1.2 面板分页注释同步（`StructureAnalysisPanel.vue` 的「每页固定 12 行」改为 14 行）。验证：注释取值与常量一致
- [x] 1.3 用例改为 40 条元素：首屏 14 行且分页为「第 1 / 3 页 · 共 40 条」、第 2 页仍 14 行、末页 12 行。验证：`npx vitest run` 中该用例通过

## 2. 门禁

- [x] 2.1 前端关单门禁：`npm run lint:styles`、`npx vue-tsc --noEmit`、`npx vite build`、`npx vitest run`。验证：全绿（仓库既有的无关报错按现状如实记录）
