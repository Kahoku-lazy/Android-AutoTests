## 1. 固化分块结论（只读，不改代码）

- [x] 1.1 记录分叉点与重叠面：`git merge-base HEAD 1228869b` = `2111f52c`；WIP 1107 文件、HEAD 1537 文件、重叠 1012。验证：把三个数字与 `git diff --shortstat` 输出贴进关单。
- [x] 1.2 把 design.md 的区域重叠表复核一遍（`frontend/src` 49/251/47、`frontend/tests` 10/76/2、`dev_docs/project-viz` 55/12/9、`engines` 82/104/81、`tests` 216/221/216、`.agents/docs` 51/52/51、`.agents/rules` 2/2/2）。验证：逐行实跑 `git diff --name-only <mb> 1228869b -- <area>` 与 HEAD 侧对比，数字一致。

## 2. 丢弃 C 块（注释 / docstring）

- [x] 2.1 明确不搬 `.agents/rules`、`.agents/docs`、`engines`、`tests` 下的任何 WIP 版本。验证：`git status --porcelain` 不出现这些区域因本单产生的改动；`git diff HEAD -- engines tests .agents/rules` 为空。
- [x] 2.2 确认 `frontend/src` 中纯注释差异不做处理（以当前 HEAD 为准）。验证：本单对 `frontend/src` 的改动只包含第 3 组的删除与功能性修改，无「补注释」类改动。
- [x] 2.3 关单写明「C 块已作废，勿再搬」，并说明理由是 `AGENTS.md` 现行「全仓代码不写注释」。验证：关单报告含该结论。

## 3. 重做 A 块剩余部分（前端死代码）

- [x] 3.1 核对「今天已删」清单，避免重复：`task-detail.ts`、`mediaUrl.ts`、`DoodleNote.vue`、`tests/{shared/p0/mediaUrl,task-list/p0/task-detail,task-list/p0/planner-input-format,shared/p0/DoodleNote}.spec.ts` 应已不存在。验证：逐个 `Test-Path` 为 False。
- [x] 3.2 删除剩余 11 个零引用源码文件：`shared/components/StepScreenshotPanel.vue`、`shared/components/RateBar.vue`、`shared/composables/useExpandCollapse.ts`、`modules/task-list/components/{TaskOutcomeDonut,TaskMediaThumb,CaseImportCard,TaskShareCharts}.vue`、`modules/task-list/components/TaskMediaThumb.style.css`、`modules/dashboard/components/{DualAxisBarLineChart,SeriesBarChart}.vue`、`modules/task-list/helpers/yaml-case-titles.ts`、`shared/ocrMatch.ts`。验证：`frontend/src` 内这些名字命中 0；`npm run typecheck` 通过。
- [x] 3.3 删除随之失效的 3 个用例：`tests/shared/p0/ocrMatch.spec.ts`、`tests/task-list/p0/{yaml-case-titles,TaskMediaThumb}.spec.ts`。验证：`npm run test` 全绿，无 `Cannot find module`。
- [x] 3.4 图标库 45 → 15：删除 30 个未使用 `makeIcon` 导出，保留 `IconUser` `IconLock` `IconMail` `IconDevice` `IconPlay` `IconBrain` `IconClock` `IconAlertCircle` `IconLayers` `IconMonitor` `IconTrendingUp` `IconActivity` `IconWifi` `IconRefresh` `IconSearch`；注释按规则不写。验证：`grep -c "^export const Icon"` = 15；删除的 30 个名字在 `src` 命中 0。
- [x] 3.5 删除 `shared/animations.ts` 的 `selectPop` / `iconBounce` / `loadingDots`，并删除 `shared/styles/motion.css` 中只服务它们的 `.wb-loader` / `.wb-select-ring` 两段。验证：3 个名字与 2 个类名在 `src`/`tests` 命中 0；`npm run lint:styles` 通过。
- [x] 3.6 删除 `modules/task-list/constants.ts` 的 15 个死常量（`TASK_DEVICE_POLL_INTERVAL_MS`、`CASE_SOURCE_*` 4 项、`TASK_REPORT_HEADER_*` 2 项、`TASK_REPORT_POLL_MS`、`REPORT_POLL_BACKOFF_MS`、`REPORT_POLL_MAX_FAILURES`、`DEFAULT_OPEN_CASE_INDEX`、`STEP_EXEC_NO_SHOT_TEXT`、`AGENT_ROUTES`、`ROUTE_LABELS`、`ROUTE_ICONS`）。验证：15 个名字在 `src` 命中 0；`useTaskList.ts` 与 `TaskBoard.vue` 仍编译。
- [x] 3.7 时间格式化收口：先为 `device-pool` / `ops-console` / `bug-manager` / `report-generator` 四处写「现口径快照」用例（锁定现值，含设备池非法串的 `Invalid Date` 现状），再在 `shared/helpers/datetime.ts` 落 4 原语 + 2 组选项，改 4 个调用方（task-detail.ts 已随「退详情页」单删除，其 formatTaskTime 不再存在），最后把设备池非法串一例改为「—」并注明这是唯一变化。验证：快照用例中除该一例外，其余断言一字未改仍全绿。
- [x] 3.8 `ai-assistant/helpers/time-label.ts` 保持零改动。验证：`git status` 不含该文件；其用例全绿。

## 4. B 块移交退役（已由 retire-project-viz 承担）

- [x] 4.1 需求方裁决「不要了」后，dev_docs/project-viz/ 由 
etire-project-viz 整目录删除（53 文件），并清掉 .gitignore / 
uff.toml 专属例外与两个技能的「参考实现」表述。验证：openspec list 中 
etire-project-viz 已归档为 2026-11-24-retire-project-viz；dev_docs/project-viz 不存在。
- [x] 4.2 声明 WIP 的 simplify-project-viz-pipeline 随之作废、不再搬回。验证：本单未出现该变更目录，关单报告含该声明。

## 5. 门禁与关单

- [x] 5.1 `npm run typecheck`、`npm run build`、`npm run lint:styles`、`npm run test` 四条 exit 0。验证：记录退出码与用例数。
- [x] 5.2 用例账：以本单开工前为基线，逐项说明差额来自哪些被删用例 / 新增快照用例。验证：差额可对账。
- [x] 5.3 确认未触碰他人未提交改动：`TodayUsageChart.vue`、`useECharts.ts`、`style.css`、`echarts-setup.ts`。验证：`git diff` 中这四个文件的改动仍只有原有那一行 import 与 echarts 相关 WIP 内容。
- [x] 5.4 关单报告：C 块作废理由、A 块剩余清单与结果、B 块搬回与自检结果、WIP 分支后续处置建议（是否删除）。验证：报告落 `dev_docs/DEV_TEST/`，随后归档本单（`skip_specs: true`）。
