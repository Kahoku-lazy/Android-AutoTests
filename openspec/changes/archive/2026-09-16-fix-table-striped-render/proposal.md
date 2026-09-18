## Why

变更 14 把 `element-locator` 的裸 `stripe` 改成 `:striped="true"` 后，Chromium 断言显示斑马纹**仍然不渲染**：奇数/偶数行底色都是 `rgb(255,255,255)`。根因与变更 1 修复行选中态时相同 —— 全局 `frontend/src/style.css` 的 `.el-table td { background: var(--app-bg-card) !important }` 压过了 EP 的条纹规则 `.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell { background: var(--el-fill-color-lighter) }`（后者特异性 (0,4,2) 但**无** `!important`，而 CSS 层叠中 importance 优先于特异性）。即：**全站任何表格的斑马纹都无法渲染**，与是否传 `striped` 无关。变更 14 因此留下一个未达成验收项（已登记为看板 #17）。

## What Changes

- 在共享皮肤中按变更 1 的同一手法补斑马纹规则：把条纹底色画在 `> td.el-table__cell` 上并带 `!important`，特异性高于全局规则
- 在 `tokens.css` 登记共享组件令牌 `--comp-table-row-striped-bg`（暖色纸面族派生，取代 EP 的冷灰 `#fafafa`）
- 规则顺序放在"选中行"规则**之前**，使选中态（含 EP `current-row`）仍优先于斑马纹
- **BREAKING**：无

## 关联文档

- 看板待纠正项 #17（第 10 轮发现）
- `dev_docs/DEV_TEST/前端UI风格一致性分析-2026-09.md` §3.1（同机制）
- 既有同机制修复：`openspec/changes/archive/2026-09-16-fix-l4-table-render`
- 本变更补齐的能力：`frontend-l4-data-surface`

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `frontend-l4-data-surface`：新增要求「斑马纹在请求时可见」

## Impact

- `frontend/src/shared/styles/tokens.css`（新增 1 条组件令牌）
- `frontend/src/shared/styles/workbench-theme.css`（新增斑马纹共享规则）
- 观感变化：全站传 `striped` 的表格首次出现斑马纹（`device-pool`、`report-generator` ×3、`element-locator` 页面元素表）
- 不影响：行选中态（仍优先）、`AppTable` 的 `striped → ep stripe` 映射契约、接口与数据

## 登记为后续输入

- `report-generator/constants.ts` 死导出清退、令牌与死 CSS 清退（变更 14 移出范围的部分）→ 另开批次