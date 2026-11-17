# 数据展示规格 — 表格皮肤 / 表纸 / 分页

**以代码为准**：`frontend/src/style.css`（EP 全局覆盖）+ `shared/components/AppTable.vue` + `shared/styles/workbench-theme.css`。令牌值见 [../tokens.md](../tokens.md)。

> **作用域警示**：斑马纹与表纸皮肤**只在 `.wb-shell` 内生效**。

## 1. Table 表格（EP 全局皮肤）

| 维度 | 实际规格 |
|------|----------|
| 表头 | 底 `--app-bg-subtle`、字 `--ink`、字重 700、`uppercase` + `letter-spacing .04em`、下框 `2px solid var(--ink)`；**字号见 §1.1（16px，设备/BUG 页已落地）**，全局默认仍是 `--app-size-xs` |
| 单元格 | 底 `--app-bg-card`、下框 `1px solid transparent`（保行高，**不画网格线**）|
| hover 行 | 底 `--paper` |
| 斑马纹 | `--comp-table-row-striped-bg`（`color-mix(--color-orange-76 25%, 白)`）；**只在 `.wb-shell .ac-table` 下生效**，画在 `> td` 上并排除选中行 |
| 选中行 | `--comp-table-row-selected-bg`（`color-mix(--c-element 18%, 白)`，模块可覆写 accent）；类名唯一 `is-selected`（兼容 EP `current-row`）|
| 圆角 / 外框 | 圆角 `--app-radius-table`（`4px 10px`）+ `overflow: hidden`；外框**未覆盖** |
| 表纸皮肤（`AppTable` 传 `accent`）| `.sketch-sheet`：框 `--comp-sheet-border`（`1px solid --color-ink-79`）、底 `--comp-sheet-bg` 白、圆角 `--comp-sheet-radius`（`2px 6px 2px 4px`）、硬影 `4px 4px 0 0 <accent>`、**表体不旋转**（显式 `transform: none`）|
| 已登记例外 | ① device-pool 把表纸线型改成**实线**（只改 `border-style`）；② device-pool 用**无影变体**（`box-shadow: none`），描边与圆角不变，见 §2.1 |

**约束**：只用共享 `AppTable`（禁原生 `el-table`、禁第二套通用表封装）；扁列表**不得**再套 `el-card`，需要分组容器时用 `.doc-section` 或 `AppCard`；高度（固定表头）由页面通过 `height` 属性透传；加载走 `loading`，空态走 `emptyText` / `#empty` 插槽。

### 1.1 表格字号三档（2026-11 需求方设定，跨模块统一）

| 位置 | 字号 | 说明 |
|------|------|------|
| **列头**（`th`） | **16px**（`--app-size-md`） | 单行不折：`white-space: nowrap` 要加在 `th .cell` 上（EP 把文字包在 `.cell` 里）；列宽按 16px 复核 |
| **单元格文本** | **14px**（`--app-size-sm`） | 型号 / 编号 / 标题、状态与分类标签、胶囊、分辨率、操作键文案、**单行的情况下也是 14px** |
| **时间 / 日期** | **12px**（`--app-size-xs`） | **仅当它是格内第二行**（该格因此占两行）时用 12，例如「11 分钟前」下的「接入 2026-11-17 14:38:49」 |
| **时间 / 日期（单行）** | **14px** | 时间日期是该格**唯一内容**、格子只占一行时，按正文档给 14，**不要**因为「它是时间」就压到 12 |

**判定口诀**：先看这一格占几行 —— 两行且其中一行是时间 → 时间那行 12；只占一行（无论内容是不是时间）→ 14。

**落地现状**：

- 已按三档实现：设备管理（`device-pool/DevicePoolView.style.css` + `DeviceIdentityCell.vue` + `DeviceActionsCell.vue`）、BUG 单管理（`bug-manager/index.style.css` + `BugIdentityCell.vue`）。
- **存量待迁移**：其余表格的表头仍是全局 `12px`（报告 / 用例 / 任务清单 / 运营等）。迁移时按本节三档改，并同步该页的列宽与 `nowrap`，不要只改字号导致表头折行。

**自检**：列头 16 且单行；正文与操作键 14；格内第二行的时间 12；单行时间 14；全部取 `--app-size-*` 令牌，不写字号字面量。

## 2. AppTable 表纸

- **props**：`columns` / `dataSource` / `rowKey`(默认 `id`) / `striped` / `border` / `loading` / `emptyText`(默认「暂无数据」) / `tableLayout` / `rowClassName` / `accent`
- **能力**：`columns[].children` 分组表头 · `#header-<prop>` 自定义表头 · `#cell-<prop>` 单元格 · `ref.tableRef` 取底层实例 · `$attrs` 透传 `height` 等 EP 原生属性
- 斑马纹与选中行底色画在 `> td.el-table__cell` 上并带 `!important`（因为全局单元格底色也是 `!important`）
- 全仓**只有这一套**通用表：禁原生 `el-table`、禁第二套封装

### 2.1 无影变体（device-pool，2026-11 登记）

`/devices` 表格的表纸**不绘制硬影**，只留共享描边与圆角：

```css
.device-workbench :deep(.sketch-sheet) {
  border-style: solid; /* 实线：本页登记的线型 */
  box-shadow: none;    /* 无影：本页登记的变体 */
}
```

- **只在此作用域生效**：共享 `.wb-shell .sketch-sheet` 的硬影声明不得修改——同一套皮肤另有 9 处消费方（报告 / 用例 / 缺陷 / 运营 ×3 / 串口日志 ×2 / 用例预览）。
- 描边宽度、颜色与圆角仍取 `--comp-sheet-border` / `--comp-sheet-radius`；模块不得写宽度 / 颜色 / 圆角的字面量。
- 去影**不波及表内按钮**：`el-button` 的 2px 位移硬影保留。
- 规范出处：`openspec/specs/frontend-doodle-sketch-table` 的「Device page paper uses the shadowless variant」。

## 3. Pagination 分页

项目**不使用 EP 分页组件皮肤**，统一走共享 `usePagination` + 自绘控件：

- 取数：`usePagination(source, { pageSize, options })` → `currentPage / totalPages / pagedItems / goPage / setPageSize`
- 文案：「第 X / Y 页 · 共 N 条」，按钮「上一页 / 下一页」（`el-button size="small"`，到边界禁用）
- 选项集与默认每页行数来自模块 `constants.ts`（固定行数的页只登记单一取值）
- 数据源缩小导致页数减少时，由 composable 自动夹取 `currentPage`——页面**不得**自算 `totalPages` / 自写 `goPage`
