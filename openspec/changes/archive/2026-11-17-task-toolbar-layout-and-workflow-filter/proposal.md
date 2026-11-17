# 任务清单工具栏：工作流下拉筛选 + 间距与翻页对齐

## Why

任务清单把「工作流」筛选做成一排 chip，工作流一多就撑满一行；「显示行数」那一条与上方筛选、下方表格贴得太近，读起来是三段糊在一起；「上一页 / 下一页」夹在页码后面，既不在右端，不可点时的样式也和可点状态差别不大。

## What Changes

- 工作流筛选从 chip 组改为**下拉**（选项「全部」+ 每个工作流），数据来自 AI 助手的 SOP 工作流列表（后端 `/api/tasks/` 的 `workflows` 字段已由 `ai_assistant.api.list_sop_workflows()` 提供）。
- 「显示行数」一条与上方筛选行、下方表格的间距加大。
- 「上一页 / 下一页」移到工具栏右端；不可点击时改为灰底灰边、撤除位移阴影。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `task-list-module`：新增「工具栏布局与工作流下拉筛选」要求。

## Impact

- 前端 `task-list`：`components/TaskBoard.vue`（模板 + scoped 样式）。
- 不动接口、不动后端、不动 `useTaskList` 的数据装配（`workflows` 已在用）。
