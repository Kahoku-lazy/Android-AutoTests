## Why

右栏同时出现了两个「进入页面编辑」按键（标题行一个、页脚一个），同一个动作在同一屏重复，读者要判断两者是否有区别。需求方要求只保留一个。

## What Changes

- 右栏的「进入页面编辑」入口收敛为**唯一一个**，位置固定在预览标题行（不随翻页滚出视口）；页脚只保留分页控件。
- 三列口径、只读约束、分页可达全部、窄屏退化全部不变。

## 关联文档

PRD-04 · ARCH-04

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `element-locator-page-workbench`: 新增「右栏编辑入口唯一且常驻可见」要求

## Impact

- 前端模块：`frontend/src/modules/element-locator/components/LocatorPagePreview.vue`（删除页脚入口按键，页脚只留分页）
- 零后端改动
- 不在本单：把入口改成图标键、入口文案改写
