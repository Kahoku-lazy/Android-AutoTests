# workflow 模块 AGENTS.md

> 全局边界 / 模板样式 / 协议要点 / 关单清单 → `../../AGENTS.md`；本文只写本模块增量，冲突以全局为准。

## 红线（全局表 workflow 行的展开）

| 只做 | 禁止 |
|------|------|
| 原型列表 → 原型内目录/页面流编排（VueFlow） | 执行测试 / 用例库同步 / 非本模块 import 本模块 Pinia stores |

- **VueFlow 节点图内部状态不能外部直接篡改**，否则可视化编排数据丢失；外部只能经适配层读写。
- Pinia stores（`workflowStore` / `libraryStore`）仅本模块使用，禁止其他模块 import。

## 本模块契约

**信封特例（非全局 `{status, data}`）**：legacy 端点（前端消费）为平铺 `{status, prototypes|directories, tree}` / `{status, document}`；DRF ViewSet 路由并存——双信封已登记 ARCH-09，收敛前禁止混改。

- 原型：`/workflow/prototypes*`（create / GET|POST|DELETE detail）
- 目录：`/workflow/directories*`（create 须 `prototype_id` 或 `parent_id`；更新删除走 `{ action }` / move `{ parent_id }`）
- 文档：`/workflow/documents*`（create 带 `prototype_id`；import 含 `overwrite`/`prototype_id`；move `{ directory_id }`；export GET）
- 跨模块素材（只读）：`/elements/pages` · `/elements/pages/{id}/items` · `/elements/web-groups` · `/elements/web`

## 本模块特殊布局/样式

- 路由：`/workflow` 原型列表 · `/workflow/prototypes/:prototypeId` 工作台
- **文档两类**：`page_flow`（UI 页面关系）· `api_flow`（接口串行/数据流转）——同目录分文件，画布不混排
- **节点**：页面流用 `StartNode` / `PageNode` / `PopupNode` / `EndNode`；接口流只用 `ApiNode` —— `registry/nodeRegistry.ts` 为唯一真相源

## 本模块协议要点

- VueFlow 状态经 `useVueFlowAdapter.ts` + Pinia stores 管理，组件不得直接篡改内部图状态。
- `libraryStore` 须先 `setPrototypeId` 再拉目录/文档。

## 关单附加项（全局清单的 delta）

```
[ ] 节点图状态只经适配层/stores，无外部直接篡改
[ ] 节点类型经 nodeRegistry，未散落定义
[ ] Pinia 未扩散到本模块之外
[ ] 目录/文档 CRUD 带 prototype_id 作用域
[ ] move/import body 字段 snake_case
```
