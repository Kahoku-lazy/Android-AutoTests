# frontend-l4-data-surface Specification

## Purpose
定义 L4 数据展示面（表格 / 卡片网格 / 表单）的实现口径：表格首选共享件并明确可绕过的能力边界、分页唯一实现、表单校验走 Element Plus 原生 `:rules` + `validate()`，以及卡片与网格的零件归属，使各模块的列表与表单读起来是同一套语言。

## Requirements

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

### Requirement: Single pagination implementation

L4 分页 MUST 由共享 `usePagination` composable 提供（`currentPage` / `totalPages` / `pagedItems` / `goPage` / `setPageSize` / `PAGE_SIZE_OPTIONS`）；页面 SHALL NOT 自建分页状态机（自算 `totalPages`、自写 `goPage` / `setPageSize`）。分页选项集 MUST 来自模块 `constants.ts`，SHALL NOT 在页面内联或本地重复定义。固定每页行数的页面 MAY 只登记单一取值，但选项集与其默认值仍 MUST 来自模块 `constants.ts`。数据源缩小导致总页数减少时，composable MUST 自动把 `currentPage` 夹取到有效范围（`1 ≤ currentPage ≤ totalPages`），MUST NOT 让 `pagedItems` 落在空页；页面 MAY 额外在筛选 / 搜索变化时显式回到第 1 页。

#### Scenario: Paginated lists use the shared composable

- **WHEN** 列表需要分页
- **THEN** 页面取用 `usePagination` 的返回值驱动分页，控件文案为「第 X / Y 页 · 共 N 条」与「上一页 / 下一页」
- **AND** 不出现页面内自建的 `totalPages` / `goPage` 实现

#### Scenario: Page size options come from a single source

- **WHEN** 检查报告列表与报告详情的每页行数选项
- **THEN** 两处取值相同，且都来自 `report-generator/constants.ts` 的 `PAGE_SIZE_OPTIONS`
- **AND** 该模块内不存在内联或被本地重新声明的选项集

#### Scenario: Registered exception does not multiply

- **WHEN** 检查全仓分页实现
- **THEN** 唯一实现是 `shared/composables/usePagination.ts`，消费方为 `device-pool`、`report-generator/index`、`report-generator/ReportDetail` 与 `device-inspector`
- **AND** 原 `report-generator/ReportDetail.vue` 的手写分页例外已于 2026-09-15 退役，全仓 SHALL NOT 重新引入自算 `totalPages` / 自写 `goPage` 的状态机

#### Scenario: Fixed page size still comes from module constants

- **WHEN** 设备检查器元素表格固定每页 8 行且不渲染「显示行数」选择器
- **THEN** 其 `PAGE_SIZE_OPTIONS=[8]` 与默认行数仍声明在 `device-inspector/constants.ts`，页面内不出现行数字面量

#### Scenario: Shrinking source never leaves an empty page

- **WHEN** 用户停在第 3 页时切换筛选条件，使结果集只剩 1 页（设备管理页与设备检查器同口径）
- **THEN** `currentPage` 自动落到有效范围（第 1 页），表格 MUST NOT 显示空页
- **AND** 该夹取行为由共享 `usePagination` 承担，消费方无需各写一遍

### Requirement: Form validation uses Element Plus rules

需要校验的表单 MUST 使用 Element Plus 表单校验（`el-form` 的 `:model` + `:rules`，配 `el-form-item` 的 `prop` 与 `formRef.validate()`）；`el-form-item` 的 `required` MUST NOT 在缺少 `:rules` 时单独使用——此时它只渲染必填星号而不触发任何校验，属误导性 UI。字段若**实际非必填**（空值有默认兜底或后端可推导），MUST NOT 标注 `required` 星号。校验失败文案与 `ElMessage` 提示 MUST 由调用方处理（`frontend/AGENTS.md` 硬性规范 §1.5）。

#### Scenario: Required field actually validates

- **WHEN** 用户提交一个带必填字段的表单且该字段为空
- **THEN** 提交被阻止，并在该字段上展示 Element Plus 校验提示
- **AND** 该 `el-form-item` 通过 `:rules` 声明必填，而不是只有 `required` 属性

#### Scenario: Registered debt is not extended

- **WHEN** 检查全仓 `el-form-item` 的 `required`
- **THEN** 不存在「仅 `required`」的必填项，命中数为 0
- **AND** 原 `AgentBasicInfo` 的名称项被认定为**非必填**（空值由父组件取线路名或「平台小助手」兜底），已移除误导性的必填星号，而非补 `:rules`

### Requirement: Cards and grids reuse shared parts

可复用数据块（图表卡 / 表格卡 / 指标卡 / 认证卡 / 条目卡）MUST 使用 shared 卡片零件（`AppCard` / `KpiCard` / `SketchCard` / `DoodleNote`）；卡片网格 MAY 由模块自建（`grid-template-columns`），SHALL NOT 为此抽出共享网格组件，也 SHALL NOT 另建与 shared 卡壳视觉不一致的私有默认卡样式。

#### Scenario: Metric row reuses the shared KPI card

- **WHEN** 页面渲染指标行
- **THEN** 卡片来自 `shared/components/KpiCard.vue` 或其薄包装
- **AND** 不出现模块私有的清新风统计卡默认样式

#### Scenario: Module-owned grid is allowed

- **WHEN** 页面需要卡片网格布局
- **THEN** 网格由模块样式自建，不要求抽共享网格组件
- **AND** 卡片外观仍来自 shared 零件，主题锚点仍在页面根上

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

### Requirement: Flat lists do not wrap AppTable in Element Plus card

设备管理与报告列表的扁列表 MUST 以 `AppTable` 表纸呈现数据；SHALL NOT 再用 `el-card` 作为表格外套。需要分组容器时 MUST 使用 `.doc-section` 或 `AppCard`，且表纸皮肤遵循 `frontend-doodle-sketch-table`。

#### Scenario: Device table drops Element Plus card chrome

- **WHEN** 用户在 `/devices` 查看表格视图
- **THEN** DOM 中该表不位于 `el-card` 内
- **AND** 仍由共享 `AppTable` 渲染行与列
