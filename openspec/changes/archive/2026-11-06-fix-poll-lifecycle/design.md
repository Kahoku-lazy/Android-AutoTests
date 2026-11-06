## Context

动机见 `proposal.md - Why`。方案需要的现状事实：

- `frontend/src/App.vue:18-24` 把**所有**路由包在 `<keep-alive :max="5">` 里，并以 `:key="route.path"` 区分实例。切页 = 失活，`onUnmounted` 不执行。
- 三处轮询各有形态：`useReportPoll` 是 `setTimeout` 自调度（3 秒）、`useTaskList` 是 `setInterval`（10 秒，且每次 `load()` 成功后按「有无非终态任务」重排）、`useDashboardAutoRefresh` 是 `setInterval` + 在途标志（30 秒）。
- `useRoute()` 返回的是 `router.currentRoute` 的响应式代理，是**全局**当前路由，不是「本组件所在的那条路由」。
- `TaskDetailPage.vue` 的 `taskId` 由 `String(route.params.id)` 派生，并被 `watch(taskId, () => loadReport())` 订阅；`loadReport()` 第一步 `flow.value = null`、第二步在失败时写 `error`，而模板用 `v-if="error"` / `v-else` 两个**不同的根 `<div>`**（已用 `@vue/compiler-sfc` 确认根是单个元素，非多根 Fragment）。
- 后端 `TaskReportAPIView` 的 404 需要 `report_cache_meta` 返回 None，而 `/api/tasks/NaN/report/` 连 `<int:task_id>` 都匹配不上，返回的是 Django 的 URL 解析 404——这解释了控制台里那个「大小既不是信封 50 B、也不是任务不存在」的 404。

约束：任务进度 MUST 继续走 HTTP 轮询；后端零改动；不引入新的全局机制。

## Goals / Non-Goals

**Goals:**

- 页面不再是当前路由后，任务清单、任务详情、仪表盘三处轮询在下一拍就停，且判定不依赖组件是否卸载。
- 任务详情页不再因为「全局路由变了」而请示一个不存在的任务，缓存页不会被其它任务的响应改写。
- 4xx 不再进入退避重试，错误定位与处理一致（立即停 + 手动重试）。
- 保持既有用户可感行为：回到页面立即补一次、不出现骨架、不丢展开态与滚动位置。

**Non-Goals:**

- 不动 `App.vue` 的 keep-alive 配置与 `:max="5"`（改全局缓存策略的连带面远大于本缺陷）。
- 不重构 `TaskDetailPage.vue` 的模板根节点（见决策 6）。
- 不改任何轮询间隔、退避常量、后端缓存 TTL（这些属于 `task-list-module` / `platform-load-budget` / `agent-task-flow-report` 已定的预算）。
- 不覆盖串口日志 `useLogPorts` 等其它同类位点（见 Risks）。

## Decisions

**1. 用 `onDeactivated` / `onActivated`，不改 keep-alive 白名单。**

每个轮询器在自己的 composable 里认领生命周期：失活 `stop()`、激活恢复。备选与取舍：

- 备选 A：`<keep-alive :include>` 只缓存需要的页面 → 否。需要给每个 SFC 起 `name`，且知识库助手明确依赖失活语义释放麦克风与 WS（`knowledge-assistant/index.vue` 的注释），改全局策略会牵连它。
- 备选 B：路由守卫里统一停/启 → 否。各轮询器的「该不该跑」条件不同（详情看任务状态、看板看有无运行中任务、仪表盘恒跑），守卫层拿不到这些条件，还得维护一张「哪个页面注册了轮询」的登记表。
- 结论：三个 composable 各自认领，3 个文件、每处约 10 行，语义最直接，且 compposable 已在使用方组件的作用域内，拿得到生命周期钩子。

**2. `onActivated` 首次挂载也会触发，必须加「首次」标记。**

否则首屏会变成「onMounted 拉一次 + onActivated 再拉一次」。写成模块内的 `hasMounted` 本地标志：`onMounted` 置真，`onActivated` 只在已置真时恢复。项目里已有同款范式（`ai-assistant/index.logic.ts` 的 `loadedOnce`），照抄语义即可，不新造概念。

**3. 任务详情的任务标识在 setup 读一次，删掉 `watch(taskId)`。**

`:key="route.path"` 已经保证「一条任务路径一个实例」，实例存续期间 id 本来就不该变；`watch` 唯一的效果就是让实例跟着**全局**路由漂移。备选 `onBeforeRouteUpdate` 只在同一 route record 内参数变化时触发，而本场景是不同 path、不同实例，用不上——为不存在的需求引入依赖。

**4. 非法标识前置守卫，且不进入错误态。**

`Number.isFinite(id)` 不成立时直接 return：不发请求，也不写 `loading` / `error`。缓存页不该因为「别人导航」而被写成错误态，否则用户切回去看到的是「加载报告失败」而不是刚才的报告。

**5. 4xx 立即停，不退避。**

任务按 id 定位，4xx（404）不会因为重试而恢复；截图中一次 `NaN` 就白烧 5 个请求、空转约 7 分钟。实现上让 `refresh()` 把失败原因带回来（`{ ok: false, status }` 形式的返回值或抛出带 `response.status` 的错误），4xx 直接 `failed = true` + `stop()`，网络错误与 5xx 走原有阶梯。备选「统一退避」在 `add-task-detail-live-refresh` 的规格里是简化写法，其意图是抗抖动，4xx 不属于抖动，本次细化不违背。

**6. 不重构模板根节点，「`insertBefore`」先观察。**

崩溃链是：离开路由 → 全局 `params` 变空 → `NaN` 请求 → 404 → `flow = null` + `error = ...` → 根 `<div>` 整体替换 → 与 transition/keep-alive 的 DOM 搬运撞车。决策 1、3、4、5 把这条链的前半段全部切断后，该路径不可达。而把两个根 `<div>` 合并成单根会移动 `.doc-page` 这个 `flex: 1` 布局钩子的层级（`App.vue` 的 `.main-content__body :deep(.doc-page)`），视觉回归面大于收益。留 `tasks.md` 5.2 的观察项，复现再开单。

**7. 失败分类不改 `useTaskList` 与 `useDashboardAutoRefresh`。**

这两处一次失败就是一次失败，没有「资源消失」语义（列表与统计不会 404），套用 4xx 分类只会增加分支。只有报告接口有「目标可能已不存在」的语义。

## 模块防火墙自检

- 跨 App import：无。本变更只改 `frontend/src/modules/task-list/` 与 `frontend/src/modules/dashboard/`，后端零改动。
- `INSERT/UPDATE/DELETE`：无。纯前端读接口。
- 前端不直连数据库：遵守，仍只经 `shared/api-client` 打 `/api/tasks/*` 与 `/api/dashboard/*`。
- 通道：不新增 HTTP 端点、不新增 WebSocket / SSE 生产点；本变更是**减少**既有 GET 的调用次数。
- 模块边界：改动都在模块私有目录内，不新增 `shared/` 共享件；`task-list` 与 `dashboard` 互不引用。

## Risks / Trade-offs

- **失活即停后回到页面看到旧数据** → 缓解：`onActivated` 立即静默补一次；详情页交给既有 3 秒节奏、列表页仅在数据超过 10 秒时补拉；补拉 MUST NOT 显示骨架、MUST NOT 清零。
- **`onActivated` 与 `onMounted` 双拉** → 缓解：首次标记 + 单测断言「首次挂载只发一次请求」。
- **与在途变更 `add-task-detail-live-refresh` 同改 `useReportPoll.ts`** → 缓解：本变更只在文件尾部加生命周期钩子、在失败分支加 4xx 分类，不动调度结构与退避常量；冲突面集中在文件尾。
- **4xx 立即停会让「网关偶发 404」变成永久停** → 缓解：保留既有手动重试入口（`restart()`），提示文案说明「自动刷新已暂停 · 点击重试」。
- **串口日志 `useLogPorts` 是同类位点（同样只在卸载清理）** → 本变更不覆盖：无现场证据，且要连带 `serial-log-module` 规格。记录在此，复现后另开单；它的自动刷新有在途守卫，危害远小于详情页。
- **`insertBefore` 仍可能在其它「离场时改根节点」的页面出现** → 本变更不解决通用问题，只消除本页触发路径；观察项见 `tasks.md` 5.2。

## Migration Plan

纯前端，无数据迁移、无接口变更、无部署顺序要求。

- 上线：构建产物更新，硬刷新生效。
- 回滚：`git revert` 单个提交即可回到现状；`useTaskDetail.ts` 的删除不影响任何引用方（无引用）。
- 灰度：不引入开关。若需临时关闭，把对应轮询间隔常量置 0 的既有约定仍然有效。

## Open Questions

- 是否要把 keep-alive 白名单收敛（只缓存确实需要的页面）？本变更不做，等本单落地后的实测数据再评估——若后台轮询归零后仍有「缓存页占内存」的反馈，再单独立项。
