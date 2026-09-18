## ADDED Requirements

### Requirement: Table zebra striping is visible when requested

当表格请求斑马纹（`AppTable` 的 `striped` 为真，映射为 EP 的 `stripe`）时，条纹行与普通行的**单元格**底色 MUST 有可感知差异。由于全局 `.el-table td` 底色带 `!important`，条纹底色 MUST 由共享规则画在 `> td.el-table__cell` 上并同样带 `!important`，其层叠优先级 MUST 高于全局单元格底色。行使选中态（`is-selected` / EP `current-row`）时，选中底色 MUST 优先于条纹底色。条纹底色 MUST 取自 `tokens.css` 已登记令牌。

#### Scenario: Striped rows are visually distinct

- **WHEN** 在浏览器中打开任一传 `striped` 的表格（`device-pool`、`report-generator` 列表与详情、`/elements` 的页面元素表）
- **THEN** 条纹行与普通行的单元格计算底色不同
- **AND** 该差异来自共享规则而非 EP 默认（不依赖 `--el-fill-color-lighter` 的冷灰）

#### Scenario: Selection wins over striping

- **WHEN** 用户选中一个位于条纹位置的行
- **THEN** 该行呈现选中底色，而不是条纹底色
- **AND** 取消选中后恢复条纹底色

#### Scenario: Unstriped tables are unaffected

- **WHEN** 表格未请求斑马纹
- **THEN** 所有行底色一致（不出现意外条纹）