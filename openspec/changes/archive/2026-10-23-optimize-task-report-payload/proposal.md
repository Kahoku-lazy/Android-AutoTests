## Why

任务 142（H6810全功能测试 - 03，156 轮、12 用例）打开一次要 **12.8 秒**（Playwright 实测首屏可见），完全稳定 14.8 秒。定位结果是三个叠加问题，而不是网络：

1. `GET /api/tasks/142/report/` 返回 **9.47MB** JSON、耗时 **4.4s**，其中 `data.rounds`（5.04MB）与 `data.cases[].rounds`（5.06MB）是**同一份轮次数据的完整副本**；
2. 详情页默认展开全部 12 个用例、一次渲染 **60,187 个 DOM 节点**（`.flow-item` 8,640 条），渲染耗时约 8 秒；
3. 任务已终结（failed），事件不再变化，但每次打开都重新扫 174,098 行事件、重新构建同一份 JSON。

## What Changes

- **BREAKING**：`GET /api/tasks/{id}/report/` 的 `data.cases[]` 不再内嵌 `rounds`，改为 `round_ids`（整数数组）；`data.rounds[]` 新增稳定的 `round_id`。响应体积目标：同一任务 9.47MB → ≤5MB。
- 终态任务（`completed` / `failed` / `interrupted` / `cancelled` / `stopped`）的报告 MUST 缓存；第二次请求 MUST 走缓存（本地 <300ms），并带 `ETag`，`If-None-Match` 命中返回 `304`。非终态任务 MUST NOT 缓存；任务重跑或事件新增 MUST 使旧缓存失效。
- 任务详情页默认**只展开第一个用例**；每个用例内的轮次**分页显示 20 条**；用例卡加 `content-visibility: auto`，滚动到视口外不参与布局。DOM 节点目标：60,187 → ≤3,000。
- 前端按 `round_ids` 关联 `rounds`，MUST NOT 在内存里复制整份轮次对象。
- 不做：不删事件表数据、不改事件写入、不删 `ToolCallDeltaEvent` 渲染项（与既有 spec 的 `count` 场景冲突，收益仅 ~0.4MB）、不改报告接口的单轮明细字段。

## 关联文档

无（性能缺陷修复：PRD 未定义任务详情的加载时延，本变更只收紧实现口径）。

## Capabilities

### New Capabilities

（无。变更落在既有两个能力的口径收紧上。）

### Modified Capabilities

- `agent-task-flow-report`: 轮次只下发一份（`round_ids`）、终态报告缓存与条件请求的两条新要求。
- `task-list-module`: 任务详情页的默认展开、轮次分页与按需渲染。

## Impact

- 后端：`backend/apps/task_list/task_reports.py`（`_flow_cases` 改引用）、`backend/apps/task_list/views.py`（缓存 + ETag）、`backend/apps/task_list/api.py`（如需缓存读写入口）
- 前端：`frontend/src/modules/task-list/TaskDetailPage.vue`、`TaskDetailPage.style.css`、`helpers/task-detail.ts`
- 契约：`openspec/openapi.yaml` 若字段形状变化需重新生成
- 测试：`tests/graybox/integration/test_task_flow_report*`、`frontend/tests/task-list/*`
- 不涉及：数据表、迁移、事件写入、计费
