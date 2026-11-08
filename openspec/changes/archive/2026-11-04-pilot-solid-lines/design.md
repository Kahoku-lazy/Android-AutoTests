## Context

- 规则：`dashed` 只允许出现在 `KpiCard.vue` / `AgentRouteCard.vue`，由 `frontend/tests/check-dashed-whitelist.mjs` 按「文件 → 次数」基线把关（`npm run lint:lines`，已进 `run.py check`）。
- 现状：22 个文件 / 37 处；其中任务详情 5 个组件、仪表盘 2 个文件。
- 仪表盘卡片皮肤来自 `workbench-theme.css` 的全局 `.wb-shell .ac-card`（`2.5px dashed !important` + 硬投影 + 微倾），改全局会波及所有页面。

## Goals / Non-Goals

**Goals:**

- 两个试点页全部实线；观感与任务详情新卡片一致（白卡 + 1px + 圆角 + 无硬投影）。
- 只在本页作用域覆盖，不改全局皮肤、不动其它页面。

**Non-Goals:**

- 不改全局 `.ac-card` / `.el-dialog` / `.el-drawer` / `--comp-*` 令牌（留给后续全量迁移）。
- 不动 KpiCard / AgentRouteCard（白名单）。

## Decisions

### 1. 仪表盘用页面作用域覆盖，而不是改全局 AppCard

在 `DashboardView.style.css` 加 `.dashboard-workbench .ac-card { border: 1px solid …; border-radius: …; box-shadow: none; transform: none }`。理由：全局规则一条影响 11 个 AppCard 实例（dashboard 7 + device-pool 1 + report 3），试点只该动仪表盘。

### 2. 取消微倾与硬投影

实线卡片再倾斜会显得歪；硬投影属于涂鸦语言。悬停只加深边框，不加阴影（门禁要求阴影模糊半径为 0，模糊阴影写不进去）。

### 3. 组件侧直接改声明，不加页面作用域

`CaseImportCard` / `TaskMediaThumb` / 证据块只在任务详情（及其用例编写分支）出现，直接改组件样式即可，不必再套一层作用域。

## 模块防火墙自检

- 只改 `frontend/src/modules/{task-list,dashboard}` 与一个前端门禁脚本；无跨模块 import、无后端改动。

## Risks / Trade-offs

- [仪表盘卡片失去涂鸦识别度] → 试点先看观感，不行可整页回退（改动集中在 `DashboardView.style.css` 一处覆盖块）。
- [其它页面仍虚线，切换页面观感不一致] → 这是试点的预期代价；确认后再全量迁移。
- [基线删除后旧文件又出现虚线会立刻红] → 这正是想要的：试点页从「存量放行」变成「0 容忍」。
