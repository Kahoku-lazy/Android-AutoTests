# 第二批三模块 Vitest 用例 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 device-pool / element-locator / test-runner 三个稳定模块补齐 P0+P1 vitest 用例，纳入既有「模块×优先级」分类体系。

**Architecture:** 纯测试交付（不改 src/）：每任务 = 读源码 → 按设计 §2 用例清单写 spec → 跑绿 → pathspec 提交。三个 api.ts 用统一表驱动断言；全局单例（WS map、localStorage 计数器）每用例前清理。

**Tech Stack:** Vitest 4.1.10 + @vue/test-utils + jsdom（现有基建），无新依赖。

**规格来源：** [DESIGN-batch2-3modules.md](./DESIGN-batch2-3modules.md) — 任务编号对应的「测什么」列即本计划的需求来源，验收对应其 §5。

## Global Constraints

- **提交纪律**：主工作区有大量无关未提交文件 + 并发会话随时扫库提交。每个 commit 只 add 本任务 spec 文件，pathspec 提交：`git commit -m "..." -- <files>`。禁止 `git add .`、`git commit -am`。若目标文件/目录出现与己无关的改动，停下报告 BLOCKED。
- pre-commit hook 会自动 stash 未暂存文件，正常现象。
- 所有命令在 `frontend/` 目录运行。
- Commit message 用 Conventional Commits，本计划统一 `test:` 前缀。
- **命名规范**：`describe('[P0] <被测单元>')`、`it('<场景>：<预期>')`（全角「：」；多预期全角「，」；≤12 字单一预期短名可省「：」）。每个 spec 文件头注释注明 `[P0]/[P1] 必测/建议测 — 一句话职责 目录：tests/<module>/p0/`。
- **不改 src/**：测试只读源码；不得为了可测性改导出（除非符号确属实现残留导致完全不可测——此时报告 BLOCKED 而不是改源码）。
- 全量回归基线：现有 107 用例必须保持通过；新用例只增不减。
- 用例中断言行为、不测实现细节；API 层一律 mock（见各任务 MOCK 块）。

---

### Task 1: device-pool P0 — api.ts + useHeartbeat + useDevicePoolState

**Files:**
- Create: `frontend/tests/device-pool/p0/api.spec.ts`
- Create: `frontend/tests/device-pool/p0/useHeartbeat.spec.ts`
- Create: `frontend/tests/device-pool/p0/useDevicePoolState.spec.ts`

**Interfaces:**
- Consumes: 无（首个任务）。复用测试基建：`tests/helpers/mountComposable.ts` 的 `mountComposable`（需要 onMounted 时用）
- Produces: 无跨任务接口；本任务建立 device-pool 的 mock 惯例（Task 2 沿用）

- [ ] **Step 1: 读源码**

Read：`frontend/src/modules/device-pool/api.ts`、`composables/useHeartbeat.ts`、`composables/useDevicePoolState.ts`、`composables/useDeviceActions.ts`（Task 2 备用）。核对以下符号是否存在：api.ts 的 `apiListDevices/apiScanDevices/apiConnectDevice/apiActivate/apiLockDevice/apiReleaseDevice/apiDisconnect/apiGetQueue/apiJoinQueue/apiLeaveQueue/apiHeartbeat`；useHeartbeat 的 `startHeartbeat(tick)/stopHeartbeat/heartbeatActive` 与 `HEARTBEAT_INTERVAL`（来自 constants）；useDevicePoolState 的 `fetchDevices/doScan/doActivate/error/loading/devices/currentSerial/queueLength`。任一不存在 → BLOCKED 报告实际导出。

- [ ] **Step 2: 写 api.spec.ts（12 端点表驱动）**

统一 mock（文件顶部）：
```ts
import { vi } from 'vitest'
import client from '@/shared/api-client'
import * as dpApi from '@/modules/device-pool/api'

vi.mock('@/shared/api-client', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
}))
```
表驱动用例（`it.each`，每条：调用 → 断言 client 方法、URL、body）：
1. `apiListDevices` → `get('/devices')`
2. `apiScanDevices()` → `post('/devices/scan')`；`apiScanDevices('10.0.0.1')` → body `{target:'10.0.0.1'}`
3. `apiConnectDevice('S1',{activate:true,userId:1,timeout:999})` → `post('/devices/connect')` body 含 `activate:true`
4. `apiConnectDevice('S1',{})` → 默认 `timeout:300` 注入 body
5. `apiActivate('S1')` → 对应 URL
6. `apiLockDevice('S1',1,900,'user')` → body `{serial:'S1',user_id:1,timeout:900,type:'user'}`（以源码实际 body 字段为准）
7. `apiReleaseDevice('S1',{userId:1,reason:'done',unlock:true,force:false})` → URL/body
8. `apiDisconnect('S1',{force:true,reason:'x',userId:1,isAdmin:false})` → body `is_admin:false`（布尔字段名以源码为准）
9. `apiGetQueue` → `get('/devices/queue')`（URL 以源码为准）
10. `apiJoinQueue('S1',1)` / `apiLeaveQueue('S1',1)` → URL/body
11. `apiHeartbeat` → URL
12. 每个端点都断言**恰好调用一次**对应 client 方法
说明：URL/method/body 以源码为准；每条用例名形如 `it('apiScanDevices：带 target 时透传 body')`。跑 `npx vitest run --project device-pool/p0`（project 会在文件创建后自动生成）或 `npx vitest run tests/device-pool/p0/api.spec.ts`。

- [ ] **Step 3: 写 useHeartbeat.spec.ts（fake timers）**

文件顶部：`vi.useFakeTimers()`（describe 内），`afterEach(() => { vi.clearAllTimers(); vi.useRealTimers() })`。直接调用 composable（无需 mount，除非有 onUnmounted 清理——若源码用 onUnmounted，则用 `mountComposable` 挂载并 unmount）。用例：
1. `启动后：按 HEARTBEAT_INTERVAL 周期调用 tick`（推进 3 个周期断言 3 次）
2. `二次 start：不产生双定时器`（调用两次后推进一步周期，断言 tick 只加 1）
3. `unmount 后：不再调用 tick`（挂载版：wrapper.unmount() 后推进，tick 不再增加）

- [ ] **Step 4: 写 useDevicePoolState.spec.ts**

统一 mock：`vi.mock('@/modules/device-pool/api')`（全部 11 函数 vi.fn()）。beforeEach `vi.clearAllMocks()`。用例：
1. `fetchDevices 成功：写入 devices/currentSerial/queueLength，loading 复位`（mockResolvedValue 信封 `{status:true,data:{...}}`，响应字段名以源码为准）
2. `fetchDevices 失败：error 置位，loading 复位`（mockRejectedValue 或 `{status:false,message:'xx'}`，断言 error 文案与源码一致）
3. `doScan 异常：返回降级 {status:false,message:'扫描失败'}`（mockRejectedValue 后调用，断言**不抛异常**且返回该对象）
4. `doActivate 成功：写入 currentSerial 并触发刷新`（断言 currentSerial 更新 + fetchDevices 被再次调用——若源码联动为 fetchDevices/fetchQueue 以源码为准）

- [ ] **Step 5: 跑绿并回归**

```bash
npx vitest run tests/device-pool/p0
```
Expected: 全部通过。再跑全量 `npx vitest run`：现有 107 + 新增全绿。

- [ ] **Step 6: Commit**

```bash
git add frontend/tests/device-pool/p0
git commit -m "test: device-pool P0 — api 表驱动 + 心跳轮询 + 设备池状态" -- frontend/tests/device-pool/p0
```

---

### Task 2: device-pool P0 — useDeviceActions + DevicePoolView.logic

**Files:**
- Create: `frontend/tests/device-pool/p0/useDeviceActions.spec.ts`
- Create: `frontend/tests/device-pool/p0/DevicePoolView.logic.spec.ts`

**Interfaces:**
- Consumes: Task 1 的 mock 惯例（api-client/element-plus/animations mock 块）
- Produces: 无

- [ ] **Step 1: 读源码**

Read `composables/useDeviceActions.ts`、`DevicePoolView.logic.ts`、`@/shared/composables/usePagination`（logic 依赖）。核对：`RUNNER_OCCUPIED_PREFIXES`、`getActive()`（token-storage）、`handleLockClick/handleRefresh/handleRelease/handleNetworkConnect/openDisconnectDialog`、KPI 计算字段名（onlineCount/busyCount 等以源码为准）、`usePagination` 导出。任一不符 → BLOCKED。

- [ ] **Step 2: 写 useDeviceActions.spec.ts**

统一 mock：
```ts
vi.mock('@/shared/animations', () => ({ countUpFormatted: vi.fn(), staggerReveal: vi.fn(), animate: vi.fn() }))
vi.mock('element-plus', () => ({ ElMessage: { success: vi.fn(), warning: vi.fn(), error: vi.fn() } }))
vi.mock('@/shared/auth/token-storage', () => ({ getActive: vi.fn(() => 'u1'), getActiveUsername: vi.fn(() => 'u1') }))
```
pool 用**桩对象**注入（不 mock api）：构造 `{ devices: ref([...]), scanning: ref(false), loading: ref(false), doLock: vi.fn(), doRelease: vi.fn(), ... }` 按源码签名补齐。用例：
1. `handleLockClick：他人锁定时仅 warning 不发请求`（目标设备状态含锁且非本人，断言 ElMessage.warning 调用、pool.doLock 未调用）
2. `handleRefresh：scanning/loading 中短路`（不调 loadDevices）
3. `handleRelease：RUNNER_OCCUPIED_PREFIXES 占用拒绝释放`（构造占用者名带 runner 前缀，断言 warning + doRelease 未调用）
4. `handleNetworkConnect：空 target 短路`

- [ ] **Step 3: 写 DevicePoolView.logic.spec.ts**

Mock 三个子 composable：
```ts
vi.mock('@/modules/device-pool/composables/useDevicePoolState', () => ({ useDevicePoolState: vi.fn() }))
vi.mock('@/modules/device-pool/composables/useHeartbeat', () => ({ useHeartbeat: vi.fn() }))
vi.mock('@/modules/device-pool/composables/useDeviceActions', () => ({ useDeviceActions: vi.fn() }))
```
每个返回桩（refs + vi.fn 函数），用 `mountComposable`（需 onMounted 触发）。用例：
1. `KPI：按状态统计 online/busy/offline/total`（注入 4 台设备不同状态，断言 computed 值）
2. `切换 activeFilter：过滤列表并重置页码`
3. `挂载：调用 loadDevices 与 startHeartbeat`

- [ ] **Step 4: 跑绿并回归**（同 Task 1 Step 5 命令，范围 tests/device-pool/p0 + 全量）

- [ ] **Step 5: Commit**

```bash
git add frontend/tests/device-pool/p0
git commit -m "test: device-pool P0 — 设备操作 handler + 页面编排" -- frontend/tests/device-pool/p0
```

---

### Task 3: device-pool P1 + p2 登记

**Files:**
- Create: `frontend/tests/device-pool/p1/useDevicePoolState.spec.ts`
- Create: `frontend/tests/device-pool/p1/useDeviceActions.spec.ts`
- Create: `frontend/tests/device-pool/p1/DevicePoolView.logic.spec.ts`
- Create: `frontend/tests/device-pool/p2/README.md`

**Interfaces:**
- Consumes: Task 1/2 的 mock 惯例
- Produces: 无

- [ ] **Step 1: 写三个 P1 spec**

按设计 §2.1 P1 清单各归其位：
- useDevicePoolState.spec.ts：`do* 成功时联动 fetchDevices/fetchQueue`（每类操作一条，断言刷新调用）；`doHeartbeat：吞异常仅 debug 不抛`
- useDeviceActions.spec.ts：`成功/失败分支的 ElMessage 文案`（mock pool 函数 resolve/reject，断言对应 message 函数）；`openDisconnectDialog：isBusyOthers 计算正确`（他人占用时弹窗文案/标志）
- DevicePoolView.logic.spec.ts：`filteredDevices 越界时 currentPage 收敛到 totalPages`；`groupedDevices：三分组`（按状态分组断言各组内容）

- [ ] **Step 2: 写 p2/README.md**

```markdown
# [P2] 默认不写 Vitest

| 项 | 原因 | 去向 |
|----|------|------|
| DevicePoolView.vue 整页 mount | 多组件拼装，mock 多收益低 | E2E |
| 设备操作动画（animejs） | 视觉无业务分支 | 不测 |
| 真后端扫描/连接/心跳联调 | 依赖设备与网络 | E2E |

优先级约定见：`../../PRIORITY_TEMPLATE.md`
```

- [ ] **Step 3: 跑绿并回归**：`npx vitest run tests/device-pool` + 全量。

- [ ] **Step 4: Commit**

```bash
git add frontend/tests/device-pool
git commit -m "test: device-pool P1 联动/文案/分页收敛 + P2 登记" -- frontend/tests/device-pool
```

---

### Task 4: element-locator P0 — api.ts 表驱动

**Files:**
- Create: `frontend/tests/element-locator/p0/api.spec.ts`

**Interfaces:**
- Consumes: api-client 统一 mock（Task 1 惯例）
- Produces: 无

- [ ] **Step 1: 读源码**

Read `frontend/src/modules/element-locator/api.ts`，列出全部 37 个导出与各自的 method/URL/body 形状。与设计 §2.2 的符号核对；不符 → BLOCKED。

- [ ] **Step 2: 写 api.spec.ts**

统一 mock 同 Task 1。表驱动覆盖**全部 37 端点**（`it.each`），重点用例单独写：
1. `apiBatchMovePages([1,2],5)` → body `{page_ids:[1,2],parent_id:5}`
2. `apiBatchMovePages([1,2],null)` → `parent_id:null` 显式归一化（源码 `?? null` 语义）
3. `apiBatchMoveWebGroups/apiBatchMoveApiGroups` 同款两条（用各自 ids 字段名，以源码为准）
4. `apiClearAll()` 无 ids → body `{}`；`apiClearAll([1,2])` → `{ids:[1,2]}`（body 字段名以源码为准）
5. `apiListWebElements({type:'x',page:2})` → params 透传到 query
其余端点归为一张参数表：`[调用, method, url]` 三元组逐一断言。

- [ ] **Step 3: 跑绿并回归**：`npx vitest run tests/element-locator/p0` + 全量。

- [ ] **Step 4: Commit**

```bash
git add frontend/tests/element-locator/p0
git commit -m "test: element-locator P0 — 37 端点表驱动" -- frontend/tests/element-locator/p0
```

---

### Task 5: element-locator P0 — useElementTree

**Files:**
- Create: `frontend/tests/element-locator/p0/useElementTree.spec.ts`

**Interfaces:**
- Consumes: element-plus / event-bus mock 惯例
- Produces: 无

- [ ] **Step 1: 读源码**

Read `composables/useElementTree.ts`。核对 `buildPageTree`、`selectPage`、`isDescendantOf` 是否**导出**：若未导出，改为经 composable 返回状态测可观察行为（如 selectPage 后 pageTree 结构与 xpath 解析结果）；`bus` 来自 `@/shared/event-bus`。onMounted 自动 loadPages → 用 `mountComposable`。

- [ ] **Step 2: 写 spec**

统一 mock：
```ts
vi.mock('element-plus', () => ({ ElMessage: { success: vi.fn(), warning: vi.fn(), error: vi.fn() }, ElMessageBox: { confirm: vi.fn() } }))
vi.mock('@/modules/element-locator/api', () => ({ apiGetPages: vi.fn(), apiCreatePage: vi.fn(), apiUpdatePage: vi.fn(), apiDeletePage: vi.fn(), apiGetPageElements: vi.fn(), apiBatchMovePages: vi.fn(), apiClearAll: vi.fn() }))
vi.mock('@/shared/event-bus', () => ({ bus: { on: vi.fn(), off: vi.fn(), emit: vi.fn() } }))
```
用例（按设计 §2.2 #2）：
1. `buildPageTree：扁平列表 → 嵌套树，孤儿归根`（若导出直接测；否则经 loadPages 后断言 pageTree 形状）
2. `selectPage：xpath_candidates 坏 JSON 降级为 []`（apiGetPageElements mock 返回坏 JSON，断言选中项 xpath 字段为 []，且不抛异常）
3. `isDescendantOf：子拖到自身祖先返回 false`（构造父子目录，断言拖拽被拒绝/未调 apiBatchMovePages）
4. `onMounted：自动 loadPages`（apiGetPages 被调用）

- [ ] **Step 3: 跑绿并回归**（范围 tests/element-locator/p0 + 全量）

- [ ] **Step 4: Commit**

```bash
git add frontend/tests/element-locator/p0
git commit -m "test: element-locator P0 — 页面树构建/坏 JSON 降级/拖拽环检测" -- frontend/tests/element-locator/p0
```

---

### Task 6: element-locator P0 — useWebGroupTree + useApiGroupTree（共享夹具）

**Files:**
- Create: `frontend/tests/element-locator/helpers/treeGroupFixtures.ts`
- Create: `frontend/tests/element-locator/p0/useWebGroupTree.spec.ts`
- Create: `frontend/tests/element-locator/p0/useApiGroupTree.spec.ts`

**Interfaces:**
- Consumes: Task 5 mock 惯例
- Produces: `treeGroupFixtures.ts` 导出 `makeGroupTreeCases(apiMockKeys)` — 参数化用例工厂，两棵树的 spec 各调用一次

- [ ] **Step 1: 读源码**

Read `composables/useWebGroupTree.ts`、`composables/useApiGroupTree.ts`。核对 `selectGroup`、`__ungrouped__` 常量、各自 api 函数名（apiListWebGroups/apiBatchMoveWebGroups vs apiListApiGroups/apiBatchMoveApiGroups）与返回结构差异。

- [ ] **Step 2: 写共享夹具 treeGroupFixtures.ts**

内容（两树同构参数化）：
```ts
import { describe, expect, it, vi } from 'vitest'

export interface GroupTreeCase {
  name: string
  apiNames: string[]
  run: () => Promise<void> | void
  assert: () => void
}
```
更简做法：导出 `describeGroupTree(moduleName: 'web' | 'api')`，内部含用例：
1. `selectGroup('__ungrouped__')：参数映射为 {group_id:'null'}`（断言对应 apiList 函数收到的 params）
2. `批量移动：目标 null 时 parent_id 归一化`
3. `分组列表：扁平 → 嵌套`（与 Task 5 同构断言）

- [ ] **Step 3: 写两个 spec 各一行调用**

`useWebGroupTree.spec.ts`：mock `@/modules/element-locator/api`（web 组函数）+ `describeGroupTree('web')`。
`useApiGroupTree.spec.ts`：同款（api 组函数）+ `describeGroupTree('api')`。
两文件各自文件头注释按规范。

- [ ] **Step 4: 跑绿并回归 + Commit**

```bash
npx vitest run tests/element-locator/p0 && npx vitest run
git add frontend/tests/element-locator
git commit -m "test: element-locator P0 — Web/API 分组树共享夹具" -- frontend/tests/element-locator
```

---

### Task 7: element-locator P1 + p2 登记

**Files:**
- Create: `frontend/tests/element-locator/p1/useElementTree.spec.ts`
- Create: `frontend/tests/element-locator/p1/useWebGroupTree.spec.ts`（含 api 树并入或独立均可，建议独立 `useApiGroupTree.spec.ts`）
- Create: `frontend/tests/element-locator/p2/README.md`

**Interfaces:**
- Consumes: Task 5/6 mock 惯例
- Produces: 无

- [ ] **Step 1: 写 P1 spec**

按设计 §2.2 P1 清单：
- useElementTree.spec.ts：`doRename：同级重名校验拒绝`；`maxDepth：层级限制下 canCreateSubFolder 为 false`；`ElMessageBox.confirm 取消（reject）：不调 API`；`bus on/off 对称`（unmount 后 off 被调用，mock bus.off 断言）
- useWebGroupTree.spec.ts / useApiGroupTree.spec.ts：各自 `confirm 取消不调 API` 一条（其余 P1 与主树同构则共享夹具内补）

- [ ] **Step 2: 写 p2/README.md**

登记：ElementManager.vue 整页 mount（多组件+长按拖拽动画）、三树同构重构（明确不做）、真后端页面/元素联调 → E2E。

- [ ] **Step 3: 跑绿并回归 + Commit**

```bash
npx vitest run tests/element-locator && npx vitest run
git add frontend/tests/element-locator
git commit -m "test: element-locator P1 重名/层级/取消/事件对称 + P2 登记" -- frontend/tests/element-locator
```

---

### Task 8: test-runner P0 — api.ts + taskUtils

**Files:**
- Create: `frontend/tests/test-runner/p0/api.spec.ts`
- Create: `frontend/tests/test-runner/p0/taskUtils.spec.ts`

**Interfaces:**
- Consumes: api-client 统一 mock
- Produces: 无

- [ ] **Step 1: 读源码**

Read `frontend/src/modules/test-runner/api.ts`、`composables/taskUtils.ts`。核对设计 §2.3 #1#2 的符号：`startRun/stopRun/getActiveRuns/listTasks/saveTask/deleteTask/cancelQueue/listDefinitions/listApiDefinitions/listWebDefinitions/listDevices`；`readTaskCounter/writeTaskCounter/generateTaskId/deriveTaskStatus/isTaskQueued/taskBucket/taskPassRate/buildTaskSavePayload`。

- [ ] **Step 2: 写 api.spec.ts**

统一 client mock。用例：
1. `cancelQueue：body snake_case 映射`（`cancelQueue('ct1','S1')` → body `{client_task_id:'ct1',device_serial:'S1'}`，字段名以源码为准）
2. 其余 9 端点表驱动（method/url/body 三元组）
3. `startRun/stopRun` body 透传

- [ ] **Step 3: 写 taskUtils.spec.ts**

纯函数为主，localStorage 两个函数在 beforeEach `localStorage.clear()`：
1. `deriveTaskStatus 全分支`：`it.each` 覆盖 running/success/failed/queued+终态 outcome 漂移修正/空 status 默认值（各分支预期以源码为准）
2. `generateTaskId：计数器递增 + 跳过 existingIds`（连续生成 'ID-001','ID-002'；传入 existingIds 含 'ID-002' 时跳过；格式以源码为准）
3. `buildTaskSavePayload：logs/failedSteps 超过 200 条截断，缺省字段补默认`（构造 250 条 logs，断言 payload 里只剩 200 条）
4. `taskPassRate：无 completed 时返回 100`（除零路径）
5. `taskBucket：四分类 running/waiting/completed/incomplete`

- [ ] **Step 4: 跑绿并回归 + Commit**

```bash
npx vitest run tests/test-runner/p0 && npx vitest run
git add frontend/tests/test-runner/p0
git commit -m "test: test-runner P0 — api snake_case + taskUtils 纯逻辑" -- frontend/tests/test-runner/p0
```

---

### Task 9: test-runner P0 — useDebouncedSave + useQueuePoller

**Files:**
- Create: `frontend/tests/test-runner/p0/useDebouncedSave.spec.ts`
- Create: `frontend/tests/test-runner/p0/useQueuePoller.spec.ts`

**Interfaces:**
- Consumes: 无（两者均依赖注入，不需 vi.mock）
- Produces: 无

- [ ] **Step 1: 读源码**

Read `composables/useDebouncedSave.ts`、`composables/useQueuePoller.ts`。核对导出签名：`useDebouncedSave(tasks, saveTaskToServer): {scheduleSave, flushSave, cleanup}`；`useQueuePoller(tasks, isTaskQueued, onTaskActivated, taskAddLog, scheduleSave, getActiveRuns): {queuePollTimer, pollQueuedTasks, startQueuePolling, stopQueuePolling}`。

- [ ] **Step 2: 写 useDebouncedSave.spec.ts**

`vi.useFakeTimers()` + afterEach 还原。tasks 用 `ref([...])`，saveTaskToServer vi.fn()。用例：
1. `推进 1s：只对脏任务调 save`（scheduleSave('t1') 后推进 1000ms，断言 save 调一次参数含 t1 数据）
2. `同 id 连续调度：去重只存一次`
3. `flushSave：立即保存并清定时器`（flush 后再推进 1s 不重复调）
4. `任务已从 tasks 删除：不崩溃不调 save`（scheduleSave 后把 tasks 清空，推进 1s 断言 save 未调——若源码用 find 找不到即跳过）

- [ ] **Step 3: 写 useQueuePoller.spec.ts**

fake timers 同上；tasks ref + 全部注入函数 vi.fn()；getActiveRuns mockResolvedValue。用例：
1. `无排队任务：轮询自动停止`（start 后推进 1500ms 两次，getActiveRuns 只被调一次）
2. `匹配 client_task_id：任务升级 running + 触发三个回调`（断言字段 runId/status 更新、onTaskActivated/taskAddLog/scheduleSave 调用）
3. `已 running 的任务：跳过`
4. `getActiveRuns 抛错：被吞不抛`（mockRejectedValue 后推进，断言不抛、轮询状态可用源码语义断言）
5. `startQueuePolling：幂等不产生双定时器`

- [ ] **Step 4: 跑绿并回归 + Commit**

```bash
npx vitest run tests/test-runner/p0 && npx vitest run
git add frontend/tests/test-runner/p0
git commit -m "test: test-runner P0 — 防抖保存 + 队列轮询" -- frontend/tests/test-runner/p0
```

---

### Task 10: test-runner P0 — useTaskOperations

**Files:**
- Create: `frontend/tests/test-runner/p0/useTaskOperations.spec.ts`

**Interfaces:**
- Consumes: Task 8/9 的 mock 惯例；`../api` 与 `./useTaskWebSocket`、`./taskUtils` 需 vi.mock
- Produces: 无

- [ ] **Step 1: 读源码**

Read `composables/useTaskOperations.ts`。核对 12 个注入参数名与 `normalizeCaseIds/initTaskProgress` 行为、`createAndStart` 校验分支（空名/无设备/无用例/interval<5 各自提示文案）。

- [ ] **Step 2: 写 spec**

Mock：
```ts
vi.mock('@/modules/test-runner/api', () => ({ startRun: vi.fn(), stopRun: vi.fn(), deleteTask: vi.fn(), cancelQueue: vi.fn() }))
vi.mock('@/modules/test-runner/composables/useTaskWebSocket', () => ({ closeTaskWebSocket: vi.fn() }))
vi.mock('element-plus', () => ({ ElMessage: { success: vi.fn(), warning: vi.fn(), error: vi.fn() } }))
```
构造注入桩（12 参数全 vi.fn/ref），用 `mountComposable` 或直接调用（若含 onMounted 用前者）。用例：
1. `doStartTask：run_id 存在 → 绑定 WS`（startRun resolve `{status:true,data:{run_id:'r1'}}`，断言 bindListTaskWS 调用）
2. `doStartTask：queued 任务 → startQueuePolling`
3. `doStartTask：无 run 无 queue → 设备不可用提示`（ElMessage.warning 文案以源码为准）
4. `doStopTask：API 失败也收敛 done/stopped 并 closeTaskWebSocket + save`（mockRejectedValue 仍断言本地状态与回调）
5. `doCancelQueue：404 视为成功继续重置`（reject `{response:{status:404}}`）
6. `doRemoveTask：删除失败不剔除本地`（deleteTask reject，断言 tasks 中任务仍在）
7. `createAndStart：空名/无设备/无用例/interval<5 校验链`（四条各一条，断言 warning 且不调 startRun）

- [ ] **Step 3: 跑绿并回归 + Commit**

```bash
npx vitest run tests/test-runner/p0 && npx vitest run
git add frontend/tests/test-runner/p0
git commit -m "test: test-runner P0 — 任务操作编排三分支/收敛/校验链" -- frontend/tests/test-runner/p0
```

---

### Task 11: test-runner P0 — useTaskWebSocket

**Files:**
- Create: `frontend/tests/test-runner/p0/useTaskWebSocket.spec.ts`

**Interfaces:**
- Consumes: Task 10 的 api mock 惯例
- Produces: 无

- [ ] **Step 1: 读源码**

Read `composables/useTaskWebSocket.ts`。核对：`applyWsMessage(task, msg, hooks)` 的全部 case（log/heartbeat/case_started/step_started/step_result/iteration_result/case_finished/run_finished/device_error + 默认）、hooks 参数形状、`connectTaskWebSocket/closeTaskWebSocket/closeAllTaskWebSockets/getWsMap/setWsMap`、重连退避常量（1s/2s/4s/8s/16s 封顶 30s、5 次上限）、`wsUrl`/`getToken` import。

- [ ] **Step 2: 写 spec**

顶部：
```ts
class FakeWebSocket {
  static instances: FakeWebSocket[] = []
  url = ''
  onopen: ((ev: unknown) => void) | null = null
  onmessage: ((ev: unknown) => void) | null = null
  onclose: ((ev: unknown) => void) | null = null
  onerror: ((ev: unknown) => void) | null = null
  constructor(url: string) { this.url = url; FakeWebSocket.instances.push(this) }
  close = vi.fn(function (this: FakeWebSocket) { this.onclose?.({ code: 1000, reason: 'test' }) })
  send = vi.fn()
}
vi.stubGlobal('WebSocket', FakeWebSocket)
vi.mock('@/shared/ws-url', () => ({ wsUrl: vi.fn((p: string) => 'ws://test' + p) }))
vi.mock('@/shared/auth/token-storage', () => ({ getToken: vi.fn(() => 'tok') }))
```
beforeEach：`FakeWebSocket.instances = []`；`closeAllTaskWebSockets()`；`localStorage.clear()`；fake timers（重连用例内启用）。用例：
1. `applyWsMessage：十种消息 case` — `it.each` 逐 case 构造 msg + hooks 桩，断言任务字段/hook 调用（log 追加、step_started 去重排序、step_result failedSteps 去重、case_finished 重算 overall、run_finished/device_error 状态收敛；预期字段名以源码为准）
2. `connectTaskWebSocket：同 runId 已连接复用不重开`（两次 connect 断言 FakeWebSocket.instances 长度 1）
3. `closeTaskWebSocket：清 map 与 handler`
4. `重连：onclose 后按退避重连，5 次后放弃`（fake timers 逐档推进，断言实例数与最终停止；若源码次数上限不同以源码为准）

- [ ] **Step 3: 跑绿并回归 + Commit**

```bash
npx vitest run tests/test-runner/p0 && npx vitest run
git add frontend/tests/test-runner/p0
git commit -m "test: test-runner P0 — WS 消息分发与重连" -- frontend/tests/test-runner/p0
```

---

### Task 12: test-runner P1 + p2 登记

**Files:**
- Create: `frontend/tests/test-runner/p1/taskUtils.spec.ts`（或并入 useTaskOperations 的 P1 项，以文件归属清晰为准：建议 `useTaskOperations.spec.ts` + `useTaskWebSocket.spec.ts` 两个文件）
- Create: `frontend/tests/test-runner/p2/README.md`

**Interfaces:**
- Consumes: Task 8-11 mock 惯例
- Produces: 无

- [ ] **Step 1: 写 P1 spec**

按设计 §2.3 P1 清单：
- useTaskOperations.spec.ts：`initTaskProgress：api/web 类型用 availableCases`；`restartTask：重置字段后重新启动`（若导出，以源码为准）
- useTaskWebSocket.spec.ts：`seq gap：置 _seqGapDetected，重连后注入 _ws_reconnected`（构造 gap 消息 + 重连，断言 handler 收到的注入标志）；`applyWsMessage 未知 type：安全忽略不抛`
- （useQueuePoller 抛错吞/幂等已在 P0 覆盖，不重复）

- [ ] **Step 2: 写 p2/README.md**

登记：TestRunnerView.vue 整页 mount（WS+轮询+防抖叠加）、真实 WS 连接与重连 E2E、真后端任务联调。

- [ ] **Step 3: 跑绿并回归 + Commit**

```bash
npx vitest run tests/test-runner && npx vitest run
git add frontend/tests/test-runner
git commit -m "test: test-runner P1 seq gap/类型分支 + P2 登记" -- frontend/tests/test-runner
```

---

### Task 13: 收尾 — 注册表更新 + 全量验收

**Files:**
- Modify: `frontend/tests/README.md`（注册表 3 行状态 ✅ + P0/P1 文件数如实填写）

**Interfaces:**
- Consumes: 全部前置任务
- Produces: 验收 §5 六条的最终证据

- [ ] **Step 1: 更新注册表**

按实际创建的 spec 文件数更新三行（device-pool / element-locator / test-runner 状态 → ✅ P0+P1，文件数列如实）。

- [ ] **Step 2: 验收六条**

```bash
npx vitest run                # 1: 全量绿（107 + 三模块新增）
node -e "import('./tests/module-scan.mjs').then(m=>console.log(m.listProjects().join(' ')))"   # 2: 10 栏
npm run test:module -- device-pool   # 3: 三个 module 各跑各的
npm run test:module -- element-locator
npm run test:module -- test-runner
npm run test:report:html      # 4: HTML 报告 5 个模块分区（grep -c "device-pool\|element-locator\|test-runner" tests/reports/html/index.html）
```

Expected: 全绿、10 栏按模块名升序、三模块各自通过、报告分区 ≥3 命中、注册表 ✅（§5 第 5/6 条人工核对）。

- [ ] **Step 3: Commit**

```bash
git add frontend/tests/README.md
git commit -m "test: 注册表登记第二批三模块 ✅" -- frontend/tests/README.md
```

---

## Self-Review 记录

- **Spec 覆盖**：设计 §2.1→Task 1-3；§2.2→Task 4-7；§2.3→Task 8-12；§3 mock 五条→各任务 MOCK 块（单例卫生→Task 8/11 beforeEach）；§5 验收→Task 13。
- **占位扫描**：无 TBD/TODO；「以源码为准」是显式核查指令而非占位（符号清单已给出，实现者先读源码核对，不符即 BLOCKED——测试代码无法在未知源码细节下盲写，此为对既有代码写测试的刻意设计）。
- **类型一致性**：FakeWebSocket / mountComposable / 各 mock 块在任务间引用一致。
