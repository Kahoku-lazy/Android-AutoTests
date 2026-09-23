## Context

动机见 proposal.md。现状（2026-09-23 实测）：

- `npx vue-tsc --noEmit` 输出 3 处 `TS2322`，全部在 `ProjectTree.vue`（430 / 431 / 434 行，对应模板上的 `:allow-drag` / `:allow-drop` / `@node-drop`）。
- 现有回调签名：`allowDrag(node: { data?: UiTreeNode })`、`allowDrop(_draggingNode: unknown, dropNode: { data?: UiTreeNode }, type: string)`、`handleNodeDrop(draggingNode: { data?: UiTreeNode }, dropNode: { data?: UiTreeNode }, dropType: 'before'|'after'|'inner')`。
- Element Plus 的期望类型：`AllowDragFunction = (node: Node, event: DragEvent) => boolean`、`AllowDropFunction = (draggingNode: Node, dropNode: Node, type, evt) => boolean`、`node-drop: (draggingNode: Node, dropNode: Node, dropType, evt) => void`，其中 `Node.data` 为 `TreeNodeData`（`Record<string, any>`）。
- 运行时事实：树的 `:data` 恒为 `elTreeData`，由本文件的 `toUiNodes()` 构造，因此 `data` 一定是 `UiTreeNode`。
- 约束：`frontend/tsconfig.json` 未开 `strict`，`strictFunctionTypes` 亦为 false，故参数按双变（bivariant）比较——把参数放宽到能接受 `Node` 即可通过，无需与库类型完全一致。

## Goals / Non-Goals

**Goals:**

- 消除 3 处类型报错，使 `vue-tsc` 可作为门禁使用。
- 收窄点唯一、带注释，避免后续每加一个回调就再写一次断言。

**Non-Goals:**

- 不开启 `strict` / `strictNullChecks` / `noImplicitAny`（会引入大量存量报错，属独立议题）。
- 不改动拖拽的判定逻辑与事件语义。
- 不重构 `ProjectTree.vue`（其体积超标由另一变更处理）。

## Decisions

### 决策 1：把回调入参放宽为局部类型 `ElTreeNode = { data?: unknown }`，在 `uiDataOf()` 内收窄

- 理由：库的 `Node` 类型未从 `element-plus` 稳定导出为公共 API，直接 import 其内部路径（`element-plus/es/components/tree/src/model/node`）会绑死实现细节；用结构化的宽松类型即可满足双变比较。
- 备选一：每个回调内部各自 `as UiTreeNode` 断言。被否——断言散落三处，后续新增回调会继续复制，且失去统一的防空判断。
- 备选二：声明 `allowDrag(node: any)`。被否——等同于关闭该处类型检查，不符合"可机械验证"的方向。

### 决策 2：`uiDataOf()` 做最小结构校验（`type` 与 `key` 存在）后才返回 `UiTreeNode`

- 理由：库类型允许 `data` 为任意对象，直接断言不设防；校验两个判别字段后返回，既能满足类型收窄，也保留了对空节点的原有防空行为（原实现为 `!!node?.data`，未做字段校验，但树数据恒由 `toUiNodes()` 构造，因此不改变实际行为）。
- 备选：不校验、直接 `as UiTreeNode`。被否——与决策 1 的"不关闭类型检查"取向矛盾。

## 模块防火墙自检

本变更只改一个前端组件的类型标注：

- 跨 App import：不涉及（前端改动，无后端 import）。
- 跨 App import service / runner / consumer / state_machine：不涉及。
- INSERT / UPDATE / DELETE 收敛到 api.py：不涉及（无写库行为）。
- 前端不直连数据库、仪表盘不做写操作：不涉及（组件仅渲染与 emit 事件，HTTP 仍走模块 `api.ts`）。

无新增跨模块依赖。

## Risks / Trade-offs

- [收窄校验比原实现更严，可能把某些节点判为无效] → 树数据只由 `toUiNodes()` 生成，`type` 与 `key` 必存在；且 `handleNodeClick` 等其余路径不受影响。验证方式：`npm run typecheck` 通过 + 前端测试（含 case-manager 相关）通过 + 构建通过。
- [Element Plus 升级后签名变化] → 宽松入参对该变化更耐受；若将来库导出稳定 `Node` 类型，可再收敛。

## Migration Plan

- 生效方式：合并后 `vue-tsc` 即通过，无部署步骤。
- 验证：`cd frontend && npm run typecheck`（预期 0 报错）；`npm test` 与 `npx vite build` 保持通过。
- 回滚：还原该文件的类型标注即可，单文件改动。
