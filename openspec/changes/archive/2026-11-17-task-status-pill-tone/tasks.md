# 任务：执行状态徽标七态分色 + 渐变底

## 1. 实现

- [x] 1.1 `TaskBoard.vue` 的 `.status-pill` 基类改为消费 `--sp-color`：1.5px 状态色描边（75% 混透明）+ 20%→5% 纵向渐变 + 墨色文字
- [x] 1.2 七态各声明 `--sp-color`（pending `--c-dashboard` / running `--c-workflow` / paused `--app-status-purple` / success `--app-status-success` / failed `--app-status-danger` / interrupted `--c-ops` / cancelled `--c-report`），删除旧的纯色 `is-success` / `is-failed` 覆盖

## 2. 验证

- [x] 2.1 浏览器量测 `/tasks`（7 条假数据，每页 5 条翻两页）：七枚徽标 `background-image` 均含 `linear-gradient`，描边色两两不同，无灰底退化；已中断 = 赭橙、任务取消 = 灰紫，其余五态各自独立色相
- [x] 2.2 文字统一为墨色 `rgb(30,30,36)`（首版用「状态色 70% 混墨」，实测黄/蓝在浅渐变底上对比度不足 4.5:1，已改回墨色并把状态色只用于描边与底）
- [x] 2.3 `npx prettier --check`、`npm run lint:styles`（task-list 无新增告警）、`npx vue-tsc --noEmit` 对 task-list 无新错
- [x] 2.4 `npx vitest run tests/task-list` 全绿；截图 `temps/tasks-pills-v2.png`（第 1 页五态）、`temps/tasks-pills-p2.png`（第 2 页已中断 / 任务取消）
