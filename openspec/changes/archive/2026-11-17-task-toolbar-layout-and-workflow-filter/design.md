# 设计：工具栏重排与工作流下拉

## Context

`TaskBoard.vue` 顶部有两行控件：`.task-toolbar`（工作流 chip 组 + 执行状态下拉 + 调试清空）与 `.table-toolbar`（显示行数 + 页码 + 翻页键）。工作流选项来自 `useTaskList().workflows`，其值由后端 `/api/tasks/` 的 `workflows` 字段给出（`task_list/api.py::workflow_filter_options()` → `ai_assistant.api.list_sop_workflows()`），已删除的工作流不会出现。

## Goals / Non-Goals

**Goals**：工作流筛选收成下拉、两行工具栏之间与表格前留白加大、翻页键靠右且禁用态明显。

**Non-Goals**：不改筛选逻辑（`workflowId` 仍是字符串、「全部」用 `all`）、不改分页逻辑、不动统计卡与表格列。

## Decisions

### D1 复用 `workflowTabs` 作为选项源，不再需要 chip 组

`workflowTabs` 已经是 `[{key:'all',label:'全部'}, ...workflows]`，直接喂给 `el-select` 的 `el-option`，绑定仍是 `workflowId`。这样筛选逻辑、`visibleTasks` 的过滤条件、分页重置行为全部不变，只是控件形态从 chip 变下拉。

### D2 翻页键包进 `.page-nav`，用 `margin-left: auto` 推到右端

`.page-info` 保留在左（跟在「显示行数」后面），`.page-nav` 用 `margin-left: auto` 顶到右端；两键之间 `gap`。

### D3 禁用态用灰底灰边 + 撤影

```css
.page-nav-btn:disabled {
  background: var(--app-bg-subtle);
  border-color: var(--app-border-strong);
  color: var(--app-text-secondary);
  box-shadow: none;
  cursor: not-allowed;
}
```

可点态保持原有天蓝底 + 墨边 + 硬影。

### D4 间距用令牌双档

`.task-toolbar` 下外边距 `--app-space-md`（16px），`.table-toolbar` 上 `--app-space-sm`、下 `--app-space-md`。两行控件与表格之间因此都拉开到 ≥16px。

## Risks / Trade-offs

- [下拉收起后看不到「还有哪些工作流」] → 与执行状态下拉同类控件一致；chip 组在工作流变多时反而更难用。
- [右对齐后页码与翻页键分离] → 页码紧邻翻页键左侧，仍在同一视觉组里。

## Migration Plan

纯前端组件内改动。回退 = 还原模板与样式块。

## Open Questions

无。
