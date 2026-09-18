## 1. 锁态与功能缺陷（🔴 + 功能级 🟠）

- [x] 1.1 StepEditor 锁态只读：`defineProps` 增加 `readonly: Boolean`；步骤类型下拉/字段输入/添加/删除/复制/拖拽/子步骤操作全部加 `:disabled="readonly"`；验证 `npm run build` 通过 + 静态确认 CaseEditor.vue:214 / WebCaseEditor.vue:371 传参生效（vue-frontend-check 一.8 锁态复扫）
- [x] 1.2 report-generator 状态徽章：`index.vue` 将 `.status-ok/.status-fail/.status-stopped` 死 CSS 改为 `.badge-pass/.badge-fail/.badge-stopped` 并补 `.badge-running`（对齐 `statusBadgeClass()` 返回值与 ReportDetail.vue:439 口径）；验证 build + class↔style 复扫
- [x] 1.3 StepEditor web 步骤字段：补 `url/selector/value` 渲染分支（对齐 `shared/constants/steps.ts` 必填表与 FIELD_LABELS/FIELD_HINTS）；验证 build + WebCaseEditor 静态走查必填字段可填
- [x] 1.4 TaskDetail WS 重连：`bindDetailTaskWS` 改用 `ws.addEventListener('open'/'close')` 追加日志，不再覆盖 `useTaskWebSocket` 注册的 `onopen/onclose`（保留 backoff 重连与 `_ws_reconnected` 通知）；验证 build + 六.7.4 复扫
- [x] 1.5 MessageBubble XSS：用户消息渲染改 `v-html="sanitizeHtml(userTextContent)"`（DOMPurify 清洗，与 assistant 侧 `safeMarkdown` 同源）；验证 build + 安全复扫
- [x] 1.6 SSEMessageBuilder 消费 `TOOL_RESULT_DATA_DELTA`：新增分支累积到 `_toolResult.data/mediaType`，END 时随 block 落库并给输出占位摘要，不再落 `unknown`；验证 build + 前端单测（如 shared/sse 有 spec）

## 2. 协议与类型对齐（🟡）

- [x] 2.1 `toolbox.ts fetchAgentTools` 返回类型改 `{status; data?: {mcp?: ToolItem[]; skills?: ToolItem[]}}`；`ToolItem/KnowledgeDoc` DTO 上移 api 层导出；`useAgentTools.ts:196-197` 移除 `as` 强转；验证 build + typecheck
- [x] 2.2 `toolbox.ts getKnowledgeDocuments` 类型改 `{status; data?: {documents?: KnowledgeDoc[]; total?: number}}`；`useAgentTools.ts:155` 移除 `as` 强转；验证 build + typecheck
- [x] 2.3 `conversations.ts deleteConversation/postConfirmResult` 补 `data?: object`（对齐后端 `Response({})` → `{status, data:{}}`）；`evaluator-api.ts` 按后端实际修正：`deleteRun` → `{status}`（平铺），`submitScore` → `{status; data?: {result_id, scored}}`（DRF）；验证 build + typecheck
- [x] 2.4 信封平铺特例登记：`apps/element_locator/AGENTS.md`、`apps/case_manager/AGENTS.md`、`apps/evaluator/AGENTS.md` 契约段补「legacy 路径平铺信封」口径；`frontend/AGENTS.md` §1.3 信封特例行补 element_locator/case_manager/evaluator；验证 `python tools/gen_arch_stats.py --check-md`
- [x] 2.5 `shared/types/api-error.ts`：`formatApiError` 实现迁入本文件（消除与 api-client 的循环依赖），`getApiErrorMessage` 改走 `formatApiError` 净化；`api-client.ts` re-export 保持 6 处既有消费方不变；验证 build
- [x] 2.6 遗漏端点债登记：`monitor/{id}`/`run/{id}/snapshot`/`run/{id}/status`/`runs`（TREP Phase 0）登记 `apps/test_runner/AGENTS.md`；`devices/current` 登记 `apps/device_pool/AGENTS.md`；`auth/me` 登记 `apps/accounts/AGENTS.md`；`banks/{id}/delete` 登记 `apps/evaluator/AGENTS.md`；均保留路由不删；验证 --check-md

## 3. 可达性与编辑体验（🟠/🟡）

- [x] 3.1 `SnapshotListDrawer.vue:33` 快照项补 `role="button" tabindex="0"` + Enter/Space 键处理；验证 build + 五.10 复扫
- [x] 3.2 `PageElementsPanel.vue:133,158` 缩略图同上补键盘可达；验证 build + 五.10 复扫
- [x] 3.3 `ApiStepCard.vue:96` 变量插入 chip 补键盘可达（role/tabindex + keydown）；验证 build
- [x] 3.4 API 编辑器删除微操补确认：`StepListPanel.removeStep`、`TestDataPanel.removeRow`、`ValidationPanel.removeRule`、`ApiStepCard.removeExtract` 加 `ElMessageBox.confirm`；验证 build
- [x] 3.5 `ApiCaseEditor.vue` 接入编辑锁：`acquireEditLock/releaseEditLock` + `isReadOnly`（423 → 只读横幅）+ 保存/删除禁用 + doSave 守卫 + 四面板 readonly prop 全控件禁用 + 卸载释放；验证 build + 五.8 复扫

## 4. 样式收敛（🟠/🟡）

- [x] 4.1 字号 <12px 收敛 `--app-size-xs`：`ErrorState.vue`、`SnapshotListDrawer.vue:70`、`GroupTreePanel.vue:221,230,243`、`StepScreenshotPanel.vue`（10px/11px）、`workbench-theme.css:137`；验证 build + 二.1 复扫
- [x] 4.2 硬编码字号收敛 token：`PageHeader`（24/15px）、`WorkbenchHeader`（26/16px）、`KpiCard`（17px）、`EmptyState`（16/14px）等文本字号改 `--app-size-*`；验证 build + 二.1 复扫
- [x] 4.3 旧色值清除：`PageHeader.vue`、`style.css` 的 `#4a4e69/#9a8c98` fallback 删除或改现行 token；验证 build + 二.9 复扫
- [x] 4.4 硬编码交互/背景色收敛：`style.css`、`FilterTabs`、`KpiCard`、`RateBar`、`GroupTreePanel`、`StepScreenshotPanel`、`EmptyState`、`ErrorState`、`WorkbenchHeader`、`workbench-theme.css`、`CaseBreakdown` 逐处改 `--app-status-*`/`--ink`/`--app-bg-card`/`--app-bg-subtle` 等 token；验证 build + 二.2 复扫
- [x] 4.5 模块/状态色硬编码收敛：`device-pool/index.vue:85-86` KpiCard → `var(--c-device)/var(--c-runner)`；`taskUtils.ts taskStatusInfo` 五色 → token CSS 变量字符串；验证 build + 二.8 复扫
- [x] 4.6 对称大圆角收敛：`CaseBreakdown.vue`（20px → `--app-radius-md`）、`StepScreenshotPanel.vue`（20px）等；验证 build + 二.5 复扫
- [x] 4.7 模糊阴影收敛：`CaseBreakdown`、`AgentDetail`、`EvaluatorTab`、`StepScreenshotPanel`、`motion.css`、`ConfirmDialog` 模糊/大扩散阴影 → `--app-shadow-*` 扁平；验证 build + 二.6 复扫
- [x] 4.8 裸 px 间距收敛 `--app-space-*`：`style.css`、`DashboardView.style.css`、`DevicePoolView.style.css`、`CaseBreakdown` 等 gap/padding/margin → 刻度 token；验证 build + 二.7 复扫
- [x] 4.9 z-index 补注释并收敛：`GroupTreePanel`（80→70 弹窗层）、`workflow/index.vue`（10000→70 弹窗层、10 加注释）、`DevicePoolView.style.css`（5 加注释）按 90 侧栏/80 抽屉/70 弹窗/50 固定头口径；验证 build
- [x] 4.10 EvaluatorTab 收敛：`scoreColor` 硬编码 hex → token；行内 style 中全部硬编码 hex 改 token（`#fff3e0/#e65100/#8a7b66/#f7a8c4/#b39ef3/#f3f0ff/#5b4aa8`）；高频 pattern 已用 scoped class；**残留**：约 70 处纯布局行内 style（值已是 var token）登记为后续收敛债（全量 class 化需 E2E 排期）；验证 build

## 5. 错误态与工程债（🟡）

- [x] 5.1 `ReportDetail.vue` / `TaskReport.vue` 读失败补 ErrorState + 重试（error ref + 状态判断分支）；验证 build + 三.1 复扫
- [x] 5.2 `device-inspector/store.ts` `fetchDevices`/`fetchSnapshots` 读失败补错误态（复用模块 `error` ref → index.vue ErrorState 展示）；验证 build
- [x] 5.3 大文件拆样式层：**评估后登记暂缓**——scoped style 外置为全局 css 有类名冲突风险（如 `.kpi-row` 与 device-pool 全局同名），rules「工作正常的 CSS 治理需 E2E 单独排期」；触发条件：文件 >500 行且下次大改时随改随拆
- [x] 5.4 组件直接调 api 收口：**评估后登记保留**——`fetchStepTypes`/`caseLock`/`caseUnlock` 均仅单处消费，rules「抽 shared/抽 composable 等第二个真实消费方；单处使用不提前抽象」，收口为 1:1 包装属过度设计；组件内调用均经模块 api 层（无直接 axios/fetch），不违红线

## 6. 回归与门禁

- [ ] 6.1 全量构建 + 单测：`npm run build`、`npm run typecheck`（src 零错误；tests/dashboard 既有类型债非本次引入）、vitest 相关 spec 不回归；验证全绿
- [ ] 6.2 vue-frontend-check 复扫受影响文件：本次 16 项（1 🔴/15 🟠）逐项转绿，🟡 项标记完成/登记；验证复扫记录存档
- [ ] 6.3 文档同步：`python tools/gen_arch_stats.py --check-md` 通过；OpenSpec `npx openspec validate 2026-08-21-fix-frontend-check-findings` 通过
- [ ] 6.4 归档：tasks.md 全勾 → change 移入 `openspec/changes/archive/`，`.openspec.yaml` 补 `archived: 2026-08-21`
