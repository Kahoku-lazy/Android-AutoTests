## Why

任务详情页已经不存在，但**两条活规格对它的说法相反**：`openspec/specs/ai-task-list/spec.md:38` 要求「每张卡 MUST 提供『详情』，且『详情』MUST 进入 `/tasks/:id`」，而 `openspec/specs/dashboard-agent-tasks/spec.md:26` 写「MUST 进入任务清单（`/tasks`），MUST NOT 进入**已下线的** `/tasks/:id`」。代码事实站在后者一边：`modules/task-list/routes.ts` 只有 `/tasks`，没有详情路由，也没有详情组件。

结果是详情页的实现（`helpers/task-detail.ts` 的装配函数约 300 行）成了**只被测试驱动**的孤岛：`taskStepBlocks` / `stepBadgeText` / `currentStepLabel` / `defaultStepIndex` / `taskPassCount` / `formatPlannerInputText` / `attemptScreenshotUrl` / `hasLogCheck` / `planGoalText` / `stepTagClass` 生产零调用，而 `task-detail.spec.ts`、`planner-input-format.spec.ts` 仍在为它们跑绿。这类测试最危险：它让人以为「详情页是被测过的」，实际测的是一个已退役页面。

需求方裁决：**退已详情条款**，让规格与代码一致。

## What Changes

- **修改 `ai-task-list` 的「Task list card content and actions」需求**：去掉「详情入口 + 跳转 `/tasks/:id`」，改为明确「任务卡 MUST NOT 提供详情入口，MUST NOT 跳转 `/tasks/:id`」，与 `dashboard-agent-tasks` 对齐。卡面字段、失败/运行中操作、目标全文禁令**逐字保留**。
- **删除 `modules/task-list/helpers/task-detail.ts` 整文件**（362 行）：其中只有 `formatTaskCost` / `formatTaskDuration` 有生产调用，其余全是详情页装配。
- **把在用的两个格式化函数迁到 `modules/task-list/helpers/task-card.ts`**（原样搬移，行为不变），`TaskBoard.vue` 改 import。
- **删除两个只测死代码的用例**：`tests/task-list/p0/task-detail.spec.ts`、`tests/task-list/p0/planner-input-format.spec.ts`；`tests/task-list/p0/datetime.spec.ts` 的 `formatTaskTime` 断言改指向共享 `formatIsoNaive`（语义与断言值不变）。
- **删除三个 `STEP_LOG_CHECK_*` 常量**（`STEP_LOG_CHECK_TITLE` / `STEP_LOG_CHECK_HINT` / `STEP_LOG_CHECK_NO_SHOT_TEXT`）：它们只服务详情页的「日志检查」块。
- **连带清理 `shared/helpers/mediaUrl.ts` 与 `tests/shared/p0/mediaUrl.spec.ts`**：唯一生产使用者是 `task-detail.ts`，删除后零引用，且无任何 spec 点名。
- **不动**：`shared/types/ai.ts` 的 `TaskDetail*` / `TaskRun*` 类型（仍对应服务端 `/tasks/{id}/` 等既有接口，属接口 DTO，删类型不在本单范围）；任务卡的重新执行 / 关闭 / 清空等既有行为。

> **BREAKING**：无对外行为变化。被删入口在代码里本就不存在，本单只是让规格承认这一点。

## 关联文档

无 PRD 编号：本单是**规格纠偏 + 死代码清退**，不新增产品能力。
依据：2026-11-24 前端复杂度体检（发现 `task-detail.ts` 仅测试在用）+ 2026-11-24 需求方裁决「退已详情条款」。
关联记录：`dev_docs/DEV_TEST/DEV-前端死代码清理与时间收口-2026-11-24.md` 第六节待裁决项 1。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `ai-task-list`: 「Task list card content and actions」需求变化——任务卡不再提供「详情」入口、不再跳转 `/tasks/:id`（与 `dashboard-agent-tasks` 既有条款对齐）。

## Impact

- **规格**：`openspec/specs/ai-task-list/spec.md` 的一条 Requirement 经 delta 更新。
- **删除**：`frontend/src/modules/task-list/helpers/task-detail.ts`（362 行）、`frontend/src/shared/helpers/mediaUrl.ts`（15 行）、3 个 `STEP_LOG_CHECK_*` 常量、2 个用例文件、`mediaUrl` 的 1 个用例文件。
- **新增**：`frontend/src/modules/task-list/helpers/task-card.ts`（承接 2 个在用格式化函数）。
- **局部修改**：`modules/task-list/components/TaskBoard.vue`（import 路径）、`tests/task-list/p0/datetime.spec.ts`（import 指向共享实现）、`modules/task-list/constants.ts`（去 3 个常量）。
- **不动**：路由表（本就没有详情路由，无需删）、接口契约、后端与引擎。
- **门禁**：`npm run typecheck` + `npm run build` + `npm run lint:styles` + `npm run test`。
