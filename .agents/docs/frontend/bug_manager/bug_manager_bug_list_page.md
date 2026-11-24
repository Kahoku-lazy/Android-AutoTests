# bug-manager · BUG 单列表与契约

> 归属模块：`frontend/src/modules/bug-manager` ｜ 类型：模块功能开发说明
> 代码真相源：`frontend/src/modules/bug-manager/index.vue`、`api.ts`、`constants.ts`、`composables/useBugList.ts`、`components/BugDetailDrawer.vue`
> 上级约束：根 `AGENTS.md`、`frontend/AGENTS.md` ｜ 模块索引：`frontend/AGENTS.md`

## 职责

- `/bugs` BUG 单列表：分类/状态/关键字筛选、KPI、分页、详情抽屉与处理状态。
- 接口统一走 `api.ts` → `/api/bugs/*`。报告只复用任务清单已有的报告读取，不新拼地址。
- 关联任务只显示任务编号，不链到已下线的 `/tasks/:id`。

## 契约

- 列表 `GET /api/bugs/` 返回 `summary/total/items/truncated`，过滤参数 `category/status/keyword`。
- 详情 `GET /api/bugs/{id}/` 返回完整 `detail`；列表只给 `detail_preview`。
- 状态只允许 `open/resolved/ignored`；任务编号始终显示在表格与抽屉。
