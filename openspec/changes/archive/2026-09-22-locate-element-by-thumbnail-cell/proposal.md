## Why

**表格 → 截图的定位链路缺失。** 截图上的矩形框可以点（点击后表格对应行出现紫色填充），但反过来没有入口：表格里选中一行不会让画面上任何东西高亮，而表里大量元素没有文本（图标 / 容器），用户无法判断这一行到底指屏幕上哪个元素。

现状（真机核实）：

- 画面高亮只由 `store.selected` 驱动（`ScreenshotView.vue` 的 `drawVisible()` 画红色描边 + 淡红填充，并在视区外时平滑滚动过去）；
- 而写入 `selected` 的表格入口**只有**「左键双击数据格」（`StructureAnalysisPanel.vue` 的 `onRowDblClick`）——单击任何单元格按现行规格 MUST NOT 改动高亮；
- 「缩略图」列当前是占位行（无缩略图数据），单击它走 `openEnlarge(row)` 但立刻 `return`，等于点了没反应。

本变更把「缩略图」列变成定位入口：**左键单击该列即选中该行元素 → 画面画出对应矩形框的高亮**（复用既有选中视觉，同时该行出现紫色填充、必要时自动滚动到可见位置）。

## What Changes

- **单击「缩略图」列 = 定位高亮**：点击目标是**整格**（含该列为空占位的情形），触发既有的「选中元素」状态；MUST NOT 因此进入重命名或改动勾选。
- **放大预览改挂双击**：该列在有缩略图数据时，双击打开放大预览（单击已被定位占用）。设备检查器当前不放缩略图数据，故该手势目前处于休眠；移动手势是为了让「一次点击只有一个含义」。
- **BREAKING（交互）**：原「单击缩略图 = 打开放大预览」不再成立（现存规格未钉该手势，规格只钉「放大预览失效时有占位」）。
- 其余单元格的单击语义不变（MUST NOT 改动高亮）。

## 关联文档

- PRD-03（设备检查器）

## Capabilities

### Modified Capabilities

- `device-inspector-page`: 「手机画面按当前分组圈选并保留选中高亮」新增「单击缩略图列即高亮该元素矩形框」的例外条款与两个场景（含空占位可点）。

## Impact

- 前端：`frontend/src/modules/device-inspector/components/StructureAnalysisPanel.vue`（缩略图格的点击与样式）、`SnapshotListDrawer.vue` 无关
- 测试：`frontend/tests/device-inspector/p0/` 新增面板用例（单击缩略图列 emit select；空占位同样可点；单击其余单元格不 emit）
- 不涉及：后端、分层数据口径、`ScreenshotView.vue` 的绘制逻辑（复用既有 `selected` 通路）
