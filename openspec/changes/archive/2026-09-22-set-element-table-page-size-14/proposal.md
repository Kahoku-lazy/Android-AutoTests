## Why

上一单 `raise-element-table-page-size`（归档于 16:06）把每页行数由 7 提到 12。用户复核真实窗口后，把首屏行数定为 **14**。本单把生效规格与实现一起从 12 调到 14，避免规格与代码分叉。

## What Changes

- **每页行数 12 → 14**：`device-inspector/constants.ts` 的 `DEFAULT_PAGE_SIZE` 与 `PAGE_SIZE_OPTIONS` 同步为 14（该页固定单一取值）。
- 分页控件文案、「不提供显示行数选择器」、切换后回第 1 页的口径均不变。
- **用例随之调整**：改用 40 条元素（14 / 14 / 12 三页），保留「中间页满页 + 末页残余」的覆盖。

## 关联文档

- PRD-03（设备检查器）
- 上一单：`openspec/changes/archive/2026-09-22-raise-element-table-page-size`

## Capabilities

### Modified Capabilities

- `device-inspector-page`: 元素表格每页行数由 12 改为 14；表头全选的作用范围与分页示例随行数同步。

## Impact

- 前端：`frontend/src/modules/device-inspector/constants.ts`、`components/StructureAnalysisPanel.vue`（分页注释）
- 测试：`frontend/tests/device-inspector/p0/StructureAnalysisPanel.spec.ts`
- 不涉及：后端；`frontend-l4-data-surface` 不钉具体行数，故不改它
