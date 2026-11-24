# ops-console · 用户管理页与权限

> 归属模块：`frontend/src/modules/ops-console` ｜ 类型：模块功能开发说明
> 代码真相源：`frontend/src/modules/ops-console/index.vue`、`api.ts`、`routes.ts`、`composables/useOpsUsers.ts`、`components/OpsUserDrawer.vue`
> 上级约束：根 `AGENTS.md`、`frontend/AGENTS.md` ｜ 模块索引：`frontend/AGENTS.md`

## 入口与布局

- 路由 `/ops/users`（`routes.ts`），侧栏「运营」分组（在「AI任务」之后），标题「用户管理」。
- 该分组 `requiresOperator: true`：非运营不渲染；深链由 `router.ts` 的 `requiresOperator` 守卫拦回 `/dashboard`。
- 页面 = `WorkbenchHeader` + `FilterTabs`（全部/启用/停用）+ 搜索框 + 本页勾选 + 批量停用（超管另有批量注销）+ `AppTable` 表纸 + 分页工具条 + 右侧 `el-drawer`。
- 单页制：**不新增详情路由**。单条动作在抽屉里完成；批量动作只作用于当前页勾选。

## 数据与权限

- HTTP 唯一出口是 `api.ts`（走 `shared/api-client`），端点全部在 `/api/ops/users/`：
  - `GET /ops/users/`（`page` / `page_size` / `keyword` / `active`）
  - `POST /ops/users/{id}/disable/`、`POST /ops/users/{id}/enable/`
  - `POST /ops/users/{id}/reset-password/`
  - `POST /ops/users/disable/`（本页批量停用）、`POST /ops/users/purge/`（仅超管批量注销）
- 分页在**服务端**：翻页与改每页条数都要重新请求，不在前端切片。
- 身份判定只读 `useAuthUser()`（`isOperator` / `isSuperuser`）；页面据此置灰不可管理的行，**服务端的 403 才是权威**。
- 列表按行开抽屉；停用/启用与重置密码都要先 `ElMessageBox` 二次确认。
