## 1. 入口去重

- [x] 1.1 `LocatorPagePreview.vue` 删除页脚内的「进入页面编辑」按键，页脚只保留分页控件；标题行入口保持不动。验证：`npx vue-tsc --noEmit` 零错误、`npx eslint src/modules/element-locator` 零输出
- [x] 1.2 页脚对齐由 `space-between` 改为 `flex-end`（不再需要两端撑开）。验证：`npm run lint:styles` 批 2 / 批 4 通过

## 2. 验证与关单

- [x] 2.1 模块门禁：`npx vue-tsc --noEmit` 零错误 · `npx eslint src/modules/element-locator` 零输出 · `npm run lint:styles` 通过 · `npx vite build --mode development` 通过 · `npx vitest run tests/element-locator/p0` 30 用例全绿
- [x] 2.2 Chromium 断言：右栏内文案为「进入页面编辑」的按键数 = 1 且位于标题行；翻到最后一页该按键仍可见可点；分页文案「第 X / Y 页 · 共 N 条」与行数（10 → 3）不受影响；勾选框 / 开关 / 输入框均为 0；点该入口进详情页（10 个测试点开关）；预览期间零写请求；0 控制台错误。证据：`temps/locator-preview-cta-assert.json` + 截图
- [x] 2.3 边界检查：`python tools/gen_arch_stats.py --check-boundaries` → ✅ 零违规
