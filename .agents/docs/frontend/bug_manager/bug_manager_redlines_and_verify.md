# bug-manager · 红线与快速验证

> 归属模块：`frontend/src/modules/bug-manager` ｜ 类型：模块功能开发说明
> 代码真相源：`frontend/src/modules/bug-manager/constants.ts`、`api.ts`、`helpers/bugDistribution.ts`、`helpers/errorDetail.ts`
> 上级约束：根 `AGENTS.md`、`frontend/AGENTS.md` ｜ 模块索引：`frontend/AGENTS.md`

## 红线

| 只做 | 禁止 |
|------|------|
| 展示与处理 BUG 单 | 在页面里重新解析任务 `result` |
| 分类色用 `--c-ai` / `--c-case`，模块色 `--c-runner` | 自造第二套卡片/表格/抽屉皮肤 |
| 状态更新经 `PATCH /api/bugs/{id}/` | 直接改本地状态冒充已保存 |
| 任务编号用 `bugTaskLabel`；有报告才打开报告 | 拼 host/port，或链到 `/tasks/:id` |

## 快速验证

```bash
cd frontend
npx vitest run tests/bug-manager tests/shared/p0/sidebarNavConfig.spec.ts
npm run typecheck
npm run lint:styles
```
