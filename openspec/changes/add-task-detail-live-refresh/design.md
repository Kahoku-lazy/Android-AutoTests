## Context

现状（见 proposal.md - Why）：`TaskDetailPage.vue` 自带一套 `setTimeout` 轮询，但入口判断把「用例编写」以外的任务全挡掉了；报告接口已支持 ETag/304，运行中任务的响应却带着 `private, max-age=60`；页面每次拿到新 payload 就整体替换 `flow`，而 `watch(cases, ...)` 会在数组引用变化时重置展开态与页码。

约束：任务进度 MUST 走 HTTP 轮询，WS 唯一生产点仍是知识库语音（`backend/gateway/routing.py`、`tests/arch/test_channels.py`）；后端不改。

## Goals / Non-Goals

**Goals:**

- 执行类任务详情页在运行期间自动同步，间隔 3 秒，终态自动停。
- 自动刷新对用户「不可见」（无骨架、无报错）且不打断阅读（展开态、页码、滚动位置不丢）。
- 把轮询生命周期从页面组件里抽出来，成为可单测的组合式函数。

**Non-Goals:**

- 不做 WebSocket / SSE，也不复用知识库语音通道。
- 不做服务端增量接口（`since_seq`）与运行中报告缓存——那会改动 `agent-task-flow-report` 的「运行中任务不写缓存」，另案。
- 不规定折叠粒度（轮次还是步骤），该层归 `task-report-step-fold`。

## Decisions

**1. 用 `setTimeout` 自调度，不用 `setInterval`。**

`setInterval` 在响应慢于 3 秒时会堆积请求；自调度保证「上一轮回来才排下一轮」。代价是真实间隔 = 3 秒 + 请求耗时，对进度展示无影响。另加一个「在途」标志，避免可见性回补与常规轮询并发打同一接口。

**2. 轮询开关只看接口返回的 `task.status`，不看本地事件推断。**

已存在 `isRunning`（`running` / `pending`）。终态集合与后端 `_REPORT_TERMINAL_STATUSES` 对齐，另含 `success`，避免 `success`/`completed` 双写造成「已完成但还在刷」。

**3. 请求头用 `Cache-Control: no-cache`，不加时间戳参数。**

浏览器对带该请求头的 XHR 会走条件请求：命中则复用本地体并拿到 304。加 `?_t=` 会让每次 URL 不同，缓存直接失效、304 永远不命中，且污染访问日志。若实测某些浏览器不强制重验证，退化方案是改用 `axios` 的 `validateStatus` + 手动 `If-None-Match`，仍不加时间戳。

**4. 展开态的重置条件从「数组引用」改成「用例签名」。**

`cases` 每轮都是新数组，引用比较必然触发重置。改为「用例标题序列 + 用例数量」组成的稳定签名：新用例出现才重置（此时默认只展开第一个是合理的），同一用例追加轮次不重置、不跳页。展开集合仍按 index + `round_id` 存（后端 `round_id` 从 0 自增、只追加不改序，可安全作 key）。

**5. 刷新走独立入口 `refreshReport()`，与首屏 `loadReport()` 分离。**

首屏负责清空、骨架、错误态；刷新只替换 `flow` 并更新「最后刷新时刻」。两者混在一个 `initial` 布尔里，最容易写漏「刷新失败却把页面清空」的分支。

**6. 轮询生命周期抽到 `composables/useReportPoll.ts`。**

`TaskDetailPage.vue` 已 482 行，接近规范里的 500 行红线，而样式层早已外置；把「调度 + 退避 + 可见性 + 卸载清理」抽出去既能压住行数，也能让 fake timers 直接测到退避与暂停，不必挂整个页面。

**7. 常量 `CASE_EVENT_POLL_MS` 更名 `TASK_REPORT_POLL_MS`。**

全仓仅 `TaskDetailPage.vue` 一处消费。保留旧名会变成「名字只对应用例编写、实际全任务生效」的错误真相源。

**8. 与在途变更 `task-report-step-fold` 的接口面。**

本设计只依赖两件稳定事实：① 每个可折叠单元的稳定标识；② 折叠状态集合。step-fold 若先落地，把「用例 + `round_id`」换成「步骤 key」即可，行为要求（不重置、不跳页、新用例才回默认）不变。因此两个变更不互斥，只改实现挂点。

## 模块防火墙自检

- 跨 App import：无。本变更只改 `frontend/src/modules/task-list/`，后端零改动。
- `INSERT/UPDATE/DELETE`：无。前端只读，写操作本来也归 `backend/apps/task_list/api.py`，本次不涉及。
- 前端不直连数据库：遵守，仍只经 `shared/api-client` 打 `/api/tasks/{id}/report/`。
- 通道：不新增 HTTP 端点、不新增 WebSocket / SSE 生产点；只是提高既有 GET 的调用频率。
- 模块边界：`task-list` 不被 `ai-assistant` 反向引用；新增 composable 为模块私有，不放进 `shared/`（暂无第二个消费方）。

## Risks / Trade-offs

- **运行中报告每次全量重建**（`_load_events` 扫全部事件）→ 单任务事件量大或多人同时盯详情页时后端压力上升。缓解：只在页面可见时轮询；304 省带宽；把「运行中缓存 + 增量」留作后续变更并记录现状；必要时把间隔上调到 5 秒只需改一个常量。
- **`Cache-Control: no-cache` 的浏览器行为差异** → 若实测未强制重验证，按决策 3 的退化方案改用显式 `If-None-Match`；两条路径都不加时间戳。
- **后端 `round_id` 语义变化** → 若将来改为非自增或重排，展开态 key 会错位。缓解：key 仍以 `round_id` 为主，缺失时退化到「用例序号 + 轮次序号」。
- **与 `task-report-step-fold` 的落地顺序** → 两者都动 `TaskDetailPage.vue`。缓解：本变更的展开态保持按「可折叠单元 key」抽象实现，谁先落地都只需替换 key 来源；合并冲突集中在 `watch` 与展开集合两处。
- **后台定时器节流**（省电模式/移动端）→ 本来就要暂停，节流只会让回补更晚；由 `visibilitychange` 兜底。

## Migration Plan

纯前端，无数据迁移、无接口变更、无部署顺序要求。

- 上线：前端构建产物更新即可，硬刷新后生效。
- 回滚：`git revert` 单个提交即可回到「只有用例编写任务轮询」的状态；`useReportPoll.ts` 无外部引用，删除不影响其他页面。
- 灰度：暂不引入开关；若需要，把 `TASK_REPORT_POLL_MS` 置 0 视为关闭自动刷新的约定。
