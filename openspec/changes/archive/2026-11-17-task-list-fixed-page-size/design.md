# 设计：任务清单分页常量下沉

## Context

`TaskBoard.vue` 现在是 `usePagination(visibleTasks, { pageSize: 5, options: [5] })` —— 行数写死在页面里，与 `frontend-l4-data-surface`「分页选项集 MUST 来自模块 `constants.ts`，SHALL NOT 在页面内联」冲突；界面上还渲染了只有单取值的「显示行数」按钮组。

## Goals / Non-Goals

**Goals**：每页 10 行、行数配置进 constants、去掉选择器。

**Non-Goals**：不改分页逻辑（`usePagination` 的夹取行为不动）、不改筛选、不改页脚文案。

## Decisions

### D1 常量放在 `task-list/constants.ts`

```ts
export const TASK_PAGE_SIZE_OPTIONS = [10]
export const TASK_DEFAULT_PAGE_SIZE = 10
```

页面改成 `usePagination(visibleTasks, { pageSize: TASK_DEFAULT_PAGE_SIZE, options: TASK_PAGE_SIZE_OPTIONS })`。与设备管理页（`PAGE_SIZE_OPTIONS` / `DEFAULT_PAGE_SIZE`）同一手法，`options` 单值仍由 composable 消费，满足 l4 的「固定行数页也必须有选项集」。

### D2 模板删掉行数组，保留页码与翻页键

删除 `.toolbar-label`「显示行数」与 `v-for` 出来的 `.page-size-btn`；`PAGE_SIZE_OPTIONS` / `setPageSize` 从解构里去掉，`pageSize` 保留给 `usePagination` 内部与可能的页高计算。样式里 `.page-size-btn` 一并删除。

## Risks / Trade-offs

- [10 行比 5 行更容易一屏放不下] → 任务清单本来就在 `.doc-body` 内纵向滚动，行高不变。
- [删掉选择器后用户不能再切回 5] → 与设备页一致：单取值不渲染控件，需要时改 constants 一行。

## Migration Plan

纯前端。回退 = 还原模板里那一段与 `usePagination` 的行数参数。

## Open Questions

无。
