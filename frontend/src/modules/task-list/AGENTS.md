# task-list 模块 AGENTS.md

> **AGENTS 层级**：二级约束 —— 根 `AGENTS.md` 与上级 `frontend/AGENTS.md` 优先于本文件。

## 职责

- `/tasks` 任务清单：任务卡分组、新建任务、重跑、关闭、删除、清空。
- 任务**没有详情页**（变更 retire-engines-agents）：一行任务跑完产出一份 HTML 报告，点「报告」直接打开该报告。
- 接口统一走 `api/tasks.ts` → `/api/tasks/*`，不直打 `/api/reports/*` 或 `/api/ai/*` 的任务接口。

## 红线

| 只做 | 禁止 |
|------|------|
| 任务查看 / 创建 / 重跑 / 关闭 / 删除 / 清空 | 写助手配置、改 `AIAgent` |
| 只读展示状态、费用、报告入口 | 在前端重算计费 |
| `/api/tasks/*` 单一 HTTP 出口 | 直打 `/api/reports/task/*`、`/api/ai/agent-tasks/*` |

## 契约

- 任务列表/详情/写操作响应为全局 `{status, data}`。
- 任务行带 `report_run` / `report_name`（由 `Task.result` 派生）；两者都在时，前端打开 `/api/ai/agent-reports/<run>/<name>/`。
- 已下线：`GET /api/tasks/{id}/report/` 与 `/tasks/:id` 路由。恢复任一项须先走 OpenSpec 变更。

## 快速验证

```bash
cd frontend
npx vitest run tests/task-list
npm run typecheck
```
