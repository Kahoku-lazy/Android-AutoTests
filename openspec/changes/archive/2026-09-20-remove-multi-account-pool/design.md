## Context

动机见 proposal.md - Why。方案需要的现状约束：

- 令牌的唯一读写点是 `frontend/src/shared/auth/token-storage.ts`（`api-client.ts` 与 `useAuthPool.ts` 都从它读写）。当前实现是「`localStorage.auth_accounts` 账号池 + `sessionStorage.auth_active` 逐标签页当前账号」，并带一段「旧单账号扁平键 → 账号池」的迁移分支（`readPool()` 第 19-30 行）。
- 账号池有两个**非 UI** 消费者：`api-auth-interceptors.ts:93-97`（续期失败后按 `getActive()` 决定是否跳登录页）与 `modules/device-pool/composables/useDeviceActions.ts:52`（`currentUser`）。
- `router.ts:36` 的守卫用 `!to.query.add` 给「添加账号」留例外；`tests/e2e/test_login_e2e.py:258-280`（`E2E-009`）依赖这个例外。
- `openspec/specs/frontend-sidebar-hand-drawn` 的 `Interaction behavior unchanged` 明确要求「账号切换菜单」保持可用 —— 与新方向直接冲突，故本变更同时修改该要求。

## Goals / Non-Goals

**Goals:**

- 前端会话收敛为单账号：一个读写点、一套键、一条登出路径。
- 删除侧栏账号切换与「添加账号」入口，保留当前账号名显示与「退出」。
- 让续期失败、登出、路由守卫三条路径在单账号语义下各自只有一种行为，不留「取决于是否还有备用账号」的分支。

**Non-Goals:**

- 不改后端：会话仍按 `sid` 作废，`apps/accounts`、网关公开路径清单、接口契约与接口文档都不动。
- 不引入「跨标签页会话同步」的替代实现（见 Risks 的取舍）。
- 不重做侧栏视觉与登录页视觉，只删除账号菜单相关的 DOM 与样式。

## Decisions

### 1. 单账号存储回退为扁平键：`access_token` / `refresh_token` / `username`

理由：这三个键正是 `token-storage.ts` 现存迁移分支已经在读的「旧单账号格式」，回退即复用既有语义，且不需要给单账号再套一层 JSON 解析与容错。`sessionStorage` 不再参与会话存储。

- 备选：保留 `auth_accounts` 键但只放一个账号 —— 键名与结构继续暗示「池」，还得保留 JSON 解析与损坏兜底，收益为 0。
- 备选：新建 `auth_session` 单账号 JSON 键 —— 需要新增键、解析与文档口径，且与 `E2E-012` 等既有断言口径一起漂移更大。

### 2. 不做「账号池 → 单账号」的反向迁移，但顺带清理残留键

升级后老用户的 `localStorage.auth_accounts` 不再被读取，因此会表现为「未登录」，被守卫送回 `/login` 重新登录一次。

- 理由：`active` 账号存在 `sessionStorage`，服务端与迁移代码都无法知道该给用户选哪个账号；挑错会把用户静默置于非预期账号，比「请重新登录」更糟。
- 清理：新的会话写入点（`saveSession`）在写入后 `removeItem('auth_accounts')`，避免残留的池结构与新键长期并存造成排障困惑。不做开机主动清理（无必要副作用）。

### 3. 删除 `useAuthPool` composable 与 `AuthPool` 类型，登录直接写会话

单账号下不存在「列表 / 切换 / 并发账号」这些需要响应式状态的东西，因此没有保留 composable 的理由。

- `useAuthFlow.authenticate()` 改为调用 `saveSession(username, access_token, refresh_token)`，`UseAuthFlowParams` 去掉 `auth` 入参。
- `LoginView.logic.ts` 去掉 `useAuthPool()`，不再向 `useAuthFlow` 传 `auth`。
- 侧栏显示当前账号：直接 `getUsername()`，不为此保留 composable。它不是响应式的，但侧栏只在登录后挂载，且账号名在组件生命周期内不变（登录会跳转、登出会导航）。
- 备选：保留 `useAuthPool` 名字内部改单账号 —— 「Pool」命名持续误导，且没有第二个消费者。

### 4. 续期失败分支简化为无条件跳转

删除 `AuthInterceptorDeps.getActive` 与 `if (!active)` 判断，续期失败一律 `clearToken()` + `redirectToLogin()`。

- 理由：单账号下清凭证后必然无会话，原条件恒真；保留条件会留下「为什么可能不跳转」的误导分支。
- 连带：`api-client.ts` 去掉 `getActive` 注入；`apiAuthInterceptors.spec.ts` 去掉 `getActive` 桩，原「无剩余账号 / 仍有剩余账号」两条用例合并为一条「续期失败 → 清凭证 + 跳转」。

### 5. 路由守卫去掉 `?add` 例外，登出简化为「清会话 + 回登录页」

`router.ts` 守卫改为「有令牌且访问 `/login` → 一律 `/dashboard`」。`AppSidebar` 删除账号下拉、`switchToAccount`、`finishLocalLogout` 的重载分支与「添加账号」链接；`logout()` 保留 `logoutApi()` 的 503+`retry` 提示分支，其余情况 `clearSession()` 后 `router.push('/login')`。

- 老链接 `/login?add=1` 变成无意义查询参数，被守卫忽略，无副作用。

### 6. 用 `token-storage.spec.ts` 承接被删除的账号池单测

删除 `tests/login/p0/useAuthPool.spec.ts`（5 条）后，单账号存储没有任何直接覆盖。新增 `frontend/tests/login/p0/token-storage.spec.ts`，用 `jsdom` 的 `localStorage` 断言：写入后可读回三项、二次写入覆盖而非追加、`clearSession` 清空三项、写入时清掉残留的 `auth_accounts`。这是**替换**覆盖，不是新增需求。

## 模块防火墙自检

本设计**不触碰**任何后端红线，逐条确认：

- 跨 App import：无。变更全部在 `frontend/src` 内，未新增任何 `apps/*` 之间的 import。
- 跨 App import service/runner/consumer/state_machine：无。
- `INSERT/UPDATE/DELETE` 收敛到 `api.py`：本变更不涉及任何数据库写入，后端代码零改动。
- 前端不直连数据库：无数据库访问；反而**减少**了一条本地存储读取路径（`getActive` 的两个消费者之一被删除）。
- 通信通道：未新增前端 HTTP 出口或 WebSocket 生产点；`AppSidebar` 仍只经 `shared/api/auth.ts` 调 `logout`。
- 引擎边界：不涉及 `airtest` / `uiautomator2` / `engines.android`。

## Risks / Trade-offs

- **[跨标签页不再同步]** → 单账号语义下两个标签页共享同一份 `localStorage` 会话，后登录者覆盖先登录者；先开的标签页可能短时显示旧账号名（令牌已是新的），刷新后一致。这是「移除多账号」的必然结果，本次不为它补替代实现；在 PRD「会话与账号管理」中如实记录。
- **[老用户被强制重新登录一次]** → 见 Decision 2。影响面仅限本地开发环境的一次登录成本；不引入迁移规则以免静默切换账号。
- **[测试与文档口径漂移]** → `E2E-009`（依赖 `?add=1`）、`E2E-012`（断言 `auth_accounts`）、PRD 的 TC-SESSION-003~006、单元测试文档第六节都必须与代码同批改，否则门禁给出虚假绿灯。tasks 中逐条登记。
- **[侧栏账号名非响应式]** → 若后续确有「同页登录态变化需即刻反映」的需求，再引入响应式来源；当前所有改变账号名的路径都会触发导航或跳转，故不预先抽象。

## Migration Plan

1. 先改 `token-storage.ts` 与 `api-auth-interceptors.ts`（底层），再改 `useAuthFlow` / `LoginView.logic` / `AppSidebar` / `router.ts` / `useDeviceActions.ts`（上层），最后同步测试与文档。
2. 回滚策略：本变更集中在单个提交范围内，回滚即恢复 `useAuthPool.ts`、`AuthPool` 类型与池化 `token-storage`；后端未改动，因此无数据侧回滚需求。
3. 部署后无需数据迁移；老会话按 Decision 2 失效一次。
