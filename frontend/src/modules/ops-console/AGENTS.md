# ops-console 模块约束

> **AGENTS 层级**：二级约束 —— 根 `AGENTS.md` 与上级 `frontend/AGENTS.md` 优先于本文件（本文件只写增量）。

## 入口与布局

- 路由 `/ops/users`（`routes.ts`），侧栏「运营」分组（在「AI任务」之后），标题「用户管理」。
- 该分组 `requiresOperator: true`：非运营不渲染；深链由 `router.ts` 的 `requiresOperator` 守卫拦回 `/dashboard`。
- 页面 = `WorkbenchHeader` + `FilterTabs`（全部/启用/停用）+ 搜索框 + `AppTable` 表纸 + 分页工具条 + 右侧 `el-drawer`。
- 单页制：**不新增详情路由**，所有动作都在抽屉里完成。

## 数据与权限

- HTTP 唯一出口是 `api.ts`（走 `shared/api-client`），端点全部在 `/api/ops/users/`：
  - `GET /ops/users/`（`page` / `page_size` / `keyword` / `active`）
  - `POST /ops/users/{id}/disable/`、`POST /ops/users/{id}/enable/`
  - `POST /ops/users/{id}/reset-password/`
- 分页在**服务端**：翻页与改每页条数都要重新请求，不在前端切片。
- 身份判定只读 `useAuthUser()`（`isOperator` / `isSuperuser`）；页面据此置灰不可管理的行，**服务端的 403 才是权威**。
- 列表按行开抽屉；停用/启用与重置密码都要先 `ElMessageBox` 二次确认。

## 样式

- 模块色 `--c-ops`（赭橙），表格强调色用 `accent="var(--c-ops)"`。
- 抽屉内容被 teleport 到 body：页面级 scoped 样式到不了，身份标签与状态样式由抽屉自己持有（与 serial-log 面板同一口径）。
- 字号、颜色、间距、圆角只用 `shared/styles/tokens.css` 的令牌。

## 红线

- **禁止**在页面里直接改本地状态冒充已保存：动作一律打接口，用响应回带的行替换。
- **禁止**新增删除账号、批量操作、授予运营的入口（属其它变更）。
- **禁止**把一次性密码写进日志、`localStorage` 或 URL；只在抽屉里显示，关闭即清空。
- **禁止**自己拼身份判定（如 `username === "admin"`），一律读 `useAuthUser`。

## 快速验证

```bash
cd frontend
npx vitest run tests/ops-console
npm run typecheck
npm run lint:styles
```
