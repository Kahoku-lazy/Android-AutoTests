## 1. 去掉截图圈选与筛选控件

- [x] 1.1 从 `PageElementsWorkbench.vue` 移除 `PageScreenshotOverlay`、`.page-workbench__shot`、`el-radio-group` 筛选与 `elementFilter`；`apiPageItems` 固定未筛选（`'all'` 或省略 filter），`watch` 仅依赖 `pageId`。验证：组件源码中不再出现 `el-radio-button`、`shot-pane`、`elementFilter`、`PageScreenshotOverlay`。
- [x] 1.2 删除截图联动专用逻辑：`screenshotPath`、`onShotSelect`、`scrollRowIntoView`、`selectElement` 的 `source` 参数；保留表格行点击当前行高亮与别名/测试点行内编辑。验证：文件内无 `querySelector` 滚行、无 `screenshotPath` 赋值。
- [x] 1.3 布局改为单列弹性容器包 `AppTable`/空态，删除 `__split` 双栏 grid 与窄屏「上截图下表格」media query；工具栏仅保留元素计数。验证：scoped 样式中无 `page-workbench__shot`、无 `grid-template-columns: minmax(280px`。

## 2. 清退仅 overlay 使用的文件

- [x] 2.1 删除 `frontend/src/modules/element-locator/components/PageScreenshotOverlay.vue`。验证：全仓 Grep `PageScreenshotOverlay` 命中数为 0。
- [x] 2.2 删除 `frontend/src/modules/element-locator/helpers/element-bounds.ts`。验证：全仓 Grep `element-bounds` / `mediaPathToUrl` / `resolveElementRect` 命中数为 0。

## 3. 门禁

- [x] 3.1 `cd frontend && npm run typecheck` 通过。
- [x] 3.2 按 `vue-frontend-check` 对改动文件过门禁（布局裁剪、硬编码色、展示组件、可点击可达）；确认未改后端、未改设备检查器。验证：diff 仅落在元素定位前端私有组件/helper。
