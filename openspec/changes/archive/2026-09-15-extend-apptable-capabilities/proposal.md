## Why

`frontend-l4-data-surface` spec 规定「表格首选 `AppTable`」，仅当需要**多级分组表头** / **选择列** / **底层 `TableInstance`** 时可用原生 `el-table` 并登记例外。现有 3 处例外（`PageElementsPanel` / `StructureAnalysisPanel` / `PageElementsWorkbench`）长期占用该豁免，且两处图片放大预览之外，它们是新页面最可能的模仿对象——豁免不收敛就会继续扩散。

实测这 3 处对 `AppTable` 的能力诉求是有限且通用的：`columns[].children` 分组表头、`#header-<prop>` 自定义表头（全选复选框）、`defineExpose` 底层实例（`scrollTo` / `setCurrentRow` / `$el`）、`$attrs` 透传（`height` / `header-cell-style` / `@row-click`）。有 3 个真实消费方，符合「抽 shared 件」规则。

## What Changes

- `shared/components/AppTable.vue` 扩展 4 项能力：① `columns[].children` 递归渲染分组表头（层级不限）② 新增 `#header-<prop>` 表头插槽 ③ `defineExpose({ tableRef })` 暴露底层 `TableInstance` ④ `inheritAttrs: false` + `v-bind="$attrs"` 透传，使 `height` / `header-cell-style` / `@row-click` 等直接可用
- `device-inspector/components/PageElementsPanel.vue`：迁回 `AppTable`（dump / OCR 两级分组 + 选择列改为 `#header-_select` / `#cell-_select`）
- `device-inspector/components/StructureAnalysisPanel.vue`：迁回 `AppTable`（7 列扁平 + 行点击/行类名）
- `element-locator/components/PageElementsWorkbench.vue`：迁回 `AppTable`（经 `tableRef` 取底层实例做滚动定位与 `setCurrentRow`）
- **BREAKING**：无。`AppTable` 既有 props / 插槽语义与默认行为不变（新增能力均为可选）；3 处迁移后渲染结果与交互保持

## 关联文档

- `openspec/specs/frontend-l4-data-surface/spec.md`：修改「Shared AppTable is the default table implementation」
- `openspec/changes/archive/2026-09-15-add-l4-spec-and-l4-l5-quickref/`：3 处例外的登记出处
- `frontend/AGENTS.md` L4 速查 §③.2 / §⑤ / §⑥：例外判据与缺口的登记处
- 说明：`dev_docs/文档编号对照表.md` 不存在；本变更为前端共享件能力扩展，不改业务需求

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `frontend-l4-data-surface`: 「Shared AppTable is the default table implementation」的例外场景由「3 处登记例外」改为「能力已补齐、例外归零」

## Impact

- `frontend/src/shared/components/AppTable.vue` · `modules/device-inspector/components/PageElementsPanel.vue` · `modules/device-inspector/components/StructureAnalysisPanel.vue` · `modules/element-locator/components/PageElementsWorkbench.vue`
- `openspec/specs/frontend-l4-data-surface/spec.md`（归档时更新）· `frontend/AGENTS.md`（L4 速查 §③/⑤/⑥）
- 测试与门禁：`vue-tsc --noEmit`；`vue-frontend-check` 过 4 个改动文件；检查器两表与元素工作台三档宽度浏览器核验（本环境待补）
- 不影响：其余 4 个 `AppTable` 消费方（`report-generator` ×3 · `device-pool` ×1）、后端接口、路由表
