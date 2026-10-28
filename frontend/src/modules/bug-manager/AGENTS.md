# bug-manager 模块 AGENTS.md

> **AGENTS 层级**：二级约束 —— 根 `AGENTS.md` 与上级 `frontend/AGENTS.md` 优先于本文件。

## 职责

- `/bugs` BUG 单列表：分类/状态/关键字筛选、KPI、分页、详情抽屉与处理状态。
- 接口统一走 `api.ts` → `/api/bugs/*`，不直打任务或报告接口。
- 关联任务只跳转 `/tasks/:id`，不复制任务详情逻辑。

## 红线

| 只做 | 禁止 |
|------|------|
| 展示与处理 BUG 单 | 在页面里重新解析任务 `result` |
| 分类色用 `--c-ai` / `--c-case`，模块色 `--c-runner` | 自造第二套卡片/表格/抽屉皮肤 |
| 状态更新经 `PATCH /api/bugs/{id}/` | 直接改本地状态冒充已保存 |
| 任务链接用 `bugTaskRoute` | 拼 host/port 或绕过路由 |

## 契约

- 列表 `GET /api/bugs/` 返回 `summary/total/items/truncated`，过滤参数 `category/status/keyword`。
- 详情 `GET /api/bugs/{id}/` 返回完整 `detail`；列表只给 `detail_preview`。
- 状态只允许 `open/resolved/ignored`；任务编号始终显示在表格与抽屉。

## 快速验证

```bash
cd frontend
npx vitest run tests/bug-manager tests/shared/p0/sidebarNavConfig.spec.ts
npm run typecheck
npm run lint:styles
```
