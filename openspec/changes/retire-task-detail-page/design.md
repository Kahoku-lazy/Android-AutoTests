## Context

`modules/task-list/` 现存 8 个文件：`index.vue`、`routes.ts`（只有 `/tasks`）、`api/tasks.ts`、`constants.ts`、`composables/useTaskList.ts`、`helpers/{task-detail.ts,case-identity.ts,task-stats.ts}`、`components/{TaskBoard.vue,TaskStatsStrip.vue}`。

`task-detail.ts`（362 行）的 13 个导出里，生产只用 2 个：

| 导出 | 生产调用方 |
|---|---|
| `formatTaskCost` / `formatTaskDuration` | `TaskBoard.vue` |
| `taskStepBlocks` / `stepBadgeText` / `currentStepLabel` / `defaultStepIndex` / `taskPassCount` / `formatPlannerInputText` / `attemptScreenshotUrl` / `hasLogCheck` / `planGoalText` / `stepTagClass` / `isTaskTerminal` | 无（仅 `task-detail.spec.ts` / `planner-input-format.spec.ts`） |
| `TaskStepBlock` / `TaskStepPhase` / `TaskStepAttempt`（类型） | 仅上述函数与测试 |

`shared/helpers/mediaUrl.ts` 唯一生产使用者是 `task-detail.ts:227`（`attemptScreenshotUrl`），删详情模块后归零，且 `openspec/specs/**` 无一处点名。

## Goals / Non-Goals

**Goals:**

1. 规格与代码对齐：`ai-task-list` 不再要求一个不存在的详情页。
2. 删掉只被测试驱动的 300+ 行装配代码，以及为它服务的两个用例——它们给的是「详情页被测过」的假信号。
3. 保留仍在用的两个格式化函数，放进名字诚实的文件。

**Non-Goals:**

- 不恢复详情页（那需要新建路由 + 页面 + 组件，属功能改版，另案）。
- 不动 `shared/types/ai.ts` 的 `TaskDetail*` / `TaskRun*`：它们是服务端既有接口的 DTO，接口是否下线与前端是否渲染无关。
- 不动任务卡的重新执行 / 关闭 / 清空 / 媒体缩略等既有行为。

## Decisions

**D1：把 `formatTaskCost` / `formatTaskDuration` 搬到新文件 `helpers/task-card.ts`，而不是留在 `task-detail.ts` 里。**
若保留 `task-detail.ts` 只放两个函数，文件名为「详情」却只服务卡片，是新的误导；且删掉其余 300 行后该文件名会让后来者继续去那里找详情逻辑。备选：保留原文件名 → 否决。

**D2：`formatTaskTime` 随 `task-detail.ts` 一起消失，其断言改挂共享 `formatIsoNaive`。**
`formatTaskTime` 上一单已改为 `formatIsoNaive` 的薄包装且零调用；删文件时不应把它当成「在用函数」捞出来。`tests/task-list/p0/datetime.spec.ts` 里那 3 条断言（`T` 换空格、空值返回空串、非法串原样切片）语义不变，只把 import 指向 `@/shared/helpers/datetime`。

**D3：`mediaUrl` 一并删除，而不是留作「共享备件」。**
判据沿用上一单的 D10：① 零引用（删详情后成立）；② 无 spec / 技能点名（已核）；③ 删除不让任何 MUST 失去所指。三条都满足，属真死代码。备选：留着 → 否决，它正是上一单那类「共享层备件」把可检索性拖浑的来源。

**D4：规格用 MODIFIED 更新原需求，保留全部三个场景名。**
`ai-task-list` 的「Task list card content and actions」原有 3 个场景（Card fields / Failed and running actions / Detail navigation）。前两个逐字保留；第三个场景名保留但正文改为「没有详情入口、不跳转」，避免归档时被判「丢场景」。备选：删掉该场景 → 否决，会让「不提供详情」这条新口径没有可验证的落点。

**D5：不删 `dashboard-agent-tasks` 的任何文字。**
它本来就写的是「已下线、MUST NOT 进入」，是本单的对齐目标，无需改动。

## 模块防火墙自检

- **跨 App import**：不涉及，只动 `frontend/src/modules/task-list/` 与 `frontend/src/shared/`。
- **禁跨层依赖**：新文件 `task-card.ts` 只依赖语言内建（`Date.parse` / `toFixed`），不引入 API 或组件。
- **写库收敛**：不涉及任何写操作。
- **前端不直连数据库**：维持。
- **仪表盘只读**：不涉及。

## Risks / Trade-offs

- **[删掉详情装配后，将来要恢复详情页得重写]** → 该代码来自旧协议（`goal` / `verification`），恢复详情页本就要按新契重重写；保留反而会让人误以为可复用。
- **[`TaskDetailResponse` 类型留在 `ai.ts` 里可能被误认为还在用]** → 在关单汇报里说明：类型随接口保留，渲染层不再消费；若接口后续下线，另开单删类型。
- **[用例数下降被误读为覆盖率回归]** → 关单明确写出「删除的 2 个用例，其被测函数已随详情页退役一并删除」，并给出前后用例数。
