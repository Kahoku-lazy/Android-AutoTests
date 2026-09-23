## 1. 缩略图列成为定位入口

- [x] 1.1 `StructureAnalysisPanel.vue` 的 `#cell-thumbnail` 增加铺满整格的点击层：左键单击 `emit('select', row)`（复用既有选中通路），带 `.stop`，MUST NOT 触发重命名或勾选。验证：用例断言单击该格 emit 一次 `select` 且行对象正确
- [x] 1.2 该格的空占位（`—`）同样落在点击层内。验证：用例用 `thumbnail_path: ''` 的元素断言单击仍 emit
- [x] 1.3 放大预览改挂该格的双击（仅有 `thumbnail_path` 时打开），行级双击仍跳过该列。验证：用例断言双击无图行不打开预览、单击不打开预览
- [x] 1.4 点击层的样式与既有单元格做法同形（铺满单元格、指针为手型），并保证其所在单元格为定位基准。验证：`npm run lint:styles` 通过；视觉由人工在真窗口确认

## 2. 用例与门禁

- [x] 2.1 新增 `frontend/tests/device-inspector/p0/StructureAnalysisPanel-thumbnail-locate.spec.ts`：AppTable 替身渲染 `cell-thumbnail` 插槽，断言「单击缩略图列 emit select」「空占位同样可点」「单击其它单元格不 emit select」。验证：`npx vitest run tests/device-inspector` 全绿
- [x] 2.2 前端门禁：`npm run lint:styles`、`npx vue-tsc --noEmit`（全量输出逐条核对）、`npx vitest run`、`npx vite build`。验证：全绿，仅剩 3 条既有 `ProjectTree.vue` 报错
