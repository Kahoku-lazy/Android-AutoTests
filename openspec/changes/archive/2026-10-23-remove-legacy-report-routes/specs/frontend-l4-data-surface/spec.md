## MODIFIED Requirements

### Requirement: Single pagination implementation

L4 分页 MUST 由共享 `usePagination` composable 提供（`currentPage` / `totalPages` / `pagedItems` / `goPage` / `setPageSize` / `PAGE_SIZE_OPTIONS`）；页面 SHALL NOT 自建分页状态机（自算 `totalPages`、自写 `goPage` / `setPageSize`）。分页选项集 MUST 来自模块 `constants.ts`，SHALL NOT 在页面内联或本地重复定义。固定每页行数的页面 MAY 只登记单一取值，但选项集与其默认值仍 MUST 来自模块 `constants.ts`。数据源缩小导致总页数减少时，composable MUST 自动把 `currentPage` 夹取到有效范围（`1 ≤ currentPage ≤ totalPages`），MUST NOT 让 `pagedItems` 落在空页；页面 MAY 额外在筛选 / 搜索变化时显式回到第 1 页。

#### Scenario: Paginated lists use the shared composable

- **WHEN** 列表需要分页
- **THEN** 页面取用 `usePagination` 的返回值驱动分页，控件文案为「第 X / Y 页 · 共 N 条」与「上一页 / 下一页」
- **AND** 不出现页面内自建的 `totalPages` / `goPage` 实现

#### Scenario: Page size options come from a single source

- **WHEN** 检查报告列表的每页行数选项
- **THEN** 取值来自 `report-generator/constants.ts` 的 `PAGE_SIZE_OPTIONS`
- **AND** 该模块内不存在内联或被本地重新声明的选项集

#### Scenario: Registered exception does not multiply

- **WHEN** 检查全仓分页实现
- **THEN** 唯一实现是 `shared/composables/usePagination.ts`，消费方为 `device-pool`、`report-generator/index` 与 `case-manager`
- **AND** 唯一的登记例外（已删除的 `report-generator/ReportDetail.vue` 手写分页）已于 2026-09-15 退役并随页面删除，全仓 SHALL NOT 重新引入自算 `totalPages` / 自写 `goPage` 的状态机

#### Scenario: Fixed page size still comes from module constants

- **WHEN** 某模块的表格固定单一每页行数且不渲染「显示行数」选择器
- **THEN** 其 `PAGE_SIZE_OPTIONS` 只登记单一取值，该取值与默认行数相等，且两者均声明在该模块的 `constants.ts`
- **AND** 页面内不出现行数字面量；该 capability 不钉具体行数——具体行数由使用该表格的页面能力定义，避免同一数字在两份规格里各登记一次

#### Scenario: Shrinking source never leaves an empty page

- **WHEN** 用户停在第 3 页时切换筛选条件，使结果集只剩 1 页
- **THEN** `currentPage` 自动落到有效范围（第 1 页），表格 MUST NOT 显示空页
- **AND** 该夹取行为由共享 `usePagination` 承担，消费方无需各写一遍
