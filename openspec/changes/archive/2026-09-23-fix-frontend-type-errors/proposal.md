## Why

前端类型检查（`vue-tsc --noEmit`）当前有 **3 处报错**，全部集中在 `frontend/src/modules/case-manager/components/ProjectTree.vue` 的 el-tree 拖拽回调签名上：回调把参数声明为 `{ data?: UiTreeNode }`，而 Element Plus 的类型是 `Node`（其 `data` 为宽松的 `TreeNodeData`），因此三处回调都无法赋给组件的 props/事件类型。

这 3 处报错使类型检查长期为红，无法作为门禁使用（当前 CI 与本地门禁中该项均只告警）。

## What Changes

- `frontend/src/modules/case-manager/components/ProjectTree.vue`：把 `allowDrag` / `allowDrop` / `handleNodeDrop` 三个回调的参数类型对齐到 el-tree 的宽松入参，并在**唯一一处**收窄回 `UiTreeNode`（带注释说明树数据恒由 `toUiNodes()` 构造），避免每个回调各自断言。
- 不改动任何运行期行为：判定逻辑、事件语义、emit 载荷保持原样。
- **BREAKING**：无。

## 关联文档

无对应需求编号（未关联 PRD / ARCH）。本变更为前端类型缺陷修复，需求来源为门禁实跑发现的类型报错，已在 proposal 内完整描述。

## Capabilities

### New Capabilities

无。纯类型修复，不改变系统行为，按 schema 约定置 `skip_specs: true`。

### Modified Capabilities

无。

## Impact

- 仅影响 `frontend/src/modules/case-manager/components/ProjectTree.vue` 一个文件。
- 不涉及后端、API 契约、数据模型或依赖。
- 预期结果：`npm run typecheck`（vue-tsc）由 3 处报错转为 0，本地门禁告警项 `vue-tsc` 由 WARN 转 PASS。
