## Why

`App.vue` 用全局 `<keep-alive :max="5">` 缓存所有路由页面，切页只触发失活（`onDeactivated`）、不触发卸载（`onUnmounted`），而三处静默轮询（任务清单 10 秒、任务详情 3 秒、仪表盘 30 秒）都只在卸载时清理定时器。结果是人已经离开、活还在干：一个后台的任务详情页每小时约打下 87 MB 报告并让后端做 1,200 次全量重建。

同一个根因还带出一个更严重的次生故障：任务详情页的任务标识取自**全局当前路由**（`String(route.params.id)`），离开瞬间变成 `"undefined"`，`Number()` 得 `NaN`，于是打出 `GET /api/tasks/NaN/report/` 的 404；该 404 又触发「清空报告 + 切错误态」的整树重渲染，与 `<Transition mode="out-in">` 搬运缓存页 DOM 的时机相撞，抛出 `insertBefore` 异常，并把缓存页写成错误态、甚至写成别的任务的数据。

既有规格已经要求「离开页面不得继续请求」，但把停止条件挂在「组件卸载」上——这正是 keep-alive 下失效的那一环。

## What Changes

- 任务清单页、任务详情页、仪表盘的静默轮询 MUST 跟随「本页是否仍是当前路由」：失活即停、回到页面才恢复，**MUST NOT 依赖组件卸载**判定「离开」。
- 任务详情页 MUST 只认「本次打开的那个任务」：任务标识在挂载时确定，离开路由后不得再用变化后的路由参数发请求；标识缺失或非数字时不发请求。
- 报告轮询的失败分类收窄：4xx（任务不存在/已删除）立即停止并给手动重试入口，不再按 3/6/12/30 秒退避空转；网络错误与 5xx 仍按既有阶梯退避。
- 删除无引用的 `frontend/src/modules/task-list/composables/useTaskDetail.ts`（内含一个 3 秒 `setInterval` 的旧实现，本次排查中曾被误认为第二个轮询源）。
- 明确不做：不动 `App.vue` 的 keep-alive 配置、不重构 `TaskDetailPage.vue` 的模板根节点、不动轮询间隔与退避阶梯常量、后端零改动。

## 关联文档

- `PRD-平台总需求` 五、非功能约束 ·「实时性」：任务进度与列表走 HTTP 轮询。本变更只改轮询的生命周期，不改通道、不改间隔。
- 既有规格 `task-list-module`：「任务列表查询预算与轮询不叠加」（10 秒间隔、慢请求跳过）；`dashboard-trend-charts`：「仪表盘统计自动刷新」（30 秒、页面隐藏暂停）。
- 在途变更 `add-task-detail-live-refresh`（未归档）：它新增「运行中任务详情页按 3 秒轮询」与「失败退避」。本变更**不**改间隔与退避阶梯，只规定轮询的生命周期与失败分类；两者无文本重叠，先后归档互不影响。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `task-list-module`: 新增「任务页轮询随路由停止」与「任务详情只对本次打开的任务发请求」两条要求。
- `dashboard-trend-charts`: 收窄「仪表盘统计自动刷新」的停止条件——从「组件卸载时清理」改为「离开路由即停（含被 keep-alive 缓存而组件未卸载的情形）」。

## Impact

- 前端：`frontend/src/modules/task-list/TaskDetailPage.vue`、`composables/useReportPoll.ts`、`composables/useTaskList.ts`、`dashboard/composables/useDashboardAutoRefresh.ts`；删除 `composables/useTaskDetail.ts`。
- 测试：`frontend/tests/task-list/p0/`（新增路由标识与生命周期用例、扩展 `useReportPoll.spec.ts`）、`frontend/tests/dashboard/dashboardAutoRefresh.spec.ts`。
- 后端 / 接口 / 路由 / 数据库：无改动。
- 非目标：不改 keep-alive 策略；不重构详情页模板根节点（触发路径被本变更切断后另案观察）；不覆盖串口日志等其它同类轮询位点；不做报告增量拉取（`since_seq`）。
