## MODIFIED Requirements

### Requirement: Form validation uses Element Plus rules

需要校验的表单 MUST 使用 Element Plus 表单校验（`el-form` 的 `:model` + `:rules`，配 `el-form-item` 的 `prop` 与 `formRef.validate()`）；`el-form-item` 的 `required` MUST NOT 在缺少 `:rules` 时单独使用——此时它只渲染必填星号而不触发任何校验，属误导性 UI。字段若**实际非必填**（空值有默认兜底或后端可推导），MUST NOT 标注 `required` 星号。校验失败文案与 `ElMessage` 提示 MUST 由调用方处理。

#### Scenario: Required field actually validates

- **WHEN** 用户提交一个带必填字段的表单且该字段为空
- **THEN** 提交被阻止，并在该字段上展示 Element Plus 校验提示
- **AND** 该 `el-form-item` 通过 `:rules` 声明必填，而不是只有 `required` 属性

#### Scenario: Registered debt is not extended

- **WHEN** 检查全仓 `el-form-item` 的 `required`
- **THEN** 不存在「仅 `required`」的必填项，命中数为 0
- **AND** 原 `AgentBasicInfo` 的名称项被认定为**非必填**（空值由父组件取线路名或「平台小助手」兜底），已移除误导性的必填星号，而非补 `:rules`
