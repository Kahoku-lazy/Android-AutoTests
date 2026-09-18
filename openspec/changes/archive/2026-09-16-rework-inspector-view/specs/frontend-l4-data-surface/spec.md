## MODIFIED Requirements

### Requirement: Table row state stays visible

表格的行级状态（选中行、Element Plus 当前行）MUST 在视觉上可见。由于全局单元格底色带 `!important`，行状态底色 MUST 由共享规则画在 `> td.el-table__cell` 上并同样带 `!important`；系统 SHALL NOT 把行状态底色画在 `tr` 上（会被单元格底色遮盖）。行选中态的唯一类名 MUST 是 `is-selected`，由 `AppTable` 的 `row-class-name` 产出；模块 SHALL NOT 自建第二套行状态类名。行状态底色的色值 MUST 来自 `tokens.css` 已登记令牌。

#### Scenario: Selected row is highlighted

- **WHEN** 用户在 `/inspector` 的结构表格（页面分区 + 元素表格唯一视图）点击一行
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
