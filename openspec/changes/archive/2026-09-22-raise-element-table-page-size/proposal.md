## Why

元素表容器撑满结构栏（`StructureAnalysisPanel.css:88-94`：`.sap-table-body` 为 `flex: 1`、表格传 `height="100%"`），而每页固定 7 行（`constants.ts:4-5`）在常见窗口高度下占不满，表格下方留出一片空白 —— 用户真机反馈「表格下方还有大量空白，这些空白可以按需多显示几行」。

## What Changes

- **每页行数 7 → 12**：`device-inspector/constants.ts` 的 `DEFAULT_PAGE_SIZE` 与 `PAGE_SIZE_OPTIONS` 同步为 12（该页固定单一取值，选项集仍只登记一项）。
- 分页控件文案（「第 X / Y 页 · 共 N 条」与上一页 / 下一页）与「不提供显示行数选择器」的口径不变。
- **不改**：列宽与间距、表格定高策略、分组选择与圈选逻辑、勾选范围口径。

## 关联文档

- PRD-03（设备检查器）

## Capabilities

### Modified Capabilities

- `device-inspector-page`: 元素表格每页行数由 7 改为 12；表头全选的作用范围与分页示例随行数同步。

## Impact

- 前端：`frontend/src/modules/device-inspector/constants.ts`（行数的唯一登记处）、`components/StructureAnalysisPanel.vue`（分页注释里的行数说明）
- 测试：`frontend/tests/device-inspector/p0/` 新增挂载面板的用例，断言首屏 12 行与分页文案
- 不涉及：后端；`frontend-l4-data-surface` 明确该能力不钉具体行数（行数由 `device-inspector-page` 定义），故不改它
