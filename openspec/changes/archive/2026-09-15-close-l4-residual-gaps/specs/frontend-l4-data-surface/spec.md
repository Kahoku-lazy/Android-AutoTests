## MODIFIED Requirements

### Requirement: Single pagination implementation

L4 分页 MUST 由共享 `usePagination` composable 提供（`currentPage` / `totalPages` / `pagedItems` / `goPage` / `setPageSize` / `PAGE_SIZE_OPTIONS`）；页面 SHALL NOT 自建分页状态机（自算 `totalPages`、自写 `goPage` / `setPageSize`）。分页选项集 MUST 来自模块 `constants.ts`，SHALL NOT 在页面内联或本地重复定义。

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
- **THEN** 唯一实现是 `shared/composables/usePagination.ts`，消费方为 `device-pool`、`report-generator/index` 与 `report-generator/ReportDetail`
- **AND** 原 `report-generator/ReportDetail.vue` 的手写分页例外已于 2026-09-15 退役，全仓 SHALL NOT 重新引入自算 `totalPages` / 自写 `goPage` 的状态机

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
