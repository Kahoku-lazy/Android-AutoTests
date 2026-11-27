# task-list · 任务清单页与契约

> 归属模块：`frontend/src/modules/task-list` ｜ 类型：模块功能开发说明
> 代码真相源：`frontend/src/modules/task-list/index.vue`、`api/tasks.ts`、`constants.ts`、`composables/useTaskList.ts`、`components/TaskBoard.vue`
> 上级约束：根 `AGENTS.md`、`frontend/AGENTS.md` ｜ 模块索引：`frontend/AGENTS.md`

## 职责

- `/tasks` 任务清单：任务卡分组、新建任务、重跑、关闭、删除、清空。
- 任务**没有详情页**（变更 retire-engines-agents）：一行任务跑完产出一份 HTML 报告，点「报告」直接打开该报告。
- 接口统一走 `api/tasks.ts` → `/api/tasks/*`，不直打 `/api/reports/*` 或 `/api/ai/*` 的任务接口。

## 契约

- 任务列表/详情/写操作响应为全局 `{status, data}`。
- 任务行带 `created_by` / `created_by_name`：表格「创建人」列读 `created_by_name`（提交人账号名），
  空值由 `helpers/task-card.ts` 的纯函数降级为「—」；列为只读展示，不做筛选。
- 「创建人」以**渐变标签**呈现：同色系两档 `color-mix` 渐变底 + 笔色描边 + 8px 同色圆点 + 账号名
  （超长省略、`title` 给全文）。颜色由 `creatorPenVars` 按账号名 FNV-1a 哈希取 9 支彩笔令牌
  （`--c-dashboard` / `--c-device` / `--c-element` / `--c-case` / `--c-runner` / `--c-report` /
  `--c-ai` / `--c-workflow` / `--c-ops`；**不含**只服务侧栏的 `--c-task` / `--c-account`），
  同一账号恒定同色（忽略大小写与首尾空白），不同账号尽量不同；没有账号名时不套色，只显示「—」。
- 任务行带 `report_run` / `report_name`（由 `Task.result` 派生）；两者都在时，前端打开 `/api/ai/agent-reports/<run>/<name>/`。
- 已下线：`GET /api/tasks/{id}/report/` 与 `/tasks/:id` 路由。恢复任一项须先走 OpenSpec 变更。
