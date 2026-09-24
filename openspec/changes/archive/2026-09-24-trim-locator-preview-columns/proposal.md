## Why

右栏预览现在照搬了详情页的七列，把「文本 / 主定位 / 交互标注 / 测试点」也铺在概览位上——预览位的职责是「这一页有哪些元素、长什么样」，不是核对定位表达式。需求方要求：**右栏只显示缩略图、元素名称、序号；其余内容进页面编辑才显示**。

## What Changes

- 工作台右栏预览的列收窄为三列：**缩略图 · 元素名称 · 序号**。
- 「文本 / 主定位 / 交互标注 / 测试点」四列 MUST NOT 出现在右栏，只在文件详情页呈现。
- 只读约束、进入页面编辑入口、预览条数与总数标注、窄屏退化口径全部不变。

## 关联文档

PRD-04 · ARCH-04

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `element-locator-page-workbench`: 「元素表在工作台右栏复用」收窄为三列预览口径

## Impact

- 前端模块：`frontend/src/modules/element-locator/components/LocatorPagePreview.vue`（列定义与单元格模板）
- 零后端改动；文件详情页（七列、可编辑）不受影响
- 不在本单：预览条数调整、深链落进并置态、工具栏按钮皮肤统一
