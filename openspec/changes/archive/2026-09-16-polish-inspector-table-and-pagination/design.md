## Context

现状（读码核实；动机见 proposal.md - Why）：

- `device-inspector/components/SnapshotListDrawer.vue:47-55`：`el-button text type="danger"` 直接 `@click.stop="onDelete(s)"` → `store.deleteSnapshot(id)`（DELETE 端点 + 删文件），无确认。
- `shared/composables/usePagination.ts:31-63`：`currentPage` 只由 `goPage`（内部 clamp 到 `totalPages`）与 `setPageSize`（重置为 1）改动；`totalPages` 缩小时无人夹取 → `pagedItems` 切出空片。消费方：`device-pool`、`report-generator/index`、`report-generator/ReportDetail`、`device-inspector`。
- `device-pool/composables/useTableDragScroll.ts`（118 行）：外层 wrapper 横向滚 + 按拖平移，配套 CSS 在 `DevicePoolView.style.css:259-315`（`overflow-x:auto`、`min-width: var(--device-table-min-width)`、`:deep(.el-table__header-wrapper/.el-table__body-wrapper/.el-scrollbar__wrap){overflow-x:hidden}`、`is-pan-ready/is-dragging` 光标与 `pointer-events:none`）。
- 元素表列宽与间距字面量：列宽在 `StructureAnalysisPanel.vue:58-67`；间距在 `.sap-pager`（`gap:10px; padding-bottom:10px; min-height:38px`）、`.sap-body{gap:12px}`、`.sap-chip{margin-bottom:6px; padding:6px var(--app-space-sm)}`、`.sap-webview-hint{margin-bottom:10px}` 等处。
- `ai-assistant/ToolDebugPage.style.css:132`：`.td-input { … background: var(--app-bg) }`，`--app-bg` 全仓无声明（唯一引用）→ `lint:styles` 批 3 硬门禁失败。

## Goals / Non-Goals

**Goals:** 危险删除有确认；分页在任何数据变化下都不落空页（且修在共享层）；元素表横向滚动可用且首列常驻可见；元素表的列宽与间距有唯一登记处；全仓 `lint:styles` 的悬空令牌红灯消除。

**Non-Goals:** 不改后端与端点契约；不改设备管理页的表格结构/分页 UI（只享受共享夹取）；不收窄元素表列宽（用户已选「保留列宽」）；不引入 EP `fixed` 列；不动 `ai-assistant` 的其它在途改动。

## Decisions

### D1 删除确认用 Element Plus `ElMessageBox.confirm`

`SnapshotListDrawer.onDelete` 改为「先 confirm（危险态、文案写明快照与截图/缩略图文件不可恢复），确认后再调 `store.deleteSnapshot`」；取消分支（EP 以 reject 表示）直接 return，不弹错误。

- 备选：自建确认浮层 —— 否决：L5 覆盖层统一走 EP（`frontend/AGENTS.md`），且 EP 自带 ESC/焦点/键盘确认。

### D2 页码夹取放在共享 composable

`usePagination` 内加 `watch(totalPages, (tp) => { if (current.value > tp) current.value = tp })`。

- 为什么不 reset 到第 1 页：夹取不干扰用户主动翻页；「筛选变化回第 1 页」是页面语义（检查器面板已有自己的 watch），不应写进通用件。
- 备选：每个消费方各自 watch —— 否决：这正是「唯一分页实现」要避免的分散，且设备页上轮已漏。

### D3 拖拽平移提升到 shared

`device-pool/composables/useTableDragScroll.ts` → `shared/composables/useTableDragScroll.ts`；device-pool 的 import 改指共享件（1 行）。检查器接同一实现与同一套 CSS 口径（外层 wrapper 滚动 + el-table 内部 `overflow-x: hidden` + 表格 `min-width` 令牌）。

- 备选：从 device-inspector 直接 import device-pool 的内部件 —— 否决：跨模块内部实现 import，违反前端模块边界。

### D4 首列冻结用 CSS `position: sticky`

**不用** EP 的 `fixed` 列：它依赖 el-table 自身的横向滚动容器定位浮层，而本方案把横滚交给外层 wrapper（且 el-table 内部横滚被关掉），两者互斥。改为对前 3 列（`_select` 40 / `thumbnail` 66 / `name` 120）加 `position: sticky; left: 0 | 40px | 106px`；表格改 `table-layout="fixed"` 且前 3 列给显式 `width`，其余列保持 `minWidth`，让偏移量与列宽确定。

冻结单元格底色必须不透明，且要压过共享的斑马纹 / 悬停 / 行选中规则（它们对 `td.el-table__cell` 带 `!important`）：选择器带 `.sap-table-body` 前缀提升特异性并同样 `!important`，逐状态给底色（普通 / 斑马纹 / 悬停 / 选中）。

- 备选 A：EP `fixed` 列 + 保留 el-table 内部横滚 —— 否决：与 D3 的拖拽平移互斥（拖拽滚的是外层）。
- 备选 B：只做拖拽不平移、不冻结 —— 否决：用户明确要首列常驻。

### D5 列宽与间距登记

- 列宽：`constants.ts` 增 `ELEMENT_COLUMN_WIDTHS = { select: 40, thumbnail: 66, name: 120, label: 140, resourceId: 120, metrics: 150, xpath: 200, bounds: 150 }`，`ELEMENT_COLUMNS` 引用它。
- 间距：新建 `device-inspector/tokens.css`，登记 `--insp-gap-row: 10px`、`--insp-pad-filter: 10px 14px`、`--insp-pad-footer: 10px 20px`、`--insp-gap-panel: 12px`、`--insp-gap-chip: 6px`、`--insp-pager-min-h: 38px`、`--insp-hint-gap: 10px`，值与原字面量逐一相等（**视觉零变化**）；`index.vue` 的 `<style scoped>` 顶部 `@import './tokens.css';`（模块 tokens 文件已是仓库既有模式：ai-assistant / workflow / element-locator / case-manager）。
- 已登记的硬边几何（`2px` 描边/圆角、`48px` 缩略图边长、`8px` 滚动条）不在收编范围。

### D6 悬空令牌修复

`ToolDebugPage.style.css:132` 的 `var(--app-bg)` → `var(--app-bg-input)`（`.td-input` 是输入框，语义最近且已登记为白底）；只改这一行，不碰该文件的其余在途内容。

## 模块防火墙自检

- 改动全在前端；后端零改动、无迁移、无契约变更、无新端点。
- 跨模块 import 只减不增：`useTableDragScroll` 由 device-pool 内部件提升为共享件，device-pool 改指 `@/shared/composables/useTableDragScroll`。
- HTTP 出口仍是各模块 `api.ts` → `@/shared/api-client`；本次不新增请求（删除走既有 store 方法）。
- 共享件（`AppTable` / `EmptyState` / `FilterTabs`）与全局 `tokens.css` 不改；检查器样式仍落 `.inspector-workbench` 作用域，新增间距令牌落模块 tokens 文件。

## Risks / Trade-offs

- [冻结列底色被斑马纹 / 悬停 / 选中态覆盖，出现透底] → 选择器加 `.sap-table-body` 前缀 + `!important`，并在真机逐状态截图核对。
- [`table-layout="fixed"` 后列宽分布变化] → 前 3 列显式 `width`、其余 `minWidth`，真机量列宽与总宽核对（目标仍 ≈986px）。
- [拖拽平移误吞行点击] → composable 已有 `INTERACTIVE` 目标排除 + 拖动后吞掉一次 click；device-pool 已在用同一实现。
- [共享夹取影响 report-generator 分页] → 仅超界时生效；门禁跑全仓 build/typecheck，并真机看设备页与报告列表分页正常。
- [修改他人未跟踪文件（ai-assistant）] → 只改 1 行悬空令牌（用户明确要求）；不改其结构与其它样式。

## Migration Plan

纯前端改动：无数据迁移、无部署顺序。回滚 = 还原提交。门禁：`npm run lint:styles`（目标：本模块零违规，且该悬空令牌修复后全仓应转绿）、`npx vite build`、`npm run typecheck`（报错文件集不得新增）+ Playwright 真机走查（删除确认取消/确认、页码夹取、拖拽平移、首列冻结）。
