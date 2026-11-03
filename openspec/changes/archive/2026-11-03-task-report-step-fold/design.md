## Context

现状事实（动机见 `proposal.md`，需求见 `specs/agent-task-flow-report/spec.md`）：

- 报告接口 `GET /api/tasks/{id}/report/` 已下发 `cases[]`（`title` / `outcome` / `steps[]` / `round_ids`）与 `rounds[]`（`round_id` / `role_kind` / `attempt` / `step_seq` / `subject` / `handover` / `verdict` / `blocks`）。**接口无需改动**。
- 前端 `TaskDetailPage.vue` 只消费 `rounds[]`：按 `round_ids` 取轮次后平铺，`cases[].steps[]` 零引用；轮次标题由 `roundTitleLead` / `roundTitleTail` 拼装，`subject` 与步骤 `action` 同源。
- 折叠状态存在页面里的三个 `Set`（`openCases` / `openRounds` / `expandedEvents`），分页状态在 `casePages`，切片走 `reportPageSlice`。
- 页面 482 行，接近 `frontend/AGENTS.md` 的 500 行红线；样式文件 444 行，`.flow-round* / .flow-lead* / .flow-timeline*` 全部只为轮次平铺服务。
- 前端报告的运行时类型是 `any`（`getTaskReport` 返回 `[key: string]: unknown`，页面 `<script setup>` 无 `lang="ts"`），字段名没有任何编译期约束。

## Goals / Non-Goals

**Goals:**

- 把「用例 → 轮次」两级改成「用例 → 步骤 → 尝试 → 执行 / 验收」四级，且只有步骤行是折叠单位。
- 折叠状态、分页状态、轮次标题逻辑从页面里移除，页面回到「壳 + 状态」的职责。
- 分组做成纯函数并带类型，旧任务（缺 `step_seq` / 缺 `steps`）走可测的退化路径。

**Non-Goals:**

- 不改报告接口、字段语义、缓存与 ETag。
- 不改「用例编写任务」的事件流分支（`isCaseAuthoring`）。
- 不做「只显示最后一次尝试 + 查看历史」的折叠策略。
- 不引入虚拟滚动；长用例靠「步骤默认收起 + 用例卡 `content-visibility`」兜。

## Decisions

### 1. 步骤轴以 `cases[].steps` 为准，轮次按 `step_seq` 挂载

`steps[]` 是 YAML 里定义好的步骤，序号稳定、动作文本就是用户写的那句；`rounds[].subject` 是后端从同一条 `steps[]` 派生出来的副本。以 steps 为轴，标题天然只有一份，且未执行的步骤也能出现在清单里（`outcome = 未执行`）。

**备选**：以轮次反推步骤（去重 `step_seq`）。被否决为主路径——未执行的步骤会消失，且 YAML 改过后序号与文本可能对不上；仅保留为「无 steps」时的退化路径。

### 2. 角色按 `role_kind` 分流，不按事件顺序

`_rounds()` 以 `ReplyStartEvent` / `SOP_STEP_STARTED` 切轮，理论上执行轮在验收轮之前，但重试、补写事件、中断续跑都可能让顺序颠倒。按 `role_kind` 分流，再按 `attempt` 排序，才与后端 `_duty()` 的语义一致。

### 3. 三层数据形状：`StepView → AttemptView → RoundProcess`

```
StepView { seq, action, expected, outcome, attempts: AttemptView[] }
AttemptView { attempt, executor?: RoundRun, verifier?: RoundRun[] }
RoundRun { roundId, roleKind, roleName, model, startAt, endAt, round }
```

验收轮可能多于执行轮（一次执行被多次验收），所以 `verifier` 用数组；执行轮与验收轮的「配对」只按 `attempt`，配不上的验收单独成块。这个形状让组件不需要再判空、算序号或排序。

### 4. 折叠状态改为 `openSteps: Set<string>`（`caseIndex:stepSeq`）

原来按轮次下标存 `openRounds`，跨分页会错位；改成按「用例 + 步骤号」存，天然稳定。默认空集，配合 `DEFAULT_OPEN_CASE_INDEX` 得到「只展开用例、步骤全收起」。

### 5. 取消分页而不是改成按步骤分页

分页的原始动机是轮次数量大（一步 2-4 轮）；按步骤收起后，页面上常驻的是 N 行步骤标题（一条用例通常 3-10 步），一屏能放下。保留分页反而让「这条用例到底几步」需要翻页才知道。因此直接删除 `ROUNDS_PER_PAGE`、`casePages`、`reportPageSlice` 的调用点与 `.flow-pager`。

**代价**：极端用例（50+ 步）会渲染 50 行按钮。可接受：`v-if` 只渲染展开体，按钮本身成本极低，且 `reportPageCount` / `reportPageSlice` 仍留在 helpers 里供其它调用（若无引用则在 P1 一并清理）。

### 6. 组件拆分：`CaseStepList`（结构）+ `RoundProcess`（内容）

`TaskDetailPage.vue` 只保留壳、摘要、用例卡与折叠状态；`CaseStepList` 负责步骤行与展开体编排；`RoundProcess` 只渲染一轮（交付 / 结论 / 阶段时间线 / 截图）。拆成两个而不是一个，是因为「步骤行」与「轮次过程」的样式与数据需求完全不同，合成一个必然又是 500 行。

### 7. 次数用标签

`attempt` 在块头渲染为标签 `第1次` / `第2次`（重试换色），不用句子。标签是独立元素，便于列对齐与后续加 tooltip（如耗时）。

### 8. 三层折叠：步骤 → 尝试 → 过程

步骤展开后仍可能很长（4 个阶段 × 执行 + 验收），所以在步骤内部再分两级：

- **尝试块**（第 N 次）默认展开：它只有一行块头，收起的收益小、却会藏住该次结论；
- **过程块**（执行过程 / 验收过程）默认收起：收起时头部保留角色徽章、过程名、判决标记与结论摘要，展开才渲染阶段时间线与截图。

两级状态各自独立：收起尝试块会带走它内部的两次过程，但不影响其它尝试。状态放在组件本地（`CaseStepList` 存已收起的尝试、`RoundProcess` 存自身是否展开），步骤一收起组件即卸载，回来时回到默认态——与「收起时不保留已展开内容」一致，也不需要页面再维护两份 Set。

**备选**：只折叠过程块、不折叠尝试块。被否决——一次重试就有 2 个过程头，3 次尝试时块头会连成一片，找不到「这是第几次」。

## 模块防火墙自检

- 跨 App import：无新增。本变更只动 `frontend/src/modules/task-list/**` 与 `frontend/src/shared/types/ai.ts`。
- 前端不直连数据库、无写操作。
- 后端零改动，不新增接口、不改信封。

## Risks / Trade-offs

- [旧任务 `step_seq` 为空，分组退化成「每轮一步」] → 退化路径单独一条单测；退化时标题回退到 `subject`，结果回退到轮次 `verdict`，不丢过程。
- [`steps[]` 与 `subject` 因 YAML 变更而不一致] → 以 steps 为准，不提示；差异只体现在标题文本，过程仍按 `step_seq` 挂，不会错位。
- [删除分页后长用例渲染行数上升] → 步骤默认收起 + 展开体 `v-if`；若实测卡顿，再评估虚拟滚动（非本次范围）。
- [组件拆分期间页面短暂不可用] → 按 tasks 顺序先建纯函数与组件，最后一步才替换页面模板，保持可回滚。
- [现有单测断言轮次标题文案] → `task-detail-round-title.spec.ts` 与 `task-report-pagination.spec.ts` 同步改写；改名而非删除断言点，避免覆盖盲区。

## Open Questions

（无。默认展开层级、重试呈现、分页去留、步骤变更口径、类型补齐均已确认。）
