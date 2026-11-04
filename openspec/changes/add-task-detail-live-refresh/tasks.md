## 1. 常量与请求层

- [x] 1.1 `frontend/src/modules/task-list/constants.ts`：把 `CASE_EVENT_POLL_MS` 更名为 `TASK_REPORT_POLL_MS = 3000`，并新增 `REPORT_POLL_BACKOFF_MS = [3000, 6000, 12000, 30000]` 与 `REPORT_POLL_MAX_FAILURES = 5`（唯一真相源，页面与组合式函数都不写字面量）。验证：`grep -r "CASE_EVENT_POLL_MS" frontend/src` 无结果；`npm run typecheck` 通过。
- [x] 1.2 `frontend/src/modules/task-list/api/tasks.ts`：`getTaskReport` 增加请求配置 `headers: { "Cache-Control": "no-cache" }`，不加时间戳参数、不改返回结构。验证：`npm run typecheck` 通过；浏览器 Network 中该请求的 Request Headers 含 `Cache-Control: no-cache`，且未命中内存缓存（出现 `304` 或新的 `200`）。

## 2. 轮询组合式函数

- [x] 2.1 新增 `frontend/src/modules/task-list/composables/useReportPoll.ts`：入参 `refresh: () => Promise<boolean>`（返回本轮是否成功）与 `isActive: () => boolean`；内部用 `setTimeout` 自调度（不用 `setInterval`）、带「在途」标志防并发、`document.hidden` 暂停并在 `visibilitychange` 回补、失败按 `REPORT_POLL_BACKOFF_MS` 退避、连续失败达 `REPORT_POLL_MAX_FAILURES` 停并置 `failed=true`、`onUnmounted` 清理；导出 `{ polling, failed, lastUpdatedAt, restart, stop }`。文件内注释按项目模板写模块说明与函数 Args/Returns。验证：`npm run typecheck` 通过；`npx vitest run tests/task-list/p0/useReportPoll.spec.ts` 全绿。
- [x] 2.2 新增 `frontend/tests/task-list/p0/useReportPoll.spec.ts`：用 fake timers 覆盖六组——到点触发一次、响应未回来不叠加第二次、失败走 3/6/12/30 退避、`document.hidden` 期间不请求且恢复可见立即补一次、`isActive()` 返回 false 后不再调度、卸载后无残留定时器。验证：`npx vitest run tests/task-list/p0/useReportPoll.spec.ts` 全绿，且用例命名与 `specs/task-list-module/spec.md` 的场景一一对应。
- [x] 2.3 在 `useReportPoll.ts` 里补一条守卫：`TASK_REPORT_POLL_MS <= 0` 时视为关闭自动刷新、不排定时器。验证：单测新增断言（间隔传 0 时不产生请求）。

## 3. 详情页接入

- [x] 3.1 `frontend/src/modules/task-list/TaskDetailPage.vue`：删掉自带的 `pollTimer` / `stopPoll` / `schedulePoll`，改用 `useReportPoll`；把 `loadReport(initial)` 拆成首屏用 `loadReport()`（清空 + `loading` + `error`）与刷新用 `refreshReport()`（只替换 `flow`，失败只记 `failed`，不动 `error`、不动 `loading`）。验证：`npm run typecheck` 与 `npm run build` 通过；页面文件行数不因本任务上升（轮询样板移出后应下降）。
- [x] 3.2 展开态保持：把 `watch(cases, ...)` 的触发源换成「用例签名」（用例标题序列 + 用例数量），只有签名变化才重置 `openCases` / `openSteps`；`rounds` 仍按 `round_id` 作 key。验证：`npx vitest run tests/task-list` 全绿（含既有 `task-report-pagination.spec.ts` 不回归）。
- [x] 3.3 运行中信号：在「用例执行详情」标题旁加 `v-if="isRunning"` 的「运行中 · 自动刷新」（复用既有 `.flow-live`），摘要区第 2 项下方显示 `lastUpdatedAt` 格式化后的「更新于 HH:mm:ss」。不改配色、不新增 CSS 变量。验证：`npm run build` + `npm run lint:styles` 通过；人工看运行中页面出现标识、终态后消失。

## 4. 测试与门禁

- [x] 4.1 新增 `frontend/tests/task-list/p0/task-report-live-refresh.spec.ts`：用例集合不变时连续替换 `flow` 后 `openCases` / `openSteps` 保持不变；新增一个用例后回到「只展开第一个用例」；新增轮次追加在末尾且既有 `round_id` 顺序不变。验证：`npx vitest run tests/task-list/p0/task-report-live-refresh.spec.ts` 全绿。
- [x] 4.2 全量前端门禁：`npx vitest run tests/task-list`、`npm run typecheck`、`npm run lint:styles`、`npm run build:check` 四项全绿；不新增 `any`。验证结果：vitest 127/127、typecheck、build:check 三项全绿；`lint:styles` 仍红 50 处 G6 跨边界借用（`StepLogCheck` / `StepLogEvidence` / `TaskAttemptCard` / `TaskBoard` 借用 `--ai-*`），经确认全部为存量、本变更 0 新增（`TaskDetailPage.style.css` 不在清单内，`git show HEAD:…/StepLogCheck.style.css` 已含 `var(--ai-warm-border)`），按「本变更未新增违规」接受，清理另开变更。
- [ ] 4.3 人工验收（一个真在跑的执行类任务，页面停留 5 分钟）：① 新轮次自动出现；② 展开用例后 30 秒仍展开；③ 翻页后刷新不跳页；④ 切后台 2 分钟无请求、切回立刻补一次；⑤ 任务结束自动停止且摘要五项齐全。把观测到的请求总数、`304` 比例与报告接口耗时记录到本变更的说明里。**（用户执行中）**
- [x] 4.4 文档复核：确认 `README.md` 与 `PRD-平台总需求` 的「无 WebSocket / SSE，任务进度走 HTTP 轮询」表述无需改动（本变更只是让既有轮询覆盖到详情页，不新增通道）。验证：`python utils/gen_arch_stats.py --check-md --doc dev_docs/ARCH_PRD/ARCH-平台架构设计.md` 通过。
