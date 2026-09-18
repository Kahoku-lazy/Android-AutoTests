## 1. 令牌与共享规则

- [x] 1.1 `tokens.css` 登记 `--comp-table-row-striped-bg: color-mix(in srgb, var(--color-orange-76) 25%, var(--app-bg-card))`；验证：`lint:styles` 批 2 通过（非原子声明无纯色字面量）
- [x] 1.2 `workbench-theme.css` 新增斑马纹共享规则（`.wb-shell` 与 `.workflow-workbench` 两个作用域），底色 `var(--comp-table-row-striped-bg) !important`；验证：选择器含 `> td.el-table__cell` 与 `!important`

## 2. 实施中修正的两处我自己的设计错误（如实登记）

- [x] 2.1 **选择器关系写错**：初版写成 `.ac-table .el-table--striped`（后代）。但 AppTable 把 `ac-table` 与 EP 的 `el-table--striped` 挂在**同一个元素**上（`<el-table class="ac-table">`），必须是**复合**选择器 `.ac-table.el-table--striped`。已修正
- [x] 2.2 **"选中优先"的机制判断错**：设计里写"规则置于选中规则之前，靠来源顺序决胜"，但实测条纹规则特异性 **(0,8,2)** 高于选中规则 **(0,5,2)**，两者同为 `!important` 时按特异性决胜 → 条纹压过选中（断言实测 `striped+selected` 与 `striped` 同色）。已改为用 `:not(.is-selected):not(.current-row)` 显式排除选中行，并更正 `design.md` 的 D3 表述

## 3. 门禁与验收

- [x] 3.1 `npm run lint:styles` 退出码 0；验证：批 1/2/3 全绿
- [x] 3.2 `npx vite build --mode development` 通过（`built in 33.62s`，退出码 0）；验证：既有无关报错未新增
- [x] 3.3 Chromium 断言（真实 EP CSS + `tokens.css` + `style.css` + `workbench-theme.css` + 复刻 DOM，**4 项全 PASS**）：① 条纹行 `color(srgb 0.9618 0.9559 0.9422)` ≠ 普通行 `rgb(255,255,255)`（**改动前两者均为白色**，复现全站斑马纹失效）；② 条纹底色非 EP 冷灰/白（取自登记令牌派生的暖色）；③ 条纹行加 `is-selected` 后回到选中底色 `color(srgb 0.9379 0.9181 0.9965)`，**选中优先于条纹**；④ 未加 `el-table--striped` 的表格两行同色，无误加条纹
- [x] 3.4 `git diff --name-only` 仅 2 个样式文件（`tokens.css` / `workbench-theme.css`），与 `proposal.md` 的 Impact 段一致
