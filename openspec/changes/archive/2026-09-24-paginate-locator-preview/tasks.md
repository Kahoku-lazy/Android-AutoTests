## 1. 预览改为分页呈现

- [x] 1.1 `LocatorPagePreview.vue` 改用 `pagedItems` 作为表格数据源，移除 `PREVIEW_ROWS` / `previewRows` / `hiddenCount` 与「还有 N 条未显示」文案。验证：`npx vue-tsc --noEmit` 零错误、`npx eslint src/modules/element-locator` 零输出
- [x] 1.2 页脚改为左侧分页（「第 X / Y 页 · 共 N 条」+ 上一页 / 下一页，边界禁用）+ 右侧「进入页面编辑」。验证：`npm run lint:styles` 批 1–4 通过
- [x] 1.3 `ProjectWorkspace.vue` 给预览件加 `:key="selectedFile.id"`，换页面重置到第 1 页。验证：断言从 13 条页面（停在第 2 页）切到 2 条页面后显示「第 1 / 1 页 · 共 2 条」

## 2. 验证与关单

- [x] 2.1 模块门禁：`npx vue-tsc --noEmit` 零错误 · `npx eslint src/modules/element-locator` 零输出 · `npm run lint:styles` 通过 · `npx vite build --mode development` 通过 · `npx vitest run tests/element-locator/p0` 30 用例全绿
- [x] 2.2 Chromium 断言分页：13 条页面首页 10 行 +「第 1 / 2 页 · 共 13 条」+ 上一页禁用；下一页 → 3 行 +「第 2 / 2 页」+ 下一页禁用；两页名称并集 13 条、重复 0（全部可达）；回上一页恢复 10 行；换页面重置到第 1 页；表头仍为三列；勾选框 / 开关 / 输入框均为 0；预览期间零写请求（唯一写请求是登录）；0 控制台错误。证据：`temps/locator-preview-paging-assert.json` + 两张截图
- [x] 2.3 边界检查：`python tools/gen_arch_stats.py --check-boundaries` → ✅ 零违规
- [x] 2.4 文档同步：`doodle-craft` 的 `references/page-layout.md` §4.7.1「右栏表格」行改为「三列 + 分页可达全部」
