# element-locator 模块 CLAUDE.md

> 全局边界 / 模板样式 / 协议要点 / 关单清单 → `../../CLAUDE.md`；本文只写本模块增量，冲突以全局为准。

## 红线（全局表 element-locator 行的展开）

| 只做 | 禁止 |
|------|------|
| 三域资产 CRUD（页面/元素/分组/端点/跳转流） | 实时截图 dump / 执行测试 / 三域数据互串 |

- **dump 结果字段**：`_idx` / `_xpaths` / `_testpoint` 前缀字段不能用错，否则元素数据错乱。
- 实时截图流已迁设备检查器（快照式），本模块不做截图。
- 页面 / Web 元素 / API 分组三域资产各归各域，禁止互相串联。

## 本模块契约（端点有增删必须同改此处）

- 页面：`/elements/pages`（GET/POST `/create`/PUT/DELETE）· `/elements/pages/{pid}/items` · `/elements/pages/{pid}/elements[/batch]`
- 三域分组：`/elements/web-groups*` · `/elements/api-groups*` · `/elements/web*` · `/elements/api-endpoints*` · `/elements/web-flows*` · `/elements/flows*`
- 批量移动 body 为 **snake_case**：`page_ids` / `group_ids` / `parent_id`；批量导入 `{ elements }` / `{ elements, strategy }`

## 本模块协议要点

- 三域树 composable：`useElementTree` / `useWebGroupTree` / `useApiGroupTree` 各管一域，禁止跨域复用同一份树状态。

## 关单附加项（全局清单的 delta）

```
[ ] dump 结果 _idx/_xpaths/_testpoint 前缀字段使用正确
[ ] batch-move / batch-import body 字段 snake_case
[ ] 三域资产互不串联；树状态不跨域共享
```
