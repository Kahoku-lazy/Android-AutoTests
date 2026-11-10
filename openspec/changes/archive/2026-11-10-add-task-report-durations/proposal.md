## Why

任务详情能看出「哪一步过了」，但看不出「哪一步慢」。四层耗时（用例、步骤、执行模型、验收模型）需要的 `started_at` / `ended_at` / `duration_ms` 其实每行事件都落库了，报告接口却一个都没下发——用户要判断"是模型慢还是设备慢"只能自己数时间戳。

## What Changes

- **报告载荷补四层耗时**：`cases[]` 与 `cases[].steps[]` 增加墙钟 `duration_ms`；`rounds[]` 增加 `model_ms`（该轮所有 `ModelCallEndEvent` 的 `duration_ms` 之和）与 `running`。
- **明确两种口径**：用例/步骤用**墙钟**（首事件 `started_at` → 末事件 `ended_at`，含工具执行与重试）；执行/验收轮用**纯模型时长**，因为一轮里既有模型调用也有设备动作，用墙钟冒充"模型耗时"会虚高。
- **运行中的轮次不显示数字**：未拿到 `ended_at` 的轮次给 `running: true`，前端显示「进行中」，不显示 0s 误导。
- **前端只做格式化**：新增 `formatDurationMs` 纯函数（`42s` / `3m12s` / `1h02m`），三处模板各加一个徽标；分组与求和一律在后端完成，前端不重算。
- **不改埋点、不改表结构、不改接口路径**：`_load_events` 的单次扫描多取 2 个 datetime 列，分组口径与排序不变。
- 前端展示位置：用例标题行、步骤行、执行过程块头、验收过程块头。

## 关联文档

- PRD：`PRD-平台总需求` 二、2.2「用户核心旅程」——「任务详情看事件时间线与判决」。本变更把"时间线"补成"带耗时的执行分析"。
- 既有规格：`openspec/specs/agent-task-flow-report`（报告口径与性能预算）、`openspec/specs/task-list-module`（详情页展示规则）。
- 前置变更：`add-task-detail-live-refresh`（运行中 3 秒自动刷新）——运行中轮次显示「进行中」依赖它，否则数字会停在打开瞬间。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `agent-task-flow-report`: 新增「报告给出四层耗时」要求——`cases[].duration_ms`、`cases[].steps[].duration_ms`（墙钟）、`rounds[].model_ms` / `rounds[].running`（纯模型），并保持既有性能预算与字段语义不变。
- `task-list-module`: 新增「详情页展示四层耗时」要求——四处徽标、格式约定、运行中显示「进行中」、0/缺失不显示。

## Impact

- 后端：`backend/apps/task_list/task_reports.py`（`_SLIM_COLUMNS`、`_EventRow`、`_rounds`、`_annotate`、`_flow_cases`）。
- 前端：`frontend/src/shared/types/ai.ts`、`frontend/src/modules/task-list/helpers/report-steps.ts`、`components/CaseStepList.vue`、`components/RoundProcess.vue`、`TaskDetailPage.vue`。
- 测试：`tests/api/test_task_event_flow.py` 补耗时断言；新增 `frontend/tests/task-list/p0/report-durations.spec.ts`。
- 数据库 / 接口路径 / 通道：无改动；只多几个响应字段。
- 非目标：不做跨用例的前端二次汇总；不做耗时排行/趋势图；不改页头「执行 3分12秒」的中文写法（徽标用紧凑格式，二者并存）。
