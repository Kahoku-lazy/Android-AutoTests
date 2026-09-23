## Context

- 失败路径的现状（读码核实）：`store.ts` 8 个 action 共 9 处读 `data.message`（`:124,148,149,176,193,215,236,284,324`），其中 6 处是 `ElMessage.error('获取失败' / '保存失败' / '快照加载失败' / '结构分析失败' / '删除失败' / '页面加载失败')` 的固定文案；catch 块只 `console.error` 或再弹一次通用文案。
- 契约事实：axios 对非 2xx 必然 reject（`shared/api-auth-interceptors.ts:97-101` 只记日志后原样 reject）；`shared/renderers.py:26-33` 对 `<400` 恒置 `status:true`、对 `>=400` 才给 `{status:false,message}`。**推论**：9 处 `data.message` 分支在后端契约下不可达（只有异常 2xx，如 dev 代理回退 HTML，才能命中），但它们不是死代码——它们是「该读 err 却读了 data」的错位写法。
- 同层先例：`element-locator-page-workbench/spec.md:43`「工作区展示中文错误信息与重试入口」；`formatApiError`（`shared/types/api-error.ts:21-43`）已覆盖 message 透传、409 与 `uq_el_element` 冲突、404、500、网络失败。
- `ErrorState` 的按钮文案固定为「重试」（`shared/components/patterns/ErrorState.vue:17-19`），而 `index.vue:89` 绑的是 `store.clearError()` —— 名实不符。
- 删除链路现状：`deleteSnapshot` 清 `snapshot` + `checkedIds`，不清 `analysis` / `selected`（`store.ts:229-232`）；`analysis` 是结构面板与工具条计数的唯一数据源（`index.vue:88,108-110`）。
- 列表上限：`apiGetSnapshots(0, 100)` + `views.py:47` `min(limit, 100)`；`snapshotTotal` 已写已暴露但无读点；dev 库实测 309 条快照。
- 测试现状：`frontend/tests/README.md:23` device-inspector 标记「未开始 / 0 用例」；仓内已有 vitest 用例范式（如 `frontend/tests/device-pool/p0/useDeviceActions.spec.ts`）。
- 环境：平台与设备均可用（设备 `R5CT62RH88F` ONLINE、空闲），真机走查可做；Playwright 需用系统 Edge 通道（本机 playwright 1.62 与已下载 chromium 1228 不匹配）。

## Goals / Non-Goals

**Goals:**

- 后端返回的失败原因到达用户，且「重试」名副其实
- 删除当前快照后界面不残留任何已删数据
- 快照列表不再静默截断
- 把这三件可自动化的事变成回归测试（本模块首个单测）

**Non-Goals:**

- 不改后端、端点、信封与 DB
- 不给快照抽屉加分页 / 加载更多（本次只要求「如实告知」；分页另开）
- 不改 `formatApiError` / `ErrorState` / `api-client` 等共享件（只在模块侧正确使用）
- 不把 9 处 `data.message` 分支当死代码删除（它们保留为异常 2xx 兜底）

## Decisions

**D1 失败原因统一走共享 `formatApiError`，catch 内取值**
写法：`catch (e) { const msg = formatApiError(e as ApiError, '回退文案'); error.value = { message: msg, source }; ElMessage.error(msg) }`。`formatApiError` 经 `@/shared/api-client` re-export 引入（与 element-locator / case-manager 一致）。
备选：自己读 `e?.response?.data?.message` → 否决：仓内已有净化器，且它额外处理 409 / `uq_el_element` / 网络失败 / 500 的技术术语净化；自读会漏掉这些。
备选：删除 9 处 `data.message` 分支 → 否决：那会让异常 2xx（dev 代理回退 HTML、上游网关异常页）静默走成功分支。

**D2 `error` 由字符串改为带来源，retry 按来源重发**
结构：`error = ref<{ message: string; source: 'devices'|'snapshots'|'snapshot'|'analyze' } | null>(null)`；`retry()` 按 `source` 调 `fetchDevices()` / `fetchSnapshots()` / 重放最后一次快照详情或结构分析（需要记住 `lastSnapshotId`）。成功路径按 source 清空对应错误。
备选：保留字符串槽 + 只把按钮文案改成「知道了」→ 否决：用户失去恢复手段，且四源共用会互相覆盖。
备选：四个独立 error 槽 → 否决：当前页面只有一个错误条位，四个槽无处呈现，属过度设计。

**D3 删除当前快照时一并清 `analysis` 与 `selected`**
在既有 `if (snapshot.value?.snapshot_id === id)` 分支内加 `analysis.value = null; selected.value = null`，即提交到与 `applySnapshot` 同样的空态语义。
备选：删除后自动切到最新一条快照 → 否决：无规格依据，且删除后自动跳转会让用户以为删错了。

**D4 抽屉显示总数与展示范围，而不是加分页**
`SnapshotListDrawer` 头部显示「共 {{ snapshotTotal }} 条 · 已显示最近 {{ snapshots.length }} 条」（仅当 `snapshotTotal > snapshots.length` 时补后半句）。
备选：加载更多 / 分页 → 另开变更（会引入滚动加载与分页状态，超出「如实告知」的最小目标）。
备选：不显示、登记为已知限制 → 否决：静默隐瞒 209 条历史正是本次要修的病。

**D5 单测放在 `frontend/tests/device-inspector/p0/store.spec.ts`，mock 模块 `api.ts`**
3 例：① 捕获 409 时 `ElMessage.error` 收到后端 message（而非「获取失败」）；② `retry()` 会再次调用失败的 api 函数；③ 删除当前快照后 `analysis` 为 `null` 且 `filteredAnalysisElements` 为空。
备选：只做真机走查 → 否决：本模块 0 覆盖，且这三件都是纯 store 逻辑，单测成本极低、回归价值最高。

## 模块防火墙自检

- 跨 App import：零新增（只新增对共享 `@/shared/api-client` / `@/shared/types/api-error` 的使用，属共享层）
- 跨 App import service/runner/consumer/state_machine：不涉及
- INSERT/UPDATE/DELETE 收敛到 api.py：不涉及（无后端改动）
- 前端不直连数据库 / 仪表盘只读：不涉及
- HTTP 出口：仍为模块 `api.ts` → `@/shared/api-client`；请求数量与时机不变（只改失败分支的取值与重试的来源）
- 共享层：不改 `ErrorState` / `formatApiError` / `api-client`（按钮文案保持「重试」，因为本变更让它名副其实）
- 后端 / 端点 / 路由 / 迁移：零改动

## Risks / Trade-offs

- [改文案会让既有 Playwright 断言或人工预期失效] → 检索 `frontend/tests` 与 `tests/e2e` 中对「获取失败 / 保存失败」的断言，命中则同步更新；本模块当前 0 用例，风险集中在 e2e 选择器层
- [error 结构变更影响 `index.vue` 的 `v-if="store.error"`] → 同步改为 `v-if="store.error"` 加 `:message="store.error.message"`，一处改完（同文件）
- [retry 需要记住「上次失败的快照 id」] → 只在 `viewSnapshot` / `analyzeSnapshot` 记录，`applySnapshot` 成功时清理；避免记住已删快照 id
- [单测 mock api 层可能与真实契约漂移] → 用例只断言「错误消息来自 error.response.data.message」这一契约形态，不断言具体文案
- [真机走查依赖设备] → 设备 `R5CT62RH88F` 当前在线空闲；异常路径（设备占用 / 409 重名）难以自然构造，验收以单测覆盖为主、真机覆盖「删除当前快照后回到空态」与「抽屉总数」

## Migration Plan

1. store 错误净化与 error 结构 → index.vue 绑定 → 删除后清 analysis/selected → 抽屉总数
2. 单测与 README 状态行
3. 门禁：`npm run lint:styles`、`npx vite build`、store 单测、真机走查（删除当前快照 / 抽屉总数 / 至少一条真实失败路径）
4. 归档：delta 写入 `device-inspector-page`
5. 回滚：纯前端文本改动，`git revert`；无数据迁移

## Open Questions

（无）
