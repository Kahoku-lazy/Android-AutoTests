## 1. 类型与纯函数

- [x] 1.1 `frontend/src/shared/types/ai.ts`：新增 `TaskReportStep`（seq / action / expected / outcome）、`TaskReportCase`（title / outcome / steps / round_ids）、`TaskReportRound`（round_id / role_kind / role / role_name / model / step_seq / attempt / subject / handover / verdict / blocks / duty）；`getTaskReport` 返回类型改为 `TaskReportResponse`。验证：`npm run typecheck` 通过，且 `task-list` 内无新增 `any`。**验证结果**：`vue-tsc --noEmit` 退出码 0；新增 10 个报告类型（含 `TaskReportBlock` / `TaskReportBlockItem` / `TaskReportPayload`），`api/tasks.ts` 已改用新类型。
- [x] 1.2 新增 `frontend/src/modules/task-list/helpers/report-steps.ts`：实现 `caseStepViews(caseItem, roundsById)` 与 `StepView / AttemptView / StepRun` 类型。步骤轴优先 `steps[]`；无 steps 时按 `step_seq` 去重升序；再退化为每轮一步。轮次按 `step_seq` 挂载、按 `role_kind` 分流、按 `attempt` 升序；配不上的验收单独成块。纯函数，无 DOM、无 Vue 依赖。验证：`npx vitest run tests/task-list` 中新增用例通过。**验证结果**：211 行，导出 `caseStepViews` / `attemptVerdict` / `formatClock`；12 条用例全绿。
- [x] 1.3 新增 `frontend/tests/task-list/p0/report-steps.spec.ts`：覆盖「正常两步」「重试（第 1 次驳回 / 第 2 次通过）」「缺 `step_seq` 退化」「未执行步骤仍有行」「一次执行两次验收」五组。验证：`npx vitest run tests/task-list/p0/report-steps.spec.ts` 全绿。**验证结果**：实际写了 12 条（另加「验收先于执行到达」「声明外轮次补位」「坏 round_ids 跳过」「空用例」等），全绿。
- [x] 1.4 `frontend/src/modules/task-list/helpers/task-detail.ts`：删除 `executorRoundNumbers`、`roundTitleLead`、`roundTitleTail`、`roundFlag`、`ReportRoundTitleInput`、`ExecutorRoundKey`（新组件不再消费）。验证：`grep -r "roundTitleLead\|roundTitleTail\|executorRoundNumbers" frontend/src` 无结果；`npm run typecheck` 通过。**验证结果**：另删掉无人引用的 `caseRoundsById` / `reportPageCount` / `reportPageSlice`；`task-detail.spec.ts` 同步移除 3 组失效断言（10 passed）。

## 2. 组件与样式

- [x] 2.1 新增 `frontend/src/modules/task-list/components/RoundProcess.vue` + `RoundProcess.style.css`：渲染单轮过程（交付 / 结论 / 阶段时间线 / 截图，截图沿用 `TaskMediaThumb`），props 为 `round` 与 `kind`（executor / verifier）。验证：`npx vitest run tests/task-list` 通过；组件内无 `any`。**验证结果**：88 行 + 154 行样式；验收子块按判决渲染 `✅` / `❌`，无判决不渲染。
- [x] 2.2 新增 `frontend/src/modules/task-list/components/CaseStepList.vue` + `CaseStepList.style.css`：步骤行（`<button aria-expanded aria-controls>`）+ 展开体编排；展开体按尝试分块，块头渲染次数标签 `第N次`（重试换色），块内顺序为执行过程 → 验收过程。验证：`npm run lint:styles` 不新增告警；DOM 中每个步骤 `aria-controls` 都指向存在的展开体 id。**验证结果**：111 行 + 119 行样式；`lint:styles` 输出里没有这两个文件的任何条目（新增 0 处违规）；分页用例断言 `aria-controls` 与展开体 id 一一对应。
- [x] 2.3 样式迁移：把 `TaskDetailPage.style.css` 里的 `.flow-round* / .flow-lead* / .flow-timeline* / .flow-phase* / .flow-item*` 迁到两个组件自己的 scoped 样式，页面只留 `.flow-summary / .flow-section-title / .flow-case* / .badge*`。验证：`npm run lint:styles` 与 `npm run build` 通过；页面样式文件行数明显下降。**验证结果**：页面样式 444 → 292 行，页面组件 482 → 337 行；`npm run build:check` 17.0s 通过。

- [x] 2.4 步骤内三级折叠：`CaseStepList` 的尝试块默认可折叠（块头可点，收起时带走其两个过程），`RoundProcess` 的过程块默认收起、头部保留角色徽章 / 过程名 / `✅`·`❌` / 结论摘要。验证：`npx vitest run tests/task-list` 通过；展开步骤时不出现 `.flow-timeline`。**验证结果**：尝试块默认展开、过程块默认收起；收起态只剩「第1次」块头 + 两行过程头；`vue-tsc` 退出码 0。

## 3. 页面替换与分页删除

- [x] 3.1 `frontend/src/modules/task-list/TaskDetailPage.vue`：删掉轮次平铺段与 `openRounds / toggleRound / roundKey / roundOpen / roundKindClass / leadCount / blockNo / phaseClass`，改用 `<CaseStepList :steps :open-keys :key-prefix :task-id @toggle>`，折叠状态改为 `openSteps: Set<string>`（键 `caseIndex:stepSeq`，默认空集）。验证：`npm run typecheck` 通过，页面文件 ≤ 400 行。**验证结果**：337 行；`vue-tsc --noEmit` 退出码 0。
- [x] 3.2 删除分页：`constants.ts` 去掉 `ROUNDS_PER_PAGE`；页面去掉 `casePages / pageOf / pagedRounds / setPage / pageCount` 与模板里的 `.flow-pager` 整块；`TaskDetailPage.style.css` 删掉 `.flow-pager` 规则。验证：页面与样式里搜索 `pager / ROUNDS_PER_PAGE / casePages` 均无结果；`npm run build` 通过。**验证结果**：全仓只剩分页用例里的负向断言 `.flow-pager` 不存在；`build:check` 通过。
- [x] 3.3 `frontend/tests/task-list/p0/task-detail-round-title.spec.ts`：改写为步骤级断言（步骤行含序号与动作、动作不在子块重复、结果只由徽标表示、验收子块 `✅/❌`、两次尝试标签为「第1次」「第2次」）；`task-report-pagination.spec.ts` 改为「25 步全量渲染、无翻页控件」。验证：`npx vitest run tests/task-list` 全绿。**验证结果**：两个文件分别 7 条与 3 条用例；整套 `tests/task-list` 15 文件 109 passed。

- [x] 3.4 补折叠用例：展开步骤只见块头（无时间线/截图）、点开执行过程才出时间线、收起尝试块隐藏其两个过程且不影响另一次、验收过程收起仍显示 `✅` 与结论摘要。验证：`npx vitest run tests/task-list` 全绿。**验证结果**：该文件 7 → 11 条；整套 15 文件 113 passed。

## 4. 门禁与验收

- [ ] 4.1 前端门禁：`cd frontend && npx vitest run tests/task-list && npm run typecheck && npm run lint:styles && npm run build:check` 全部通过。**当前状态**：vitest（109 passed）、`vue-tsc`、`build:check` 均通过；`lint:styles` 仍红——批 3 硬门禁 50 处跨边界借用全部落在本次未改动的 `StepLogEvidence.style.css` / `TaskAttemptCard.vue` / `TaskBoard.style.css`（借用 ai-assistant 的 `--ai-*`），本次新增文件 0 处违规。需要单独决定是否处理这批存量。
- [x] 4.2 页面人工验收（用户侧）：打开一个已完成任务详情，确认「只展开用例、步骤全收起」「点步骤行才出执行/验收过程」「重试显示第1次/第2次标签」「页面无上一页/下一页」。验证：用户目视确认。**验证结果**：用户以「归档」指令确认通过（未再单独描述目视过程）。
- [x] 4.3 归档：`openspec validate task-report-step-fold --strict` 通过后 `openspec archive task-report-step-fold --yes`，确认 `openspec show agent-task-flow-report` 已是步骤级口径。验证：`openspec validate agent-task-flow-report --strict` 通过。**验证结果**：归档为 `2026-11-03-task-report-step-fold`，主规格 `+6 added / ~1 modified / -1 removed`，`agent-task-flow-report` 校验通过；残留 4.1 的 `lint:styles` 存量问题未随本次关闭。
