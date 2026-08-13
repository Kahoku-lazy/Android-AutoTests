# 前端 Vitest 第二批测试设计 — device-pool / element-locator / test-runner

> 日期：2026-08-13
> 状态：已评审通过（设计随对话确认，流程：设计→计划→SDD）
> 前置：[DESIGN-module-classification.md](./DESIGN-module-classification.md)（分类基建）与 [PRIORITY_TEMPLATE.md](./PRIORITY_TEMPLATE.md)（P0/P1/P2 约定）为本设计的上位文档，冲突时以两者为准。

## 1. 范围与文件布局

三个稳定小模块开测（case-manager / ai-assistant 因源码被并发改写暂缓，下批）：

```
tests/device-pool/{p0,p1,p2}
tests/element-locator/{p0,p1,p2}
tests/test-runner/{p0,p1,p2}
```

零配置收益自动生效：UI 分栏 4→10、`test:module` 预设、HTML 报告分区、注册表状态更新。

## 2. P0/P1 清单

### 2.1 device-pool（P0 五组）

| # | 单元 | 测什么 |
|---|------|--------|
| 1 | `api.ts` | 12 端点表驱动：URL/method/body 断言（重点 `apiConnectDevice` 默认 `timeout:300`、`is_admin` 布尔转换） |
| 2 | `useHeartbeat` | fake timers：周期 tick、二次 start 幂等（无双定时器）、unmount 后停止 |
| 3 | `useDevicePoolState` | fetchDevices 成功写 devices/currentSerial/queueLength + loading 复位；失败置 error；doScan 异常返回降级 `{status:false,message:'扫描失败'}`；doActivate 成功写 currentSerial 并刷新 |
| 4 | `useDeviceActions` | handleLockClick 他人锁仅 warning 不发请求；handleRefresh scanning/loading 短路；handleRelease 对 RUNNER_OCCUPIED_PREFIXES 占用拒绝释放 |
| 5 | `DevicePoolView.logic` | KPI 统计（online/busy/offline/total 按状态计数）；activeFilter 过滤 + watch 重置页码；mounted 调 loadDevices + startHeartbeat |

P1：do* 成功联动 fetchDevices/fetchQueue；doHeartbeat 吞异常仅 debug；handleNetworkConnect 空 target 短路；openDisconnectDialog 的 isBusyOthers；filteredDevices 越界时 currentPage 收敛；groupedDevices 三分组；ElMessage 成功/失败分支文案。

### 2.2 element-locator（P0 三组）

| # | 单元 | 测什么 |
|---|------|--------|
| 1 | `api.ts` | 37 端点表驱动：URL/method/body（重点 `apiBatchMove*` 的 `parent_id: ?? null` 归一化；`apiClearAll` 有/无 ids 两种 body；`apiListWebElements` params 透传） |
| 2 | `useElementTree` | buildPageTree 扁平→嵌套与孤儿归根；selectPage 对 xpath_candidates 坏 JSON 降级 `[]`；isDescendantOf 拖拽环检测（子拖到自身祖先返回 false） |
| 3 | `useWebGroupTree` + `useApiGroupTree` | `__ungrouped__` → `{group_id:'null'}` 特殊参数映射；两棵同构树共享一套参数化测试夹具（**只共享夹具，不重构源码**） |

P1：doRename 同级重名校验；maxDepth 层级限制；ElMessageBox confirm 取消（reject）时不调 API；bus `elements-saved` on/off 对称。

### 2.3 test-runner（P0 六组）

| # | 单元 | 测什么 |
|---|------|--------|
| 1 | `api.ts` | cancelQueue body 的 snake_case 映射（`client_task_id`/`device_serial`） |
| 2 | `taskUtils` | deriveTaskStatus 全分支（含 queued+终态 outcome 漂移修正）；generateTaskId 计数器递增 + 跳过 existingIds；buildTaskSavePayload logs/failedSteps `slice(-200)` 截断与默认值 |
| 3 | `useDebouncedSave` | fake timers 1s 后只保存脏任务；同 id 连续调度去重；flushSave 立即保存并清定时器 |
| 4 | `useQueuePoller` | 无排队任务自动停止轮询；匹配 client_task_id 时升级字段 + 触发 onTaskActivated/taskAddLog/scheduleSave；已 running 跳过 |
| 5 | `useTaskOperations` | doStartTask 三分支（run_id→绑定 WS；queued→startQueuePolling；无 run 无 queue→设备不可用）；doStopTask 无论 API 成败都收敛 + closeTaskWebSocket + save；doCancelQueue 404 视为成功继续重置 |
| 6 | `useTaskWebSocket` | applyWsMessage 全部消息 case（log/heartbeat/case_started/step_started 去重排序/step_result failedSteps 去重/iteration_result/case_finished 重算 overall/run_finished/device_error）；同 runId 已连接复用不重开 |

P1：doRemoveTask 先停后删、删除失败不剔除本地；createAndStart 校验链（空名/无设备/无用例/interval<5）；initTaskProgress 按 api/web 类型用 availableCases；seq gap 检测 + 重连后注入 `_ws_reconnected`；closeTaskWebSocket 清 map 与 handler；重连 5 次上限后放弃；useQueuePoller 抛错吞 + start 幂等；useDebouncedSave 任务已删不崩不存。

## 3. 全局 mock 策略（本批次五条约定）

1. **api-client 统一 mock**：`vi.mock('@/shared/api-client', () => ({ default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() } }))` — 三个 api.ts 全部表驱动断言。
2. **element-plus**：ElMessage / ElMessageBox 全局 mock；`ElMessageBox.confirm` 用 `mockRejectedValue` 模拟用户取消。
3. **token-storage**：getActive / getToken / getActiveUsername 按需 mock。
4. **全局单例卫生**：useTaskWebSocket 挂 window 的 `_task_ws_map`/`_task_ws_handlers` 在每个 `beforeEach` 里 `closeAllTaskWebSockets()`（或重置 window 键）；taskUtils 的 localStorage `_task_id_counter` 用 `clearAuthStorage()` 同款清理。
5. **animejs**：useDeviceActions 动画依赖，`vi.mock('animejs')`（animate/stagger vi.fn()——composable 直接 import animejs，非 @/shared/animations）。

## 4. 明确不做

- useElementTree / useWebGroupTree / useApiGroupTree 三棵复制粘贴式同构树**不重构源码**，只共享测试夹具。
- index.vue 整页 mount、真实 WebSocket 连接 → P2 / E2E。
- case-manager、ai-assistant（源码在动）、workflow、report-generator、device-inspector、digital-human → 后续批次。
- 不引入新 npm 依赖；不改 src/ 业务代码。

## 5. 成功标准（验收清单）

1. 三模块 P0+P1 用例全部通过；全量 `npx vitest run` 无回归（现有 107 用例不变，新增用例数 = 三模块之和）。
2. `node -e "import('./tests/module-scan.mjs').then(m=>console.log(m.listProjects().join(' ')))"` 输出 10 栏（5 模块 × p0/p1，按模块名升序）。
3. `npm run test:module -- device-pool` / `element-locator` / `test-runner` 各自只跑本模块。
4. `npm run test:report:html` 报告出现 5 个模块分区，KPI 与全量一致。
5. `tests/README.md` 注册表三个模块状态改为 ✅（P0/P1 文件数如实更新）。
6. 命名符合「场景：预期」规范（含 ≤12 字短名例外）；spec 文件头注明 `[P0]/[P1]` 与目录。

## 6. 变更记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-08-13 | 初版：三模块 P0/P1 清单、mock 策略、验收标准 |
