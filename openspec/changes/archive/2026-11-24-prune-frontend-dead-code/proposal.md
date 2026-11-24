## Why

2026-11-24 的前端复杂度体检（`frontend/src` 35,120 行 / 261 文件）发现两类纯消耗：**① 13 个源码文件在 `src` 内全引用数为 0，合计 1,285 行**，其中 3 个还挂着「只测死代码」的用例，让单测给出假安全感；**② 时间格式化有 6 处 8 个函数各写一套**，`shared/helpers/datetime.ts` 自己的模块头就写着「语义与 device-pool 的既有实现保持一致；那两处旧实现暂未迁回」——共享件已建好，迁移没做完。

两者都不改变任何页面应该长什么样，但都在持续制造假信号：检索「这个组件谁在用」要人工排除一批孤儿，检索「时间怎么格式化」要分辨 6 份实现哪份是当前口径。上一轮死动画清理（`2026-09-14-remove-dead-animation-exports`）保留的 3 个函数，其调用方在此后被删除，现在也已归零——同类欠账正在滚动累积。

> 取证途中另发现 3 个**同为零引用但不应删**的文件（`DoodleNote.vue`、`SplitHandle.vue`、`errorDetail.ts`），它们分别被活规格 / 设计系统技能点名。详见「非目标」与设计 D7：零引用不等于死代码，这三处暴露的是「规格要求、实现未接」的既有漂移。

## What Changes

**A 档：删除已证零引用的死代码（无行为变化）**

- **12 个零引用文件 / 1,260 行**（`src` 内任何 import、模板标签、字符串引用均为 0）：

  | 文件 | 行 | 备注 |
  |---|---:|---|
  | `shared/components/StepScreenshotPanel.vue` | 373 | 详情页下线后遗留 |
  | `modules/task-list/components/TaskOutcomeDonut.vue` | 158 | |
  | `modules/task-list/components/TaskMediaThumb.vue` | 126 | 有单测 |
  | `modules/task-list/components/TaskMediaThumb.style.css` | 42 | 上者的样式层 |
  | `modules/dashboard/components/DualAxisBarLineChart.vue` | 116 | |
  | `modules/dashboard/components/SeriesBarChart.vue` | 87 | |
  | `shared/components/RateBar.vue` | 84 | |
  | `modules/task-list/components/CaseImportCard.vue` | 75 | |
  | `shared/ocrMatch.ts` | 63 | 有单测；引擎侧能力误放在前端 |
  | `modules/task-list/helpers/yaml-case-titles.ts` | 48 | 有单测 |
  | `shared/composables/useExpandCollapse.ts` | 45 | 侧栏仍是手写 `Set` |
  | `modules/task-list/components/TaskShareCharts.vue` | 43 | |

- **`modules/ai-assistant/api/agents.ts`（25 行）**：`listAgents` / `getAgentDetail` / `saveAgent` 三个导出零调用；模块文档 `ai_assistant_style_and_redlines.md:19` 已明确「`api/agents.ts` 在任务清单侧已无引用，删它不必再先改 `task-list`」。同步修正 `assistants.ts` 文件头「任务清单仍走 api/agents.ts」的过期注释。
- **3 个失效用例文件 / 187 行**（其唯一被测对象即上表文件）：`ocrMatch.spec.ts`、`TaskMediaThumb.spec.ts`、`yaml-case-titles.spec.ts`。
- **`modules/task-list/api/tasks.ts` 的 `getTask`**：任务详情页已下线（`routes.ts` 只有 `/tasks`），该接口零调用。
- **`shared/icons/index.ts` 的 30 个未使用图标**：共 45 个 `makeIcon` 导出，全站实际引用 15 个；侧栏导航走 `sidebarNavConfig.ts` 的 lucide 字符串键，与这套自绘图标无关。
- **`shared/animations.ts` 的 3 个死导出**：`selectPop` / `iconBounce` / `loadingDots` 零调用（上一轮保留时仍在用，调用方后被删除）；连带删除只服务它们的 CSS 残留 `.wb-loader` 与 `.wb-select-ring`（`shared/styles/motion.css`）。
- **`modules/task-list/constants.ts` 的 15 个死常量**：`TASK_DEVICE_POLL_INTERVAL_MS`、`CASE_SOURCE_*`（4 个导出）、`TASK_REPORT_HEADER_ICON` / `TASK_REPORT_HEADER_GRADIENT`、`TASK_REPORT_POLL_MS`、`REPORT_POLL_BACKOFF_MS`、`REPORT_POLL_MAX_FAILURES`、`DEFAULT_OPEN_CASE_INDEX`、`STEP_EXEC_NO_SHOT_TEXT`、`AGENT_ROUTES`、`ROUTE_LABELS`、`ROUTE_ICONS`。
- **`js-yaml` 与 `@types/js-yaml`**：唯一使用者 `yaml-case-titles.ts` 已删，依赖随之移除。

**B 档：时间格式化收口为单一实现（输出逐字保持不变）**

- 6 处实现合并到 `shared/helpers/datetime.ts`，暴露 4 个原语 + 2 组选项：
  - `formatRelativeTime(iso, { granularity?: "date" | "long" })` — 默认到「日期」；`long` 追加「天 / 月 / 年」（运营台现口径）
  - `formatDateTime(iso, { precision?: "minute" | "second" })` — 精确到分（运营台、BUG 单）或秒（设备池、用例表）
  - `formatMonthDayTime(iso)` — 「MM-DD HH:mm」（报告台账）；无法解析返回 `null` 由调用方兜底
  - `formatIsoNaive(raw)` — 不解析、不换算，只把 `T` 换空格并截到分（任务卡现口径）
- 改 5 个调用方：`device-pool/helpers.ts` + `DevicePoolView.logic.ts`、`ops-console/helpers/datetime.ts`（转薄包装）、`bug-manager/constants.ts`、`report-generator/helpers/report-row.ts`、`task-list/helpers/task-detail.ts`。
- **唯一可见变化（缺陷修复）**：`device-pool` 的相对时间在**非法时间串**上会漏出 `Invalid Date`（缺 `NaN` 判定），收口后与其它页面一致显示「—」。该口径无 spec 覆盖，属恢复到全站既有兜底行为。

**不改变**：`modules/ai-assistant/helpers/time-label.ts`（36 行）**保持原样**——它刻意「只取墙上时间、不做时区换算」，是另一套语义，不属于本次重复项。

## 关联文档

无 PRD 关联：本变更为纯删除 + 等价重构，不改变任何需求级行为，故 `.openspec.yaml` 设 `skip_specs: true`。
依据：2026-11-24 前端复杂度体检（35,120 行全量扫描）+ 需求方决策「按 1→2 顺序：先删死代码，再收口时间函数」。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 不改变任何 Requirement 文本。所删代码均零引用；时间格式化各页面输出逐字保持，唯一变化是设备池非法时间的兜底文案，该口径无 spec 承载，故不产生 delta。）

## Impact

- **删除**：`frontend/src` 下 13 个文件（1,285 行）+ `frontend/tests` 下 3 个用例文件（187 行）。
- **局部修改**：`shared/icons/index.ts`（45 → 15 个图标）、`shared/animations.ts`（去 3 个导出）、`shared/styles/motion.css`（去 2 段死 CSS）、`modules/task-list/constants.ts`（去 15 个常量）、`modules/task-list/api/tasks.ts`（去 `getTask`）、`shared/helpers/datetime.ts`（扩为唯一实现）、5 个时间格式化调用方、`frontend/package.json` + lock（去 `js-yaml`）。
- **文档同步**：`shared/icons/index.ts` 头注释图标数；`.agents/skills/doodle-craft/SKILL.md` 的「存量待迁移」清单去掉已删的 `TaskMediaThumb` / `CaseImportCard`。
- **不动**：路由、HTTP 出口（仍只 `shared/api-client.ts`）、鉴权、任何接口契约、后端与引擎；工作区里他人未提交的 `dev_docs/project-viz` 等改动一概不碰。
- **门禁**：`npm run typecheck` + `npm run build` + `npm run lint:styles` + `npm run test`。
- **非目标（三处「零引用但不可删」，均属既有 spec 漂移，需需求方裁决）**：
  1. `modules/bug-manager/helpers/errorDetail.ts`（39 行）——`openspec/specs/bug-ticket-management/spec.md` 的 MUST 点名 `splitErrorDetail`；删它会把「规格要求接线、实现未接」变成「规格指向不存在的文件」。
  2. `shared/components/DoodleNote.vue`（178 行）——`openspec/specs/frontend-l4-data-surface/spec.md` 的 MUST 把 `DoodleNote` 列为共享卡片零件。
  3. `shared/components/SplitHandle.vue`（145 行）——`doodle-craft` 的版式规则要求「两栏之间 MUST 有 `SplitHandle`（共享件）」，且 `standalone-html.md` 要求「手柄行为照抄 `shared/components/SplitHandle.vue`」。
  4. 另：`task-detail.ts` 的详情页装配函数（约 300 行）与 `STEP_LOG_CHECK_*` 常量——`ai-task-list` 仍要求详情进入 `/tasks/:taskId`，而 `routes.ts` 无该路由。
- **非目标（本次不做）**：`deviceAddress` 双口径、分页条 8 处重复、ECharts 主题 6 份重复、运营台 `.vue` 业务逻辑下沉、`pinia`/`mermaid`/`marked`/`dompurify` 等零 import 依赖的去留。
