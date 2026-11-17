# 任务清单：去掉行数选择器，每页固定 10 行

## Why

任务清单的「显示行数 5」只提供 5 一个取值，却占了一枚按钮的视觉位；同时每页 5 行对「一眼扫完今日任务」偏少。另外这个 5 是页面内联写死的（`usePagination(..., { pageSize: 5, options: [5] })`），违反 `frontend-l4-data-surface`「分页选项集与默认值必须来自模块 constants」的口径。

## What Changes

- 删除「显示行数」标签与行数按钮组（与设备管理页一致：单取值不渲染选择器）。
- 每页固定 **10** 行，取值落到 `task-list/constants.ts`（`TASK_PAGE_SIZE_OPTIONS` / `TASK_DEFAULT_PAGE_SIZE`），页面不再内联数字。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `task-list-module`：新增「每页固定 10 行且不渲染行数选择器」要求。

## Impact

- 前端 `task-list`：`components/TaskBoard.vue`（模板与样式）、`constants.ts`（新增两个分页常量）。
- 不改接口、不改筛选与分页逻辑。
