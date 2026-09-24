## Why

右栏预览当前只给首屏 6 条，其余元素在右栏看不到——要浏览一个页面有多少元素、分别叫什么，仍必须逐个进入页面。需求方要求：**预览要能看全部，并支持上一页 / 下一页**。

## What Changes

- 右栏预览改为**分页呈现该页全部元素**：每页固定 10 行（与详情页同口径），提供「第 X / Y 页 · 共 N 条」与上一页 / 下一页（到边界禁用）。
- 取消「只取首屏 6 条 + 还有 N 条未显示」的截断表达。
- 列口径（只有缩略图 / 元素名称 / 序号三列）、只读约束、进入页面编辑入口、窄屏退化全部不变。

## 关联文档

PRD-04 · ARCH-04

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `element-locator-page-workbench`: 「元素表在工作台右栏复用」由首屏截断改为分页可达全部

## Impact

- 前端模块：`frontend/src/modules/element-locator/components/LocatorPagePreview.vue`（改用共享分页状态 `pagedItems / currentPage / totalPages / goPage`）
- `ProjectWorkspace.vue`：预览件按选中页面加 `:key`，避免跨页面残留页码
- 零后端改动；详情页七列与编辑行为不受影响
- 不在本单：预览每页行数改为可配置、进详情页时承接当前页码、深链落进并置预览态
