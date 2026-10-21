# task-list 模块 AGENTS.md

> **AGENTS 层级**：二级约束 —— 根 `AGENTS.md` 与上级 `frontend/AGENTS.md` 优先于本文件。

## 职责

- `/tasks` 任务清单：任务卡分组、新建任务、重跑、关闭、删除、清空。
- `/tasks/:id` 任务详情：事件流程报告、步骤尝试、日志证据、日志检查。
- 接口统一走 `api/tasks.ts` → `/api/tasks/*`，不直打 `/api/reports/*` 或 `/api/ai/*` 的任务接口。
- 任务发布时读取助手列表可复用 `@/modules/ai-assistant/api/agents`；本模块不得被 `ai-assistant` 反向 import。

## 红线

| 只做 | 禁止 |
|------|------|
| 任务查看 / 创建 / 重跑 / 关闭 / 删除 / 清空 | 写助手配置、改 `AIAgent` |
| 只读展示事件、日志证据、费用 | 在前端重算计费或重排日志证据 |
| `/api/tasks/*` 单一 HTTP 出口 | 直打 `/api/reports/task/*`、`/api/ai/agent-tasks/*` |

## 契约

- 任务列表/详情/写操作响应为全局 `{status, data}`。
- 任务详情报告 `GET /api/tasks/{id}/report/` 为平铺 `{status, task, rounds, cases, conclusion}`，按端点结构读取。
- 任务卡「详情」、测试报告行点击、仪表盘任务点击统一进入 `/tasks/:id`。

## 快速验证

```bash
cd frontend
npx vitest run tests/task-list
npm run typecheck
npm run build:check
```
