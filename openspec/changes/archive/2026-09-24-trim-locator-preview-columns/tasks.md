## 1. 预览列收窄为三列

- [x] 1.1 `LocatorPagePreview.vue` 的 `PREVIEW_COLUMNS` 收窄为 缩略图 / 元素名称 / 序号 三列，并删除 `#cell-text_val`、`#cell-primary_xpath`、`#cell-flags`、`#cell-is_test_point` 四个插槽与 `interactionLabels` 导入。验证：`npx vue-tsc --noEmit` 零错误、`npx eslint src/modules/element-locator` 零输出
- [x] 1.2 清理失去消费方的样式（`.page-preview__flags` / `.page-preview__flag`），保留缩略图占位与文本省略样式。验证：`npm run lint:styles` 批 1–4 通过
- [x] 1.3 元素名称列吃掉剩余宽度（保持 `minWidth`、不设固定 `width`），三列不出现横向滚动。验证：Chromium 断言表头恰为三列，表体 `scrollWidth = clientWidth = 820`

## 2. 验证与关单

- [x] 2.1 模块门禁：`npx vue-tsc --noEmit` 零错误 · `npx eslint src/modules/element-locator` 零输出 · `npm run lint:styles` 通过 · `npx vite build --mode development` 通过 · `npx vitest run tests/element-locator/p0` 30 用例全绿
- [x] 2.2 Chromium 断言：右栏表头 `['缩略图','元素名称','序号']`（不含其余四列）；勾选框 0 / 开关 0 / 输入框 0；双击不出输入框；预览期间写请求 `[]`；页脚「预览前 6 条 · 共 13 条（还有 7 条未显示）」；入口按键 2px 实边 + 2px 圆角 + 硬阴影；点入口后详情页表头为七列、21 个输入框与 10 个测试点开关齐备；0 控制台错误。证据：`temps/locator-preview-assert.json` + 截图
- [x] 2.3 边界检查：`python tools/gen_arch_stats.py --check-boundaries` → ✅ 零违规
- [x] 2.4 文档同步：`doodle-craft` 的 `references/page-layout.md` §4.7.1「右栏表格」行写明预览只给三列
