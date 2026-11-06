## 1. 任务详情页的任务标识（P0）

- [x] 1.1 `frontend/src/modules/task-list/TaskDetailPage.vue`：`taskId` 改为 setup 时从本次路由读一次（`Number(route.params.id)`），删除 `watch(taskId, () => loadReport())`，首屏只保留 `onMounted(loadReport)` 一个入口。验证结果：`grep -n "watch(taskId" TaskDetailPage.vue` 无结果；`npm run typecheck` 通过。
- [x] 1.2 `frontend/src/modules/task-list/TaskDetailPage.vue`：`loadReport()` 与 `refreshReport()` 增加前置守卫——`Number.isFinite(taskId)` 不成立时直接返回，不置 `loading`、不写 `error`、不发请求；`refreshReport()` 把 4xx 原样抛出交给轮询器。验证结果：`tests/task-list/p0/task-detail-route-identity.spec.ts` 两条用例覆盖「离开路由不再发请求」与「A→B 不串数据」。
- [x] 1.3 新增 `frontend/tests/task-list/p0/task-detail-route-identity.spec.ts`：照抄 `App.vue` 的 `RouterView → KeepAlive → key=route.path` 结构挂载真实页面。验证结果：新增 2 条用例全绿；**反向验证**——把 `TaskDetailPage.vue` 临时回退到 HEAD 版本后该 spec 2/2 失败（`[195, 201, 201]` 多出一条旧实例为 201 发的请求），确认用例能咬住原缺陷。

## 2. 轮询生命周期跟随路由（P0）

- [x] 2.1 `frontend/src/modules/task-list/composables/useReportPoll.ts`：新增 `onDeactivated`（清定时器、不置 `stopped`）与 `onActivated`（首次激活跳过；`stopped` 为假时立即 `schedule(0)`），并用 `deactivated` 标记让 `schedule()` 在缓存期间不排定时器。验证结果：`useReportPoll.spec.ts` 13 条全绿，新增「失活后不再请求、激活后立即补一次」「失活不恢复已停止的轮询」「404 立即停」「5xx 仍退避」4 条。
- [x] 2.2 `frontend/src/modules/task-list/composables/useTaskList.ts`：`onDeactivated(stopPoll)` + `deactivated` 守卫（`schedulePoll()` 在缓存期间不重排），`onActivated` 静默 `load(true)` 补拉一次。验证结果：`useTaskList.spec.ts` 8 条全绿，新增「离开清单后不再轮询、回来补拉一次」。
- [x] 2.3 `frontend/src/modules/dashboard/composables/useDashboardAutoRefresh.ts`：同款失活停止 / 激活恢复（抽出 `clearTimer` / `startTimer`）。验证结果：`dashboardAutoRefresh.spec.ts` 7 条全绿，新增「失活后停止轮询，回来立即刷新并恢复定时器」。

## 3. 失败分类：4xx 立即停（P1）

- [x] 3.1 `frontend/src/modules/task-list/composables/useReportPoll.ts`：失败分支区分 4xx 与网络错误 / 5xx，4xx 直接 `failed = true` + `stop()`，其余仍走 `REPORT_POLL_BACKOFF_MS`；判定输入取抛出错误的 `response.status`（`httpStatusOf()`），契约写进 `refresh` 参数的注释。验证结果：`useReportPoll.spec.ts` 中「404 立即停止，不进入退避」「5xx 与网络错误仍按退避重试」两条全绿。
- [x] 3.2 `frontend/src/modules/task-list/TaskDetailPage.vue`：`refreshReport()` 按 3.1 契约返回失败分类（4xx 原样抛出，其余返回 `false` 保持静默）。验证结果：`npm run typecheck` 通过；`npx vitest run tests/task-list` 全绿。

## 4. 门禁与人工验收

- [x] 4.1 前端门禁：`npx vitest run tests/task-list tests/dashboard`、`npm run typecheck`、`npm run build:check` 三项全绿。验证结果：25 个文件 / 208 条用例全绿；`vue-tsc --noEmit` 无输出；`vite build` 31.65s 成功。
- [x] 4.2 仓库门禁：`python run.py check` → **22/23 通过**，唯一失败是既有的 `tests/login/p0/LoginView.hero.spec.ts`（工作区 `LoginView.vue` 已改成「AI 智能化测试平台」，spec 仍断言「AI 自动化测试平台」，属用户并行改动，与本变更无关）；全量 `vitest` 476/478，2 条失败同为该 spec。本变更未引入任何新增失败。
- [x] 4.3 人工验收（Chrome Network，只看 XHR，10 秒窗口）：① 任务详情 → 仪表盘后无 `report/`；② 任务清单 → 仪表盘后无 `tasks/`；③ 仪表盘 → 任务详情后无 `stats/`、`activities/`；④ 全程无 `/api/tasks/NaN/report/`、控制台无 `insertBefore`；⑤ A → B → A 三跳后数据与报告不串。验证结果：用户在浏览器按上述五条逐项验收通过（2026-11-06），离开页面后对应接口在 10 秒窗口内无新增请求，控制台不再出现 `NaN` 404 与 `insertBefore`，A → B → A 后仍显示 A 的报告且无错误态。
- [x] 4.4 对照量：用同一窗口复测「停留在运行中任务详情页」的 `report/` 条数与字节数，确认可见状态下的频率与载荷未被本变更改变（仍为 3 秒 / 全量），只消除离开后的请求。验证结果：与 4.3 同轮观测完成——停留期间 `report/` 仍按 3 秒节奏出现、单条大小与改动前一致；未单独记录精确条数（该轮运行中任务时长较短）。

## 5. 收尾与观察

- [x] 5.1 删除 `frontend/src/modules/task-list/composables/useTaskDetail.ts` 及其唯一的测试 `frontend/tests/task-list/p0/useTaskDetail.spec.ts`（内含一个 3 秒 `setInterval` 的旧实现，全仓无组件引用）。验证结果：`grep -rn "useTaskDetail" frontend` 无结果；`helpers/task-detail.ts` 的三个引用方（`StepLogCheck` / `TaskAttemptCard` / `TaskBoard`）不受影响，`isTaskTerminal` 仍由该 helper 内部使用；全量 vitest 仅少这 2 条用例，无新增失败。
- [ ] 5.2 观察项（一周）：复核 `insertBefore` 是否复现。若复现，记录「页面 / 操作路径 / 控制台栈」并另开「详情页模板单根化」变更；若未复现，在 `design.md` 的 Risks 中标注「未复现，观察结束」。
