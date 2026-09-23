## Why

登录模块目前把令牌按账号名存进「账号池」，并围绕它实现了侧栏账号切换、添加账号、按账号登出与跨标签页同步。但本平台的会话模型是单账号的（一次登录一个 `sid`，登出作废该会话的全部令牌），多账号池在本仓没有真实使用场景，却把令牌存储、侧栏组件、续期失败分支和 5 条单测都绑在池结构上。本次移除多账号机制，让前端会话回归「一次只持有一个账号」。

## What Changes

- **BREAKING**：前端会话由「多账号池」改为**单账号** —— 本地一次只保存一个账号的 `access_token` / `refresh_token` / `username`，不再有账号列表、逐标签页的「当前账号」（`sessionStorage.auth_active`）与跨标签页同步。
- **BREAKING**：移除侧栏的账号切换 UI —— 用户卡片不再展开账号下拉，菜单里的「添加账号」入口连同 `/login?add=1` 的路由守卫例外一并移除；侧栏仍显示当前账号名与「退出」。
- **BREAKING**：登出行为简化 —— 登出即清空本地会话并回 `/login`，不再「还有别的账号就自动切过去并整页重载」。
- 令牌续期失败时**无条件**清空本地凭证并跳转 `/login`，移除原先「池里还有备用账号就不跳转」的分支。
- 设备页的「当前用户」改为读取单账号会话里的 `username`。
- 移除 `useAuthPool` composable 与 `AuthPool` 类型；`token-storage.ts` 收敛为单账号读写点，仍是 api-client 与页面读令牌的唯一真相源。
- 同步更新 PRD、单元测试文档、功能测试用例与端到端用例中记载多账号行为的段落。

## 关联文档

- PRD：`dev_docs/ARCH_PRD/PRD-00-登录模块.md` —— 「登出」与「会话与账号管理」两节的 §UI交互 / §业务逻辑 / §数据表单，以及 §测试 中 TC-SESSION-003~006 的期望口径（本次变更后这些用例的期望作废）。
- ARCH：`dev_docs/ARCH_PRD/ARCH-平台总体架构.md` —— 前端 `shared/` 层职责与请求链路（令牌注入点）。
- 测试资产：`dev_docs/DEV_TEST/单元测试文档/单元测试-登录.md`（第六节账号池状态层）、`dev_docs/DEV_TEST/功能测试用例/功能测试用例-登录.md`（多账号相关 BF 条目）。
- 说明：模板引用的 `dev_docs/文档编号对照表.md` 在本仓不存在；实际文档位于 `dev_docs/ARCH_PRD/` 与 `dev_docs/DEV_TEST/`。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `auth-session`: 新增「前端单账号会话」要求 —— 本地一次只保留一个账号、登出即清空会话、续期失败无条件清凭证并跳转 `/login`；并明确已登录访问 `/login` 不再有 `?add` 例外。
- `frontend-sidebar-hand-drawn`: 移除「Interaction behavior unchanged」要求（它把「账号切换菜单保持可用」写成契约），并以新要求「Sidebar interactions preserved without account switching」承接仍然成立的部分 —— 折叠、拖拽调宽、退出登录，且明确账号菜单不再存在。

## Impact

- 前端 `shared/`：`auth/token-storage.ts`（重写为单账号读写）、`composables/useAuthPool.ts`（删除）、`types/auth.ts`（移除 `AuthPool`）、`api-client.ts`（去 `getActive` 注入）、`api-auth-interceptors.ts`（去 `getActive` 依赖与备用账号分支）。
- 前端页面与模块：`views/LoginView.logic.ts`、`views/composables/useAuthFlow.ts`、`shared/components/AppSidebar.vue` 及其 `AppSidebar.style.css`、`modules/device-pool/composables/useDeviceActions.ts`、`router.ts`（移除 `?add` 例外）。
- 前端单测：删除 `frontend/tests/login/p0/useAuthPool.spec.ts`；改写 `apiAuthInterceptors.spec.ts`、`useAuthFlow.spec.ts` 与 `frontend/tests/device-pool/{p0,p1}/useDeviceActions.spec.ts`。
- 端到端：`tests/e2e/test_login_e2e.py` —— `E2E-009` 依赖 `/login?add=1` 停在登录页、`E2E-012` 直接断言 `localStorage.auth_accounts`，两条都必须改写。
- 文档：`PRD-00-登录模块.md`、`单元测试-登录.md`、`功能测试用例-登录.md`。
- 后端：**无接口变更** —— 会话仍按 `sid` 作废，`apps/accounts`、网关公开路径清单与接口契约均不动；因此不涉及跨 App 依赖与写库收敛。
