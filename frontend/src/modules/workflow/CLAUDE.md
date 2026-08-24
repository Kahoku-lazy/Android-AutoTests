# workflow 模块 CLAUDE.md

> 全局边界 / 模板样式 / 协议要点 / 关单清单 → `../../CLAUDE.md`；本文只写本模块增量，冲突以全局为准。

## 红线（全局表 workflow 行的展开）

| 只做 | 禁止 |
|------|------|
| 页面流节点图编排（VueFlow 5 类节点 + 目录/文档管理） | 执行测试 / 用例库同步 / 非本模块 import 本模块 Pinia stores |

- **VueFlow 节点图内部状态不能外部直接篡改**，否则可视化编排数据丢失；外部只能经适配层读写。
- Pinia stores（`workflowStore` / `libraryStore`）仅本模块使用，禁止其他模块 import。

## 本模块契约

**信封特例（非全局 `{status, data}`）**：legacy 端点（前端消费）为平铺 `{status, directories, tree}` / `{status, document}`；DRF ViewSet 路由（未消费）**无 status 信封**——双信封并存已登记 ARCH-09 §1.5 / PRD-09 §4.1，收敛前禁止混改。

- 目录：`/workflow/directories*`（create / 更新删除走 `{ action }` / move body `{ parent_id }`）
- 文档：`/workflow/documents*`（create 不带 `doc_id` 即新建、带则更新；import body 含 `overwrite`；move body `{ directory_id }`；export 走 GET）
- 跨模块素材（只读）：`/elements/pages` · `/elements/pages/{id}/items` · `/elements/web-groups` · `/elements/web`

## 本模块特殊布局/样式

- **节点 5 类**：`StartNode` / `PageNode` / `PopupNode` / `ApiNode` / `EndNode` —— `registry/nodeRegistry.ts` 为唯一真相源（含默认端口/最大实例数/配色），新增节点类型只准改 registry。

## 本模块协议要点

- VueFlow 状态经 `useVueFlowAdapter.ts` + Pinia stores 管理，组件不得直接篡改内部图状态。

## 关单附加项（全局清单的 delta）

```
[ ] 节点图状态只经适配层/stores，无外部直接篡改
[ ] 节点类型经 nodeRegistry，未散落定义
[ ] Pinia 未扩散到本模块之外
[ ] move/import body 字段 snake_case
```
