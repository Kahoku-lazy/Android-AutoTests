# 数据展示规格 — 表格皮肤 / 表纸 / 分页

**以代码为准**：`frontend/src/style.css`（EP 全局覆盖）+ `shared/components/AppTable.vue` + `shared/styles/workbench-theme.css`。令牌值见 [../tokens.md](../tokens.md)。

> **作用域警示**：斑马纹与表纸皮肤**只在 `.wb-shell` 内生效**。

## 1. Table 表格（EP 全局皮肤）

| 维度 | 实际规格 |
|------|----------|
| 表头 | 底 `--app-bg-subtle`、字 `--ink`、字重 700、字号 `--app-size-xs` + `uppercase` + `letter-spacing .04em`、下框 `2px solid var(--ink)` |
| 单元格 | 底 `--app-bg-card`、下框 `1px solid transparent`（保行高，**不画网格线**）|
| hover 行 | 底 `--paper` |
| 斑马纹 | `--comp-table-row-striped-bg`（`color-mix(--color-orange-76 25%, 白)`）；**只在 `.wb-shell .ac-table` 下生效**，画在 `> td` 上并排除选中行 |
| 选中行 | `--comp-table-row-selected-bg`（`color-mix(--c-element 18%, 白)`，模块可覆写 accent）；类名唯一 `is-selected`（兼容 EP `current-row`）|
| 圆角 / 外框 | 圆角 `--app-radius-table`（`4px 10px`）+ `overflow: hidden`；外框**未覆盖** |
| 表纸皮肤（`AppTable` 传 `accent`）| `.sketch-sheet`：框 `--comp-sheet-border`（2.5px dashed 墨）、底 `--comp-sheet-bg` 白、圆角 `--comp-sheet-radius`（`2px 6px 2px 4px`）、硬影 `4px 4px 0 0 <accent>`、**表体不旋转**（显式 `transform: none`）|
| 已登记例外 | device-inspector / device-pool / element-locator 三页把表纸虚线改成**实线**（只改 border-style）|

**约束**：只用共享 `AppTable`（禁原生 `el-table`、禁第二套通用表封装）；扁列表**不得**再套 `el-card`，需要分组容器时用 `.doc-section` 或 `AppCard`；高度（固定表头）由页面通过 `height` 属性透传；加载走 `loading`，空态走 `emptyText` / `#empty` 插槽。

## 2. AppTable 表纸

- **props**：`columns` / `dataSource` / `rowKey`(默认 `id`) / `striped` / `border` / `loading` / `emptyText`(默认「暂无数据」) / `tableLayout` / `rowClassName` / `accent`
- **能力**：`columns[].children` 分组表头 · `#header-<prop>` 自定义表头 · `#cell-<prop>` 单元格 · `ref.tableRef` 取底层实例 · `$attrs` 透传 `height` 等 EP 原生属性
- 斑马纹与选中行底色画在 `> td.el-table__cell` 上并带 `!important`（因为全局单元格底色也是 `!important`）
- 全仓**只有这一套**通用表：禁原生 `el-table`、禁第二套封装

## 3. Pagination 分页

项目**不使用 EP 分页组件皮肤**，统一走共享 `usePagination` + 自绘控件：

- 取数：`usePagination(source, { pageSize, options })` → `currentPage / totalPages / pagedItems / goPage / setPageSize`
- 文案：「第 X / Y 页 · 共 N 条」，按钮「上一页 / 下一页」（`el-button size="small"`，到边界禁用）
- 选项集与默认每页行数来自模块 `constants.ts`（固定行数的页只登记单一取值）
- 数据源缩小导致页数减少时，由 composable 自动夹取 `currentPage`——页面**不得**自算 `totalPages` / 自写 `goPage`
