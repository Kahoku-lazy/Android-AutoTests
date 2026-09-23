## 1. SketchTable 表纸

- [x] 1.1 `PageElementsWorkbench.vue` 的 `AppTable` 增加 `accent="var(--c-element)"`。验证：模板含 `accent="var(--c-element)"`，渲染根出现 `.sketch-sheet`。
- [x] 1.2 在 `.locator-workbench.file-view` 作用域覆写 `.sketch-sheet { border-style: solid }`（可写在 `LocatorFileView.vue` 或模块 tokens/scoped CSS）。验证：选择器带 `.file-view`，只改 `border-style`，无描边色/宽/圆角字面量。

## 2. 硬边删除键

- [x] 2.1 在 `.locator-workbench.file-view` 对非 text/link 的 `el-button` 套硬边几何（对齐 `logout-btn`：2px 墨边、2px 圆角、`2px 2px 0 0 var(--ink)`，hover 位移 + 3px 阴影）。验证：`LocatorFilePanel` 仍用 `el-button` + 确认删除，不引入 `DoodleBtn`。
- [x] 2.2 删除键危险红底 + 浅色字，对比度口径 ≥ 4.5:1，色值全部 `var(--*)`。验证：无新增 `#hex` 交互色；`ElMessageBox.confirm` 流程仍在。

## 3. 门禁

- [x] 3.1 确认未改 `DoodleBtn.vue` / `FilterTabs.vue` / `ErrorState.vue` / `tokens.css` / `style.css` / `workbench-theme.css`，且项目列表/目录树无 `.file-view` 硬边误伤。验证：`git diff --stat` 本次实现仅落在元素定位文件详情相关 vue/css。
- [x] 3.2 `cd frontend && npm run typecheck`（本变更文件 0 报错）且 `npm run lint:styles` 通过。
- [x] 3.3 按 `vue-frontend-check` 扫改动文件（硬编码色、字号、可点击可达、布局裁剪）。
