## Context

- 表纸皮肤在 `shared/styles/workbench-theme.css`：`.wb-shell .ac-table` 与 `.workflow-workbench .ac-table`。
- 全局 `style.css` 的 `.el-table th` 用 `!important` 设了表头底色与 2px 墨线，共享皮肤必须同优先级覆盖。
- `frontend-l4-data-surface` 原文要求「不出现可见行列线、表头 700」。

## Goals / Non-Goals

**Goals：**

- 表头变轻（无底色、1px 细线、600 字重、次要色），数据行用 1px ink 8% 分隔、行高加大。

**Non-Goals：**

- 不加列分隔线、不加斑马纹、不改表格结构/列宽/排序；不动模块自己的状态 chip。

## Decisions

### 1. 行线用 ink 系 `color-mix`，不用模块色

参考图的行线是中性灰。用 `color-mix(in srgb, var(--ink) 8%, transparent)` 既贴合纸面，也符合「模块色只做描边/装饰」的规则；表头线取 14% 稍重一档。

### 2. 覆盖全局表头必须带 `!important`

全局 `.el-table th` 的底色与 2px 底线都是 `!important`；共享皮肤的 `.wb-shell .ac-table th.el-table__cell` 特异性更高，但同样需要 `!important` 才能覆盖。

### 3. 行高用单元格 padding，不改 EP 行高变量

`padding: var(--app-space-md) 0` 对 EP 的 `.el-table__cell` 生效，避免依赖 EP 内部行高变量名。

## 模块防火墙自检

- 只改 `shared/styles/workbench-theme.css` 与 spec；无模块代码改动。

## Risks / Trade-offs

- [表格行数很多时 1px 行线可能显密] → 行线很浅（8%），且行高从默认提到 16px 上下内距，密度可控。
- [4 个列表页同时变化] → 这是表纸的统一皮肤，属于预期的一致性变化。
