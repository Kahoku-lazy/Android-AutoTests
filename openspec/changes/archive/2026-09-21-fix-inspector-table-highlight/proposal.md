## Why

设备检查器里几处已经改过的界面，和现行页面契约不一致：设备选择仍被要求天蓝底，元素表仍被要求每页 8 行，点行高亮的手势也不明确。这些改动没有先落 OpenSpec，需要把最终行为写回契约，避免实现和规格各说各话。

## What Changes

- 设备选择触发键与展开后的下拉浮层改为白底、无阴影；墨线边框保留。触发键不再使用天蓝底。**BREAKING**（相对「触发键始终天蓝底」）
- 元素表格每页固定行数由 8 改为 7（含表头全选只作用于当前页的口径）。**BREAKING**（相对「固定 8 行」）
- 无数据时表纸高度锁在结构栏内，空态文案留在可视区域内，底边不得超出屏幕
- 单击「元素名称」只进入重命名，不改变手机画面高亮
- 双击「标识」单元格，才在手机截图上按该元素坐标画红框高亮；单击表格行（含单击「标识」）不触发红框

## 关联文档

PRD-03

## Capabilities

### New Capabilities

### Modified Capabilities

- `device-inspector-page`: 设备选择控件的底色与阴影、元素表分页行数、空表高度，以及「元素名称 / 标识」与手机红框高亮的手势

## Impact

- 前端 `device-inspector`：`constants.ts` 分页常量、`index.vue` 设备选择皮肤、`CaptureForm.vue` 下拉 `popper-class`、`StructureAnalysisPanel.vue` 空表高度与行点击、`ScreenshotView.vue` 红框绘制
- 主规格 `device-inspector-page` 中「按键可用性」「固定 8 行分页」「设备选择控件」「勾选当前页行数」需要同步改写
- 无后端 API、无表结构变更
