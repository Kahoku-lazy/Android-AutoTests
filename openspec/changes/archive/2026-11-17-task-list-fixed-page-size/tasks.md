# 任务：任务清单固定每页 10 行

## 1. 实现

- [x] 1.1 `constants.ts` 新增 `TASK_PAGE_SIZE_OPTIONS = [10]` 与 `TASK_DEFAULT_PAGE_SIZE = 10`
- [x] 1.2 `TaskBoard.vue` 的 `usePagination` 改用这两个常量，删除页面内联的 `pageSize: 5`
- [x] 1.3 模板删除「显示行数」标签与行数按钮；解构去掉 `PAGE_SIZE_OPTIONS` / `setPageSize`
- [x] 1.4 样式删除 `.page-size-btn` 与 `.toolbar-label` 相关规则

## 2. 验证

- [x] 2.1 浏览器验收 `/tasks`（12 条假数据）：`rows: 10`、`第 1 / 2 页 · 共 12 条`、`hasSizePicker: false`
- [x] 2.2 `prettier --check` 通过、`eslint src/modules/task-list` 无新问题、`vue-tsc` 对 task-list 无新错
- [x] 2.3 `node tests/run.mjs module task-list`：48 用例全绿；截图 `temps/tasks-page10.png`
