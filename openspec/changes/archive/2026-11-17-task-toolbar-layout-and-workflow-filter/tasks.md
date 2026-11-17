# 任务：任务清单工具栏重排

## 1. 工作流下拉筛选

- [x] 1.1 `TaskBoard.vue`：把 `FilterTabs` 换成 `el-select`（选项来自 `workflowTabs`），绑定仍是 `workflowId`，宽度 200px
- [x] 1.2 移除不再使用的 `FilterTabs` 引入

## 2. 间距与翻页对齐

- [x] 2.1 `.task-toolbar` 下外边距 `--app-space-md`；`.table-toolbar` 上 `--app-space-sm` / 下 `--app-space-md`；实测「筛选行 → 显示行数行」16px、「显示行数行 → 表格」17px（改前均为 0）
- [x] 2.2 翻页键包进 `.page-nav` 并用 `margin-left: auto` 靠右；实测 `.page-nav` 右边界与工具条右边界同为 1519px
- [x] 2.3 禁用态：实测「上一页」`background rgb(243,239,226)`（`--app-bg-subtle`）、`box-shadow: none`；「下一页」保持天蓝底 + 2px 硬影

## 3. 验证

- [x] 3.1 `/tasks` 实跑：工作流下拉展开为「全部 / Android-UI-SOP / Govee-UI-SOP」（数据即后端 `/api/tasks/` 的 `workflows`，来自 `ai_assistant.api.list_sop_workflows()`）；页内 `.filter-tabs` 已不存在
- [x] 3.2 `npx vue-tsc --noEmit` 对 task-list 无新错、`npx eslint src/modules/task-list` 0 error、`npx prettier --check` 通过
- [x] 3.3 `node tests/run.mjs module task-list`：48 用例全绿；截图 `temps/tasks-toolbar-clean.png`
