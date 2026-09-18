## 1. 简单两处（composable 守卫 → 字段校验）

- [x] 1.1 `case-manager/ProjectList.vue`：`el-form` 补 `:model` / `ref` / `:rules`，`项目名称` 补 `prop="name"`；`confirmCreate` 改为 `await formRef.value?.validate()` 失败即 return；验证：空名提交被阻止且在字段内提示
- [x] 1.2 `workflow/PrototypeList.vue`：同构改造（`prop="name"`）；验证：同上

## 2. 弹窗 / 面板表单

- [x] 2.1 `device-inspector/components/SaveToElementsDialog.vue`：`el-form` 补 `:model` / `ref` / `:rules`，两个互斥必填项补 `prop`（`selectedPageId` / `newPageLabel`）；`confirm()` 的两处空值 `ElMessage.warning` 由 `validate()` 取代；验证：两种模式各自必填生效
- [x] 2.2 `element-locator/components/LocatorFilePanel.vue`：两套表单各建 `ref` / `:model` / `:rules`，4 处必填补 `prop`（`name` / `locator_value` / `name` / `url`）；`saveWeb` / `saveApi` 的 `ElMessage.warning` 由 `validate()` 取代；验证：两套表单分别必填生效，互不干扰
- [x] 2.3 `ai-assistant/EvaluatorTab.vue`：试卷编辑器 `el-form` 补 `:model` / `ref` / `:rules`，`名称` 补 `prop="name"`；`saveBank()` 的空值 `ElMessage.warning` 由 `validate()` 取代；验证：空名不提交
- [x] 2.4 `ai-assistant/components/TaskBoard.vue`：`el-form` 补 `:model` / `ref` / `:rules`，`任务目标` 补 `prop="goal"`；`onSubmit` 先 `validate()`；保留按钮 `:disabled`；验证：清空目标后提交被阻止并内联提示

## 3. 规格与速查同步

- [x] 3.1 以 MODIFIED 更新 `specs/frontend-l4-data-surface/spec.md` 的「Form validation uses Element Plus rules」（两个场景：必填真校验 + 债务不再扩大，后者改为 10 处已接入 + 1 处登记例外）；验证：`openspec validate --strict` 通过
- [x] 3.2 更新 `frontend/AGENTS.md` L4 速查 §⑥：`:rules|formRef` 判据由 0 改为实测值，「11 处仅 required」缺口改为「10 处已接入 · 1 处登记例外（`AgentBasicInfo` 空名有父级默认兜底）」；验证：速查与 spec 一致

## 4. 门禁与归档

- [x] 4.1 `cd frontend && npm run typecheck`；验证：全仓 34 个既有错误，6 个改动文件零错误
- [x] 4.2 用 `vue-frontend-check` 过 6 个改动文件；验证：改动行无新增字号 / 硬编码色 / 契约违规
- [x] 4.3 归档（经 `openspec-archive-change`）；验证：`openspec/specs/frontend-l4-data-surface/spec.md` 已更新，变更进入 archive
