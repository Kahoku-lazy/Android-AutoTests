## Purpose

定义 L4 数据展示面（表格 / 卡片网格 / 表单）的实现口径：表格首选共享件并明确可绕过的能力边界、分页唯一实现、表单校验走 Element Plus 原生 `:rules` + `validate()`，以及卡片与网格的零件归属，使各模块的列表与表单读起来是同一套语言。

## ADDED Requirements

### Requirement: Shared AppTable is the default table implementation

L4 多行多列列表 MUST 首选共享件 `AppTable`（`.ac-table`），列以 `{title, dataIndex, width, align}` 数组声明；系统 SHALL NOT 为同一场景另建第二套通用表格封装。仅当需要**多级分组表头**、**选择列**或**底层 `TableInstance` 句柄**（以及 `AppTable` 未暴露的布局参数）时，MAY 直接使用 `el-table`，但 MUST 在 `frontend/AGENTS.md` 与本 spec 同时登记为例外。

#### Scenario: Flat list prefers the shared table

- **WHEN** 页面渲染扁平多行多列列表
- **THEN** 使用共享 `AppTable` 渲染，且页面根带 `wb-shell`（或等价主题锚点）
- **AND** 不出现为同一场景自建的通用表格封装

#### Scenario: Registered exceptions for grouped headers and instance access

- **WHEN** 页面需要 dump / OCR 多级分组表头、复选框选择列，或需要底层 `TableInstance` 做截图↔表格滚动联动
- **THEN** 允许直接使用 `el-table`，且该例外同时登记在 `frontend/AGENTS.md` 与本 spec
- **AND** 现有例外为 `device-inspector` 的 `PageElementsPanel` / `StructureAnalysisPanel` 与 `element-locator` 的 `PageElementsWorkbench` 共 3 处，SHALL NOT 扩散到第四处

### Requirement: Single pagination implementation

L4 分页 MUST 由共享 `usePagination` composable 提供（`currentPage` / `totalPages` / `pagedItems` / `goPage` / `setPageSize`）；页面 SHALL NOT 另写一套分页状态机。已存在的例外 MUST 登记，且在收敛前 MUST NOT 新增第二套。

#### Scenario: Paginated lists use the shared composable

- **WHEN** 列表需要分页
- **THEN** 页面取用 `usePagination` 的返回值驱动分页，控件文案为「第 X / Y 页 · 共 N 条」与「上一页 / 下一页」
- **AND** 不出现页面内自建的 `totalPages` / `goPage` 实现

#### Scenario: Registered exception does not multiply

- **WHEN** 检查全仓分页实现
- **THEN** 共享 composable 消费方为 `device-pool` 与 `report-generator/index`
- **AND** `report-generator/ReportDetail.vue` 的手写分页是登记例外，全仓 SHALL NOT 出现第 4 套分页实现

### Requirement: Form validation uses Element Plus rules

需要校验的表单 MUST 使用 Element Plus 表单校验（`el-form` 的 `:model` + `:rules`，配 `el-form-item` 的 `prop` 与 `formRef.validate()`）；`el-form-item` 的 `required` MUST NOT 在缺少 `:rules` 时单独使用——此时它只渲染必填星号而不触发任何校验，属误导性 UI。校验失败文案与 `ElMessage` 提示 MUST 由调用方处理（`frontend/AGENTS.md` 硬性规范 §1.5）。

#### Scenario: Required field actually validates

- **WHEN** 用户提交一个带必填字段的表单且该字段为空
- **THEN** 提交被阻止，并在该字段上展示 Element Plus 校验提示
- **AND** 该 `el-form-item` 通过 `:rules` 声明必填，而不是只有 `required` 属性

#### Scenario: Registered debt is not extended

- **WHEN** 检查全仓 `el-form-item`
- **THEN** 存在 11 处「仅 `required`、无 `:rules`」的历史用例，登记为已知缺口
- **AND** 新增或修改的表单 MUST NOT 增加该类用例

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
