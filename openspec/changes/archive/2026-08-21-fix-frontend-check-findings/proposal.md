## Why

`vue-frontend-check` 全量静态校验（2026-08-21，三层多代理 + 主审亲证）发现 **1 🔴 + 15 🟠 + 17 🟡**。其中 🔴（StepEditor 锁态仍可写）违反 `frontend/AGENTS.md` §1.2 编辑锁纪律与 case-manager 模块关单项「锁态只读禁用」，必须修复；其余 🟠 含功能可见性缺陷（状态徽章色丢失、web 必填字段无法编辑、详情页 WS 断线不重连、用户消息 XSS 面、SSE 数据型工具结果丢弃）与样式 token 违规，🟡 为协议类型对齐与工程债。以 OpenSpec 拆解逐一修复，恢复到设计预期行为。

## What Changes

按层分组修复（详见 tasks.md）：

1. **锁态与功能缺陷（🔴 + 功能级 🟠）**：StepEditor 声明 `readonly` prop 并全控件禁用；report-generator 状态徽章 class 对齐；StepEditor 补 web 步骤字段分支；TaskDetail WS 不覆盖重连钩子；MessageBubble 用户消息 DOMPurify 清洗；SSEMessageBuilder 消费 `TOOL_RESULT_DATA_DELTA`。
2. **协议与类型对齐（🟡）**：toolbox.ts / conversations.ts / evaluator-api.ts 类型对齐后端 DRF 信封；信封平铺特例登记（element_locator / case_manager 两侧 AGENTS.md + frontend/AGENTS.md §1.3）；`getApiErrorMessage` 走 `formatApiError` 净化；TREP Phase 0 预留端点登记为技术债（不删路由）。
3. **可达性与编辑体验（🟠/🟡）**：可点击 div/span 补键盘角色；API 编辑器删除微操补确认；ApiCaseEditor 接入编辑锁（参照 WebCaseEditor 最小实现）。
4. **样式收敛（🟠/🟡）**：字号/颜色/圆角/阴影/间距/模块色/旧色值收敛 token；z-index 补注释；EvaluatorTab 行内 style 收敛。
5. **错误态与工程债（🟡）**：ReportDetail / TaskReport / device-inspector 读失败补错误态；>500 行文件先拆样式层。

**Non-goals**：① CSS `@import` 治理（`login-card.css`/`auth-form-card.css`，已登记暂缓项，触发 E2E 再动）；② 平铺信封改造成信封式（legacy 特例未收敛前禁止，本 change 只登记不改造）；③ >500 行文件的逻辑层重构（只拆样式层）；④ 新增测试用例以外的无关重构。

## 关联文档

- `frontend/AGENTS.md` §1.2/§2/§3（分层纪律、风格约束、协议要点）——约束来源
- `frontend/src/modules/{case-manager,test-runner,report-generator,ai-assistant,device-inspector,device-pool}/AGENTS.md`——模块级契约与关单项
- `dev_docs/03-设计与架构/ARCH-06/07/09`——信封特例登记口径
- `dev_docs/02-PRD需求/PRD-08-AI助手.md` §552——`TOOL_RESULT_DATA_DELTA` 后端产出事实
- `.agents/skills/vue-frontend-check/references/calibration.md`——判罚量规（本 change 已按 §9 回写新类别）
- 缺陷清单：2026-08-21 校验报告（1 🔴 / 15 🟠 / 17 🟡）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

> Bug 修复 + 文档登记，无需求级行为变化：`.openspec.yaml` 已设 `skip_specs: true`。锁态只读、web 字段编辑、WS 重连、SSE 数据型工具结果均为恢复到 PRD/ARCH 已定义行为，非新需求。

## Impact

- 前端：`modules/case-manager/**`（StepEditor/CaseEditor 锁态、web 字段、删除确认、编辑锁）、`modules/report-generator/**`（徽章、错误态）、`modules/test-runner/**`（WS 重连、taskUtils 状态色、大文件拆样式）、`modules/ai-assistant/**`（MessageBubble XSS、SSEMessageBuilder、EvaluatorTab 样式、toolbox/conversations 类型）、`modules/device-inspector/**`（可达性、错误态、11px）、`modules/device-pool/index.vue`（KPI 色）、`shared/**`（ErrorState/PageHeader/GroupTreePanel/StepScreenshotPanel 等样式、api-error 文案）
- 后端：零代码改动（仅 `apps/element_locator/AGENTS.md`、`apps/case_manager/AGENTS.md` 文档登记）
- 测试范围：`npm run build` 通过；vitest 相关 spec 不回归；vue-frontend-check 复扫相关文件转绿
