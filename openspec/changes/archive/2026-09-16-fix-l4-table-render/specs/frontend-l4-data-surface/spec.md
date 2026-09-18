## ADDED Requirements

### Requirement: Table row state stays visible

表格的行级状态（选中行、Element Plus 当前行）MUST 在视觉上可见。由于全局单元格底色带 `!important`，行状态底色 MUST 由共享规则画在 `> td.el-table__cell` 上并同样带 `!important`；系统 SHALL NOT 把行状态底色画在 `tr` 上（会被单元格底色遮盖）。行选中态的唯一类名 MUST 是 `is-selected`，由 `AppTable` 的 `row-class-name` 产出；模块 SHALL NOT 自建第二套行状态类名。行状态底色的色值 MUST 来自 `tokens.css` 已登记令牌。

#### Scenario: Selected row is highlighted

- **WHEN** 用户在 `/inspector` 的元素面板或结构面板点击一行
- **THEN** 该行单元格呈现选中底色，且与未选中行可区分
- **AND** 该底色不是声明在 `tr` 上

#### Scenario: Single shared selected-row class

- **WHEN** 检索全仓表格行状态实现
- **THEN** 唯一类名是 `is-selected`，并兼容 Element Plus 的 `current-row`
- **AND** 不存在 `pep-row--selected` / `sap-row--selected` / `page-row--active` 等模块私有行状态类

#### Scenario: Row state survives the global cell background

- **WHEN** 检查 `frontend/src/style.css` 的 `.el-table td` 规则与共享行选中规则
- **THEN** 共享行选中规则的层叠优先级高于单元格默认底色（选择器命中 `> td.el-table__cell` 且带 `!important`）
- **AND** 选中行在任何含表格页面都可见

### Requirement: Tables draw no visible grid lines

表格纸面 MUST NOT 呈现可见的行网格线与列网格线：模块色 SHALL NOT 用于行分隔线或列分隔线；系统 SHALL NOT 出现「以白色或近白色令牌（如 `--app-border-light`、`--color-white`）作为可见边框色」的声明。确需保留 1px 占位时 MUST 写作 `transparent` 并注明意图。表头排版 MUST 由全局与共享皮肤唯一定义（`--app-size-xs` / 700 / `uppercase`）；模块 SHALL NOT 覆写表头字号或字重。

#### Scenario: No module-specific separators

- **WHEN** 打开 `/devices` 表格视图与 `/elements` 的页面元素表
- **THEN** 两者都不出现彩色行分隔线或列分隔线
- **AND** 表格观感差异仅来自表纸强调色（`--c-device` / `--c-element`）与状态标识

#### Scenario: Header typography is single-sourced

- **WHEN** 比较 `/devices`、`/reports` 与 `/elements` 的表格表头计算样式
- **THEN** 字号、字重与大小写变换一致（12px / 700 / uppercase）
- **AND** 不存在模块私有的表头字号或字重覆盖

#### Scenario: White is never a visible border color

- **WHEN** 检索全仓表格样式中的边框色声明
- **THEN** 不存在以 `--app-border-light` 或 `--color-white` 作为可见行线/列线颜色的声明
- **AND** 保留占位的声明写作 `transparent` 并带意图注释