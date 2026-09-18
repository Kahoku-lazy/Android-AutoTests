## Why

L5 契约（`frontend-l5-overlay`）已确立「阻塞层统一走 EP」，但两处细节仍不对齐：① **`.el-drawer` 没有任何全局皮肤** —— `style.css` 只给 `.el-dialog` / `.el-message` 上了涂鸦外观，两个抽屉（`SnapshotListDrawer` / `KnowledgePreviewDrawer`）退回 EP 默认外观，与对话框不同源；② 19 处弹层的可见性绑定实测有 4 类写法，其中 3 处是「`:model-value` + `@update:model-value` 纯写回」—— 这正是 `v-model` 的展开写法，属多余噪声。

实测结论（19 处逐一核对）：其余写法由**状态归属**决定，无法也不应统一成一种 —— 8 处本地 `ref` 用 `v-model`、3 处 store 状态纯写回（即本变更要收敛的噪声）、3 处可见性由条件表达式派生或关闭需联动清理、5 处薄封装由父组件持有可见性并 emit 领域事件。

## What Changes

- `style.css` 新增 `.el-drawer` 全局皮肤，与 `.el-dialog` 同语言（近直角圆角 `6px 10px 6px 10px` + `2.5px` 墨色边 + 裁切），使抽屉与对话框视觉同源
- 3 处「纯写回」绑定收敛为 `v-model`（等价简化，行为不变）：`SavedPagePicker.vue`、`SaveToElementsDialog.vue`、`SnapshotListDrawer.vue` 的 `:model-value="store.x"` + `@update:model-value="(v) => (store.x = v)"` → `v-model="store.x"`
- `frontend-l5-overlay` spec 新增 2 条需求：**覆盖层可见性绑定按状态归属**、**阻塞层皮肤对称**
- `frontend/AGENTS.md` L5 速查：② 代码范围补 `.el-drawer`、③ 写明绑定口径、⑥ 更新判据与已知缺口
- **明确不改**：5 处薄封装组件的对外契约（`:model-value="visible"` + 领域事件）与 3 处派生可见性绑定 —— 它们由状态归属决定，强行统一会破坏语义
- **BREAKING**：无。组件 props / emits / 调用方均不变；抽屉外观为**有意统一**（可见变化，需浏览器核验）

## 关联文档

- `openspec/specs/frontend-l5-overlay/spec.md`：本变更新增需求所在
- `openspec/changes/archive/2026-09-14-converge-l5-overlay-language/`：L5 底座收敛（原生 confirm 与自建 modal）与「薄封装是收敛方向」的裁决出处
- `frontend/AGENTS.md` L5 速查 §②/③/⑥：皮肤归属与绑定口径的登记处
- 说明：`dev_docs/文档编号对照表.md` 不存在；本变更为前端覆盖层实现对齐，不改业务需求

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `frontend-l5-overlay`: 新增 2 条需求 —— 「Overlay visibility binding follows state ownership」与「Blocking overlay skins are symmetric」

## Impact

- `frontend/src/style.css`（新增 `.el-drawer` 皮肤）
- `frontend/src/modules/device-inspector/components/SavedPagePicker.vue` · `SaveToElementsDialog.vue` · `SnapshotListDrawer.vue`
- `openspec/specs/frontend-l5-overlay/spec.md`（归档时更新）· `frontend/AGENTS.md`（L5 速查 3 处）
- 测试与门禁：`vue-tsc --noEmit`；`vue-frontend-check` 过改动文件；两个抽屉的浏览器目视（本环境无浏览器，记录为待补）
- 不影响：其余 16 处弹层的绑定与外观、`ElMessage` 皮肤、后端接口、路由表
