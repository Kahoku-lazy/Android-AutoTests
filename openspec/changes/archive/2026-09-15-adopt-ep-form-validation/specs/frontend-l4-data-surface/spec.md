## MODIFIED Requirements

### Requirement: Form validation uses Element Plus rules

需要校验的表单 MUST 使用 Element Plus 表单校验（`el-form` 的 `:model` + `:rules`，配 `el-form-item` 的 `prop` 与 `formRef.validate()`）；`el-form-item` 的 `required` MUST NOT 在缺少 `:rules` 时单独使用——此时它只渲染必填星号而不触发任何校验，属误导性 UI。校验失败文案与 `ElMessage` 提示 MUST 由调用方处理（`frontend/AGENTS.md` 硬性规范 §1.5）。

#### Scenario: Required field actually validates

- **WHEN** 用户提交一个带必填字段的表单且该字段为空
- **THEN** 提交被阻止，并在该字段上展示 Element Plus 校验提示
- **AND** 该 `el-form-item` 通过 `:rules` 声明必填，而不是只有 `required` 属性

#### Scenario: Registered debt is not extended

- **WHEN** 检查全仓 `el-form-item` 的 `required`
- **THEN** 原 10 处「仅 `required`」的表单已接入 `:rules` + `formRef.validate()`（`ProjectList` · `PrototypeList` · `SaveToElementsDialog` · `LocatorFilePanel` 两套表单 · `EvaluatorTab` 试卷编辑器 · `TaskBoard`），不再出现只画星号不校验的必填项
- **AND** 唯一保留的例外是 `ai-assistant/components/AgentBasicInfo.vue` 的名称项：空名由父组件 `AgentDetail.save()` 取线路名或「平台小助手」作默认值，属显式兜底而非漏校验；该例外 MUST 同时登记在 `frontend/AGENTS.md`
