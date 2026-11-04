## Why

任务详情页只在「用例编写」类任务上轮询：`TaskDetailPage.vue` 的 `schedulePoll()` 第一句是 `if (task.task_kind !== "case_authoring") return`，所以执行类任务（设备控制/SOP）打开后永远停在打开瞬间的状态——页头写着「执行中」，下面一个事件都不会再出现，用户只能反复手动刷新。平台既有约束要求任务进度走 HTTP 轮询（PRD 五、非功能约束「实时性」），这条约束在执行类任务的详情页上还没有兑现。

## What Changes

- **轮询放开到所有运行中任务**：`running` / `pending` 的任务详情页每 3 秒静默拉一次 `GET /api/tasks/{id}/report/`；进入终态（`completed` / `failed` / `interrupted` / `cancelled` / `stopped`）后停止。
- **静默更新与失败退避**：轮询失败不改动已展示内容、不弹错；连续失败按 3s → 6s → 12s → 30s 退避，超过上限改为提示「自动刷新已暂停」并给手动重试。
- **页面隐藏即暂停**：`document.hidden` 时跳过本轮，标签页回到可见时立即补拉一次。
- **刷新绕过浏览器缓存**：报告请求携带 `Cache-Control: no-cache` 强制重验证，复用后端已实现的 ETag/304（[views.py](backend/apps/task_list/views.py) 现有分支），避免运行中任务的 `max-age=60` 把 3 秒轮询变成 60 秒轮询。
- **刷新不打断阅读**：自动刷新 MUST NOT 重置用户已展开的用例、已翻到的页码、已展开的事件明细与滚动位置；只有出现新用例时才回到默认展开态。
- **运行中可见信号**：运行中在「用例执行详情」标题旁显示「运行中 · 自动刷新」（复用既有 `.flow-live` 样式），并在摘要区给出最后更新时间。
- 轮询生命周期抽成 `frontend/src/modules/task-list/composables/useReportPoll.ts`，详情页不再自带 `setTimeout`/`stopPoll` 样板；常量 `CASE_EVENT_POLL_MS` 更名为 `TASK_REPORT_POLL_MS`（全仓仅一处消费）。
- 不改接口字段、不改后端、不改路由。

## 关联文档

- PRD：`PRD-平台总需求` 五、非功能约束 ·「实时性：无 WebSocket / SSE；任务进度与列表靠 HTTP 轮询」。该文档未给详情页刷新单独编号，本变更即该行约束在执行类任务详情页上的落地。
- 依据现状：`openspec/specs/agent-task-flow-report/spec.md` 的「终态任务报告缓存与条件请求」（运行中任务不写缓存、终态任务给出 ETag/304）——本变更只使用它的 304 分支，不修改该能力。
- 与在途变更 `task-report-step-fold` 的关系：该变更重写同一页面的折叠粒度（轮次 → 步骤）并取消分页，但尚未实施（13 项任务全未勾选）。本变更只规定「刷新不得重置阅读状态」这一行为，不规定折叠粒度；两者无论先后落地，行为要求都成立。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `task-list-module`: 新增「运行中任务详情页自动刷新」与「自动刷新不打断已读位置」两条要求（纯新增 requirement，不改写既有「任务详情页按需渲染轮次」中的分页与折叠规则，避免与 `task-report-step-fold` 抢同一段文本）。

## Impact

- 前端：`frontend/src/modules/task-list/TaskDetailPage.vue`（轮询接入、展开状态保持、运行中标识）、新增 `composables/useReportPoll.ts`、`constants.ts`、`api/tasks.ts`（报告请求加 `Cache-Control: no-cache`）。
- 测试：新增 `frontend/tests/task-list/p0/useReportPoll.spec.ts`、`frontend/tests/task-list/p0/task-report-live-refresh.spec.ts`。
- 后端 / 接口 / 路由 / 数据库：无改动。
- 非目标：不做 WebSocket / SSE 推送（PRD 唯一例外仍是知识库语音）；不做运行中报告的服务端缓存与增量拉取（会与 `agent-task-flow-report` 的「运行中任务不写缓存」冲突，另案处理）；不改「用例编写」任务的模型事件流。
