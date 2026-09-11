# element-locator 模块 AGENTS.md

> 全局边界 / 模板样式 / 协议要点 / 关单清单 → `../../AGENTS.md`；本文只写本模块增量，冲突以全局为准。

## 红线（全局表 element-locator 行的展开）

| 只做 | 禁止 |
|------|------|
| 三系统项目下的目录/叶子 CRUD（页面/Web 元素/API 端点） | 实时截图 dump / 执行测试 / 三域数据互串 / 新建或删除系统项目 |

- **dump 结果字段**：`_idx` / `_xpaths` / `_testpoint` 前缀字段不能用错，否则元素数据错乱。
- 实时截图流已迁设备检查器（快照式），本模块不做截图。
- 页面 / Web 元素 / API 端点各归对应项目，禁止互相串联。
- 系统项目 `android` / `web` / `api` 锁定，前端不提供创建/删除/改名。

## 本模块契约（端点有增删必须同改此处）

- 路由：`/elements` 项目列表 · `/elements/projects/:code` 工作台 · `/elements/projects/:code/files/:fileId` 深链
- 旧路径 `/elements/android|web|api`、`/element-mgr` → 重定向到对应项目
- 项目/目录：`GET /elements/projects/` · `GET /elements/projects/{code}/tree/` · `POST/PATCH/DELETE /elements/directories/`
- 移动/批量删：`POST /elements/move/` `{kind,id,parent_directory_id?}` · `POST /elements/files/batch-delete/` `{kind,ids}`
- 叶子创建仍走 legacy：`POST /elements/pages/create` · `/elements/web/create` · `/elements/api-endpoints/create`（带 `directory_id`）
- 页面元素：`/elements/pages/{pid}/items` · `/elements/pages/{pid}/elements[/batch]`
- 批量移动 body 为 **snake_case**：`page_ids` / `group_ids` / `parent_id`；批量导入 `{ elements }` / `{ elements, strategy }`
- 项目/目录/move 走标准 `{status,data}`；pages/web/api-endpoints legacy 仍为平铺信封

## 本模块协议要点

- 项目化 composable：`useLocatorProjects` / `useLocatorTree` 管列表与目录树。
- 旧三域树（`useElementTree` / `useWebGroupTree` / `useApiGroupTree`）与遗留管理器已删除（见变更 `remove-legacy-element-locator-managers`）；项目树 `useLocatorTree` 为唯一树实现，禁止再引入第二棵树。

## 关单附加项（全局清单的 delta）

```
[ ] dump 结果 _idx/_xpaths/_testpoint 前缀字段使用正确
[ ] batch-move / batch-import / move / batch-delete body 字段 snake_case
[ ] 三域资产互不串联；树状态不跨域共享
[ ] 侧栏单项 /elements；旧三路径与 /element-mgr 已重定向
```
