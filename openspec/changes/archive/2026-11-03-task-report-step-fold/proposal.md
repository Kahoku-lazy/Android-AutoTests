## Why

任务详情页把「执行轮」与「验收轮」平铺成两条同级标题，标题里的动作文本又和执行该步的动作是同一句（后端 `_subject()` 直接取 YAML 的 `steps[].action`），一步读下来同一句话出现两遍；要判断「第 2 步过没过」，还得先跨过一整块执行过程找到它的验收轮。报告里早就下发好的 `cases[].steps[]`（序号 / 动作 / 预期 / 结果）前端一次都没用。

## What Changes

- **步骤成为折叠单位**：每条用例下按步骤分组，执行过程与验收过程收进该步骤的展开体；轮次不再有独立标题。动作文本只在步骤行出现一次。
- **默认收起**：进入页面只展开第一条用例的步骤清单，所有步骤展开体默认关闭。
- **重试按「次」分块**：同一步的每次尝试在展开体内单独成块，块头用次数标签（`第1次` / `第2次`），不再写「第 N 次尝试」的句子。
- **取消分页**：一条用例的步骤全量渲染，删除 `ROUNDS_PER_PAGE` 与翻页控件。
- **删除轮次标题逻辑**：`executorRoundNumbers` / `roundTitleLead` / `roundTitleTail` / `roundFlag` 与对应单测下掉；序号只由步骤提供。
- **补报告类型**：`shared/types/ai.ts` 增加 `TaskReportCase` / `TaskReportRound` / `TaskReportStep`，分组函数不再靠字段名约定。
- 不改接口字段、不改 `rounds` / `cases` 的数据结构，后端零改动。

## 关联文档

- 无独立 PRD 编号：本次为任务详情报告页的信息层级调整，对齐既有 OpenSpec 规格 `agent-task-flow-report`（PRD-平台总需求.md 未覆盖该页面）。
- 设计依据：`temps/task-detail-step-fold-proto.html`（方案稿 v2，含可点原型与现状/方案对照）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `agent-task-flow-report`: 折叠粒度由「轮次」改为「步骤」——重写「步骤标题标明模型在做什么」；新增「按步骤分组执行与验收」「步骤默认收起并全量渲染」「重试按次分块并以标签标次数」；「结论与交付挂在对应步骤」改为挂在步骤展开体内。

## Impact

- 前端：`frontend/src/modules/task-list/TaskDetailPage.vue`（瘦身）、新增 `components/CaseStepList.vue` 与 `components/RoundProcess.vue`、`helpers/report-steps.ts`、`constants.ts`、`TaskDetailPage.style.css`、`shared/types/ai.ts`。
- 测试：新增 `frontend/tests/task-list/p0/report-steps.spec.ts`；改写 `task-detail-round-title.spec.ts`；`task-report-pagination.spec.ts` 改为「全量渲染、无分页控件」断言。
- 后端 / 接口 / 路由：无改动。
- 非目标：不动「用例编写任务」的模型事件流；不删历史重试记录；不改报告接口字段。
