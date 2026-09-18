## 1. AppTable 能力扩展

- [x] 1.1 `shared/components/AppTable.vue`：支持 `columns[].children` 分组表头（渲染函数递归）、`#header-<prop>` 插槽、`defineExpose({ tableRef })`、`inheritAttrs:false` + `$attrs` 透传；验证：4 个既有消费方（`report-generator` ×3 · `device-pool` ×1）行为不变，`vue-tsc` 无错

## 2. 三处例外迁回

- [x] 2.1 `device-inspector/components/PageElementsPanel.vue`：改为 `AppTable` + 列定义（含 `children` 分组与选择列），表头复选框走 `#header-_select`、行复选框走 `#cell-_select`，透传 `height` / `header-cell-style` / `@row-click`；验证：dump/OCR 分组表头、全选与行选中、行点击高亮均与迁移前一致
- [x] 2.2 `device-inspector/components/StructureAnalysisPanel.vue`：改为 `AppTable`（7 列 + `@row-click` + `row-class-name`）；验证：列内容与行选中高亮一致
- [x] 2.3 `element-locator/components/PageElementsWorkbench.vue`：改为 `AppTable`，`tableRef.value?.tableRef?.$el` 与 `setCurrentRow` 改走新暴露；验证：截图↔表格滚动联动与当前行高亮一致
- [x] 2.4 全仓复核无原生 `el-table` 消费；验证：`rg -n "<el-table" frontend/src` 仅命中 `shared/components/AppTable.vue`

## 3. 规格与速查同步

- [x] 3.1 以 MODIFIED 更新 `specs/frontend-l4-data-surface/spec.md` 的表格需求（例外场景改为「能力已补齐、例外归零」）；验证：`openspec validate --strict` 通过
- [x] 3.2 更新 `frontend/AGENTS.md` L4 速查 §③.2 / §⑤ / §⑥：例外判据改为「AppTable 已覆盖分组/表头插槽/实例/透传」，`<el-table` 判据由 4 文件改为 1 文件，已知缺口 ① 移除；验证：速查与 spec 一致

## 4. 门禁与归档

- [x] 4.1 `cd frontend && npm run typecheck`；验证：全仓 34 个既有错误，4 个改动文件零错误
- [x] 4.2 用 `vue-frontend-check` 过 4 个改动文件；验证：改动行无新增违规；删除行经 git diff 逐行核对无脚本代码丢失
- [x] 4.3 归档（经 `openspec-archive-change`）；验证：`openspec/specs/frontend-l4-data-surface/spec.md` 已更新，变更进入 archive
