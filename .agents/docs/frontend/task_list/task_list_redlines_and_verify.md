# task-list · 红线与快速验证

> 归属模块：`frontend/src/modules/task-list` ｜ 类型：模块功能开发说明
> 代码真相源：`frontend/src/modules/task-list/api/tasks.ts`、`constants.ts`、`helpers/task-detail.ts`
> 上级约束：根 `AGENTS.md`、`frontend/AGENTS.md` ｜ 模块索引：`frontend/AGENTS.md`

## 红线

| 只做 | 禁止 |
|------|------|
| 任务查看 / 创建 / 重跑 / 关闭 / 删除 / 清空 | 写助手配置、改 `AIAgent` |
| 只读展示状态、费用、报告入口 | 在前端重算计费 |
| `/api/tasks/*` 单一 HTTP 出口 | 直打 `/api/reports/task/*`、`/api/ai/agent-tasks/*` |

## 快速验证

```bash
cd frontend
npx vitest run tests/task-list
npm run typecheck
```
