## Why

`frontend-l4-data-surface` spec 已把表单校验口径定为 Element Plus `:rules` + `formRef.validate()`，但实测全仓 `:rules` 命中 **0**，11 处 `el-form-item required` 只画必填星号。逐处核对后，这 11 处并非无校验，而是校验散落在别处：

- **10 处**由临时 `ElMessage.warning('请填写…')` 守卫（`SaveToElementsDialog` / `LocatorFilePanel` / `EvaluatorTab`）或提交按钮 `:disabled`（`TaskBoard`）兜底；`ProjectList` / `PrototypeList` 的守卫在 composable（`useProjects.ts:36-40` / `usePrototypes.ts:48-52`）
- **1 处**（`AgentBasicInfo` 的名称）由父组件 `AgentDetail.save():123-129` 的**显式默认**兜底：空名取线路名或「平台小助手」

本变更把前 10 处升级为 EP 字段级校验（错误提示从 Toast 变为字段内联），第 11 处作为登记例外保留——给它加 `:rules` 会改变「空名即取默认名」的既有行为，属产品决策而非缺陷修复。

## What Changes

- 6 个文件的表单接入 `:rules` + `formRef.validate()`：`case-manager/ProjectList.vue` · `workflow/PrototypeList.vue` · `device-inspector/components/SaveToElementsDialog.vue` · `element-locator/components/LocatorFilePanel.vue`（该文件有**两套**表单，各一套 ref / rules）· `ai-assistant/EvaluatorTab.vue`（试卷编辑器）· `ai-assistant/components/TaskBoard.vue`
- 10 处 `el-form-item` 补 `prop`，必填由 `:rules` 驱动；提交路径改为 `await formRef.value.validate()` 失败即 return
- 组件内针对空值的临时 `ElMessage.warning('请填写…')` 由字段级校验取代（**错误提示位置有意从 Toast 变为字段内联**）
- **不改** `AgentBasicInfo.vue`（空名有父级默认兜底），在 spec 与 L4 速查登记为允许的例外
- **不改** composable 内的 `addProject` / `addPrototype` 空值守卫：收敛后组件侧会提前 return，该守卫成为第二层防御且不再触发
- **BREAKING**：无。props / emits / 接口 / 路由不变

## 关联文档

- `openspec/specs/frontend-l4-data-surface/spec.md`：本变更修改的需求（Form validation uses Element Plus rules）
- `openspec/changes/archive/2026-09-15-add-l4-spec-and-l4-l5-quickref/`：该口径与「11 处已知缺口」的登记出处
- `frontend/AGENTS.md` L4 速查 §④.2 / §⑥：校验口径与缺口的登记处
- 说明：`dev_docs/文档编号对照表.md` 不存在；本变更为前端实现收敛，不改业务需求

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `frontend-l4-data-surface`: 「Form validation uses Element Plus rules」的两个场景更新——「Registered debt is not extended」由「11 处已知缺口」改为「10 处已接入 + 1 处登记例外（`AgentBasicInfo`，空名由父组件默认兜底）」

## Impact

- `frontend/src/modules/case-manager/ProjectList.vue` · `workflow/PrototypeList.vue` · `device-inspector/components/SaveToElementsDialog.vue` · `element-locator/components/LocatorFilePanel.vue` · `ai-assistant/EvaluatorTab.vue` · `ai-assistant/components/TaskBoard.vue`
- `openspec/specs/frontend-l4-data-surface/spec.md`（归档时更新）· `frontend/AGENTS.md`（L4 速查 §⑥）
- 测试与门禁：`vue-tsc --noEmit`；`vue-frontend-check` 过 6 个改动文件；6 个表单的浏览器目视（本环境无浏览器，记录为待补）
- 不影响：`AgentBasicInfo.vue`、composable 守卫、后端接口、路由表
