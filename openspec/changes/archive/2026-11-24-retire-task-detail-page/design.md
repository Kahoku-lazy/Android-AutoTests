## Context

`modules/task-list/helpers/task-detail.ts`（362 行）的 13 个导出里，生产只用 2 个：

| 导出 | 生产调用方 |
|---|---|
| `formatTaskCost` / `formatTaskDuration` | `TaskBoard.vue` |
| `taskStepBlocks` / `stepBadgeText` / `currentStepLabel` / `defaultStepIndex` / `taskPassCount` / `formatPlannerInputText` / `attemptScreenshotUrl` / `hasLogCheck` / `planGoalText` / `stepTagClass` / `isTaskTerminal` / `formatTaskTime` | 无（仅 `task-detail.spec.ts` / `planner-input-format.spec.ts`） |

`shared/helpers/mediaUrl.ts` 唯一生产使用者是 `task-detail.ts` 的 `attemptScreenshotUrl`，删详情模块后归零，且 `openspec/specs/**` 无一处点名。

## Goals / Non-Goals

**Goals:**

1. 规格与代码对齐：`ai-task-list` 不再要求一个不存在的详情页。
2. 删掉只被测试驱动的装配代码，以及为它服务的两个用例——它们给的是「详情页被测过」的假信号。
3. 保留仍在用的两个格式化函数，放进名字诚实的文件。

**Non-Goals:**

- 不恢复详情页（需新建路由 + 页面 + 组件，属功能改版，另案）。
- 不动 `shared/types/ai.ts` 的 `TaskDetail*` / `TaskRun*`：它们是服务端既有接口的 DTO，接口是否下线与前端是否渲染无关。
- 不动任务卡的重新执行 / 关闭 / 清空 / 媒体缩略等既有行为。

## Decisions

**D1：把 `formatTaskCost` / `formatTaskDuration` 搬到新文件 `helpers/task-card.ts`，而不是留在 `task-detail.ts` 里。**
若保留 `task-detail.ts` 只放两个函数，文件名为「详情」却只服务卡片，是新的误导；且删掉其余装配代码后该文件名会让后来者继续去那里找详情逻辑。

**D2：`formatTaskTime` 随 `task-detail.ts` 一起消失。**
它在当前代码里是 `raw.replace("T"," ").slice(0,16)` 的零调用本地实现，没有被其它模块引用；不因为「看起来像通用工具」而捞出来另存。

**D3：`mediaUrl` 一并删除，而不是留作「共享备件」。**
判据：① 零引用（删详情后成立）；② 无 spec / 技能点名（已核）；③ 删除不让任何 MUST 失去所指。三条都满足。

**D4：规格用 MODIFIED 更新原需求，保留全部三个场景名。**
原有 3 个场景（Card fields / Failed and running actions / Detail navigation）。前两个逐字保留；第三个场景名保留但正文改为「没有详情入口、不跳转」，避免归档时被判「丢场景」。备选：删掉该场景 → 否决，会让新口径没有可验证的落点。

**D5：不删 `dashboard-agent-tasks` 的任何文字。**
它本来就写的是「已下线、MUST NOT 进入」，是本单的对齐目标。

**D6：新文件不写注释。**
按 2026-11-24 起生效的全仓规则，`task-card.ts` 与新增用例文件一律不带模块头 / docstring / 行内注释；可读性靠命名与断言表达。

## 模块防火墙自检

- **跨 App import**：不涉及，只动 `frontend/src/modules/task-list/` 与 `frontend/src/shared/`。
- **禁跨层依赖**：`task-card.ts` 只依赖语言内建（`Date.parse` / `toFixed`），不引入 API 或组件。
- **写库收敛**：不涉及任何写操作。
- **前端不直连数据库**：维持。
- **仪表盘只读**：不涉及。

## Risks / Trade-offs

- **[删掉详情装配后，将来恢复详情页得重写]** → 该代码来自旧协议（`goal` / `verification`），恢复详情页本就要按新契约重写；保留反而会让人误以为可复用。
- **[`TaskDetailResponse` 类型留在 `ai.ts` 里可能被误认为还在用]** → 关单说明：类型随接口保留，渲染层不再消费；接口后续下线时另开单删类型。
- **[用例数下降被误读为覆盖率回归]** → 关单写明「删除的 2 个用例，其被测函数已随详情页退役一并删除」，并给出前后用例数。
