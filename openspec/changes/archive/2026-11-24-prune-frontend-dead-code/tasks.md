## 1. 基线：先锁等价，再动代码

- [x] 1.1 为 3 个待迁的相对/绝对时间函数写 golden 用例（新建 `frontend/tests/shared/p0/datetime.spec.ts`），覆盖 4 类输入：正常 ISO、空串、非法串（`"not-a-time"`）、未来时刻；逐字断言现有输出（含「刚刚 / N 分钟前 / N 小时前 / 日期」四档与「—」兜底）。验证：`npm run test -- datetime` 全绿，且该文件此时被测对象是**当前** `shared/helpers/datetime.ts`。
- [x] 1.2 为 4 个待迁的调用方补「现口径快照」用例：`device-pool`（相对含 `Invalid Date` 现状、绝对到秒）、`ops-console`（相对含天/月/年、绝对到分）、`bug-manager`（`formatBugTime` 到分、非法返回原串）、`report-generator`（`formatReportTime` 为 `MM-DD HH:mm`）。验证：`npm run test` 对应用例全绿；把实际输出抄进断言，不允许「按预期改写」。
- [x] 1.3 记录删除前基线：`npx vitest run` 的用例总数与通过数、`npm run build` 产物体积，写入 `temps/prune-frontend-dead-code/baseline.txt`。验证：文件存在且含三项数字，供关单对比。

## 2. 删除 12 个零引用文件与 3 个失效用例

- [x] 2.1 删除共享层 3 个零引用文件：`shared/components/StepScreenshotPanel.vue`（373）、`shared/components/RateBar.vue`（84）、`shared/composables/useExpandCollapse.ts`（45）。**`DoodleNote.vue` / `SplitHandle.vue` 不删**——被活规格与 doodle-craft 点名，见 D7/D10。验证：3 个名字在 `src` 内命中 0。
- [x] 2.2 删除 task-list 4 个零引用组件：`components/TaskOutcomeDonut.vue`（158）、`components/TaskMediaThumb.vue`（126）、`components/CaseImportCard.vue`（75）、`components/TaskShareCharts.vue`（43），连带其样式文件 `components/TaskMediaThumb.style.css`（42）。验证：同上；`modules/task-list/index.vue` 与 `TaskBoard.vue` 的 import 列表中不含这 4 个名字。
- [x] 2.3 删除 dashboard 2 个零引用图表组件：`components/DualAxisBarLineChart.vue`（116）、`components/SeriesBarChart.vue`（87）。验证：`DashboardView.logic.ts` 与 `index.vue` 仍能解析（`npm run typecheck` 无 `Cannot find module`）。
- [x] 2.4 删除 2 个零引用辅助模块：`shared/ocrMatch.ts`（63）、`modules/task-list/helpers/yaml-case-titles.ts`（48）。**`modules/bug-manager/helpers/errorDetail.ts` 不删**——`openspec/specs/bug-ticket-management/spec.md` 的 MUST 点名它，见 D7/D10。验证：2 个名字在 `src` 内命中 0。
- [x] 2.5 删除随之失效的 3 个用例文件：`tests/shared/p0/ocrMatch.spec.ts`、`tests/task-list/p0/yaml-case-titles.spec.ts`、`tests/task-list/p0/TaskMediaThumb.spec.ts`。**`DoodleNote.spec.ts` / `errorDetail.spec.ts` 随被测文件恢复而保留**。验证：`npm run test` 全绿；用例总数减少量与删除文件数一致，且**无** `Cannot find module` 类报错。

## 3. 删除死 API、死图标、死动画、死常量

- [x] 3.1 删除 `modules/ai-assistant/api/agents.ts` 整文件（23 行），并修正 `modules/ai-assistant/api/assistants.ts` 文件头「任务清单仍走 api/agents.ts」的过期注释。验证：`src` 内 `api/agents` 命中数 0；`typecheck` 无导出缺失。
- [x] 3.2 删除 `modules/task-list/api/tasks.ts` 的 `getTask` 及其 `TaskDetailResponse` 类型导入（若该导入被其它函数共用则保留）。验证：`getTask` 在 `src` 与 `tests` 命中数 0；`TaskDetailResponse` 仍被需要处正常引用。
- [x] 3.3 删除 `shared/icons/index.ts` 中 30 个未使用图标，保留 15 个在用的（`IconUser` `IconLock` `IconMail` `IconDevice` `IconPlay` `IconBrain` `IconClock` `IconAlertCircle` `IconLayers` `IconMonitor` `IconTrendingUp` `IconActivity` `IconWifi` `IconRefresh` `IconSearch`）。同步把头注释的图标总数改为实际值（D8）。验证：删除的 30 个名字在 `src` 命中 0；保留的 15 个仍能 import；注释数字与 `export const Icon` 计数相等。
- [x] 3.4 删除 `shared/animations.ts` 的 `selectPop` / `iconBounce` / `loadingDots` 三个导出（若其内部 helper 因此无引用，一并删除）。验证：3 个名字在 `src`/`tests` 命中 0；文件内无「声明了但无人调用」的残留 helper。
- [x] 3.5 删除 `modules/task-list/constants.ts` 的 15 个死常量（`TASK_DEVICE_POLL_INTERVAL_MS`、`CASE_SOURCE_PLATFORM` / `CASE_SOURCE_YAML` / `CaseSource` / `CASE_SOURCE_OPTIONS` / `CASE_SOURCE_DEFAULT`、`TASK_REPORT_HEADER_ICON` / `TASK_REPORT_HEADER_GRADIENT`、`TASK_REPORT_POLL_MS`、`REPORT_POLL_BACKOFF_MS`、`REPORT_POLL_MAX_FAILURES`、`DEFAULT_OPEN_CASE_INDEX`、`STEP_EXEC_NO_SHOT_TEXT`、`AGENT_ROUTES`、`ROUTE_LABELS`、`ROUTE_ICONS`）。**保留** `STEP_LOG_CHECK_TITLE` / `STEP_LOG_CHECK_HINT` / `STEP_LOG_CHECK_NO_SHOT_TEXT`（D7 待裁决项，见第 6 组）。验证：15 个名字在 `src` 命中 0；`useTaskList.ts` 与 `TaskBoard.vue` 仍能编译。

## 4. 时间格式化收口

- [x] 4.1 在 `shared/helpers/datetime.ts` 落 5 个入口：`formatRelativeTime(iso, opts?)`（`granularity: "date" | "long"`）、`formatDateTime(iso, opts?)`（`precision: "minute" | "second"`）、`formatMonthDayTime(iso)`、`formatIsoNaive(raw)`，以及内部 `pad2`。模块头注释写明各档位对应哪个页面，删除「那两处旧实现暂未迁回」的过时说明。验证：1.1 的 golden 用例**一字不改**仍全绿。
- [x] 4.2 迁移 `modules/device-pool/helpers.ts`：删除本地 `formatRelativeTime` / `formatDateTime`，改从共享导入；`DevicePoolView.logic.ts` 的导入路径随之调整。验证：1.2 中 device-pool 快照用例除**非法串一例**（应为「—」，见 4.6）外全部不变。
- [x] 4.3 迁移 `modules/ops-console/helpers/datetime.ts`：转为薄包装（D9），内部调 `formatRelativeTime(…, { granularity: "long" })` 与 `formatDateTime(…, { precision: "minute" })`。验证：`ops-console/index.vue` 零改动仍编译；该页快照用例全绿。
- [x] 4.4 迁移 `modules/bug-manager/constants.ts` 的 `formatBugTime` 与 `modules/report-generator/helpers/report-row.ts` 的 `formatReportTime`：改调共享入口，**保留各自「非法串返回原串」的现口径**（不被统一成「—」，见 D5 限定）。验证：两个模块的快照用例全绿，非法串断言仍是原串。
- [x] 4.5 迁移 `modules/task-list/helpers/task-detail.ts` 的 `formatTaskTime` 为共享 `formatIsoNaive`（保持「不解析、只切片」语义）。验证：`TaskBoard.vue` 与 `task-detail.spec.ts` 对应用例全绿。
- [x] 4.6 显式落地唯一行为变化：`device-pool` 相对时间遇非法串由 `Invalid Date` 改为「—」，并在 1.2 的快照用例中把该例期望更新为「—」，同时在断言旁注明「D5 声明的唯一变化」。验证：该用例仅此 1 条断言与基线不同，其余逐字一致。
- [x] 4.7 确认 `modules/ai-assistant/helpers/time-label.ts` **零改动**。验证：`git diff --stat` 不含该文件；其 `tests/ai-assistant/p0/time-label.spec.ts` 全绿。

## 5. 依赖清理

- [x] 5.1 删除 `package.json` 的 `js-yaml` 与 `@types/js-yaml`（唯一使用者 `yaml-case-titles.ts` 已在 2.4 删除），重跑 `npm install` 更新 lock。验证：`src` 内 `js-yaml` 命中 0；`npm run build` 通过。
- [x] 5.2 登记（不删除）零 import 依赖的处理结论：`pinia`（`createPinia()` 已在 `main.ts` 注册但全仓无 `defineStore`）、`mermaid`、`marked`、`dompurify` 在 `src` 内均零 import。本变更**不动**它们（`frontend/AGENTS.md` 技术规范仍把它们列为技术栈，去留需先改规范），只在关单汇报中列出。验证：汇报包含该清单与「未删除 + 原因」。

## 6. 复扫、门禁与文档同步

- [x] 6.1 全量复扫：12 个文件名 + 30 个图标名 + 3 个动画名 + 2 个 CSS 类名 + 15 个常量名 + `getTask` + `api/agents` + `js-yaml`，在 `frontend/src` 与 `frontend/tests` 内命中数均为 0（`openspec/` 与 `dev_docs/` 的归档叙述不计）。验证：复扫输出贴进关单汇报。
- [x] 6.2 文档同步：`shared/icons/index.ts` 头注释图标数、`.agents/skills/doodle-craft/SKILL.md` 的「存量待迁移」清单去掉已删文件、以及任何提到被删文件的模块文档，全部改正。验证：对 12 个文件名做全仓文档复扫，残留引用为 0 或已在同一提交修正（历史审计文档与 `openspec/` 归档为记录，不算）。
- [x] 6.3 登记待裁决项：把 D7 的结论写进关单汇报，共四项——① `task-detail.ts` 详情页装配函数（约 300 行）与 `STEP_LOG_CHECK_*` 常量因 `ai-task-list`（要求详情进入 `/tasks/:taskId`）与 `routes.ts`（无该路由）分叉而未删；② `bug-manager/helpers/errorDetail.ts` 因 `bug-ticket-management` 的 MUST 点名 `splitErrorDetail` 而未删；③ `DoodleNote.vue` 因 `frontend-l4-data-surface` 的 MUST 列为共享卡片零件而未删；④ `SplitHandle.vue` 因 `doodle-craft` 要求「两栏之间 MUST 有 SplitHandle」而未删。验证：汇报含该四条与对应 spec / 技能路径。
- [x] 6.4 前端门禁全绿：`npm run typecheck`、`npm run build`、`npm run lint:styles`、`npm run test`。验证：四条命令 exit 0；若 `typecheck` 有既存错误，逐条标注「既存 / 本次引入」，本次引入的必须为 0。
- [x] 6.5 对比基线：用例总数与产物体积与 1.3 的 `baseline.txt` 对比，说明减少量来源（删除的用例 / 删除的组件）。验证：数字对得上，无「减少量无法解释」的项。
- [x] 6.6 `openspec validate prune-frontend-dead-code --strict` 通过并归档。验证：输出 `Change 'prune-frontend-dead-code' is valid`（`skip_specs: true` 下不得报缺 delta）。
