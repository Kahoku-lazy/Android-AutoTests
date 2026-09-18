## MODIFIED Requirements

### Requirement: Shared AppTable is the default table implementation

L4 多行多列列表 MUST 使用共享件 `AppTable`（`.ac-table`），列以 `{title, dataIndex, width, align}` 数组声明；系统 SHALL NOT 为同一场景另建第二套通用表格封装，也 SHALL NOT 直接使用原生 `el-table`。`AppTable` MUST 覆盖分组表头（`columns[].children`）、自定义表头（`#header-<prop>`）、底层实例取用（模板 ref 上的 `tableRef`）与属性透传（`$attrs`），使这些能力的诉求不再构成绕开共享件的理由。

#### Scenario: Flat list prefers the shared table

- **WHEN** 页面渲染扁平多行多列列表
- **THEN** 使用共享 `AppTable` 渲染，且页面根带 `wb-shell`（或等价主题锚点）
- **AND** 不出现为同一场景自建的通用表格封装

#### Scenario: Registered exceptions for grouped headers and instance access

- **WHEN** 页面需要多级分组表头、复选框选择列，或需要底层 `TableInstance` 做滚动定位 / `setCurrentRow`
- **THEN** 这些诉求由 `AppTable` 自身满足：分组用 `columns[].children`、表头用 `#header-<prop>`、实例用 `ref` 上的 `tableRef`
- **AND** 全仓不存在直接使用原生 `el-table` 的页面（`shared/components/AppTable.vue` 内部实现除外）
