## 1. 底层会话存储与拦截器

- [x] 1.1 重写 `frontend/src/shared/auth/token-storage.ts` 为单账号：以 `localStorage.access_token` / `refresh_token` / `username` 为唯一存储，导出 `getToken` / `setToken` / `clearToken` / `getRefreshToken` / `getUsername` / `saveSession` / `clearSession`，`saveSession` 写入后 `removeItem('auth_accounts')`；删除账号池读写与 `sessionStorage.auth_active`。验证：`cd frontend && npx vitest run tests/login/p0/token-storage.spec.ts` 全绿。
- [x] 1.2 新增 `frontend/tests/login/p0/token-storage.spec.ts`（4 条：三项写读回、二次写入覆盖不追加、`clearSession` 清空三项、写入清掉残留 `auth_accounts`），用例前清空 `localStorage`。验证：`npx vitest run tests/login/p0/token-storage.spec.ts` 显示 4 passed。
- [x] 1.3 改 `frontend/src/shared/api-auth-interceptors.ts`：从 `AuthInterceptorDeps` 删除 `getActive`，续期失败分支改为无条件 `deps.clearToken()` + `deps.redirectToLogin()`。验证：`npx vitest run tests/login/p0/apiAuthInterceptors.spec.ts` 全绿。
- [x] 1.4 改 `frontend/src/shared/api-client.ts`：去掉 `getActive` 的 import 与注入。验证：`cd frontend && npm run typecheck` 通过。

## 2. 上层调用点收敛

- [x] 2.1 改 `frontend/src/views/composables/useAuthFlow.ts`：`UseAuthFlowParams` 去掉 `auth`，改为直接调用 `saveSession(name, access_token, refresh_token)`，并改 `UseAuthPoolReturn` 的类型依赖。验证：`npx vitest run tests/login/p0/useAuthFlow.spec.ts` 全绿。
- [x] 2.2 改 `frontend/src/views/LoginView.logic.ts`：删除 `useAuthPool()` 与向 `useAuthFlow` 传 `auth`。验证：`npx vitest run tests/login/p1/LoginView.logic.spec.ts` 全绿。
- [x] 2.3 改 `frontend/src/modules/device-pool/composables/useDeviceActions.ts`：`getActive()` 改 `getUsername()`。验证：`npx vitest run tests/device-pool` 全绿。
- [x] 2.4 删除 `frontend/src/shared/composables/useAuthPool.ts`，并从 `frontend/src/shared/types/auth.ts` 删除 `AuthPool` / `AccountTokens`。验证：`grep -rn "useAuthPool\|AuthPool" frontend/src` 无命中，且 `npm run typecheck` 通过。
- [x] 2.5 改 `frontend/src/router.ts`：守卫改为「有令牌且 `to.path === '/login'` → `/dashboard`」，移除 `!to.query.add` 例外。验证：`npm run typecheck` 通过，`grep -n "query.add" frontend/src` 无命中。

## 3. 侧栏账号区改造

- [x] 3.1 改 `frontend/src/shared/components/AppSidebar.vue`：删除账号下拉面板、`showAccountMenu`、`switchToAccount`、`finishLocalLogout` 的重载分支与「添加账号」`router-link`；账号名改由 `getUsername()` 提供；`logout()` 保留 `logoutApi()` 的 503+`retry` 提示分支，其余情况 `clearSession()` 后 `router.push('/login')`；保留 `data-testid="sidebar-active-account"` 与 `data-testid="sidebar-logout"`。验证：`npm run build:check` 通过。
- [x] 3.2 改 `frontend/src/shared/components/AppSidebar.style.css`：删除 `.account-menu` / `.account-menu__item` / `__item:hover` / `.active` / `__check` / `--add` / `__divider` 样式块。验证：`npm run lint:styles` 通过，且 `grep -n "account-menu" frontend/src/shared/components/AppSidebar.style.css` 无命中。

## 4. 前端单测同步

- [x] 4.1 删除 `frontend/tests/login/p0/useAuthPool.spec.ts`。验证：`npx vitest run tests/login` 无该文件用例，且无 import 报错。
- [x] 4.2 改 `frontend/tests/login/p0/apiAuthInterceptors.spec.ts`：去掉 `getActive` 桩与注入，把原「无剩余账号 / 仍有剩余账号」两条用例合并为一条「续期失败：清凭证并跳转 `/login`」。验证：`npx vitest run tests/login/p0/apiAuthInterceptors.spec.ts` 全绿。
- [x] 4.3 改 `frontend/tests/login/p0/useAuthFlow.spec.ts`：`makeAuth()` 桩替换为 `saveSession` 断言，登录/注册成功用例改断言会话写入。验证：`npx vitest run tests/login/p0/useAuthFlow.spec.ts` 全绿。
- [x] 4.4 改 `frontend/tests/device-pool/p0/useDeviceActions.spec.ts` 与 `frontend/tests/device-pool/p1/useDeviceActions.spec.ts`：mock 从 `getActive` 改为 `getUsername`，顺带移除本就不存在的 `getActiveUsername` 桩。验证：`npx vitest run tests/device-pool` 全绿。
- [x] 4.5 全量前端回归：`cd frontend && npm run test` —— 实测 46 files / 262 tests，登录模块 11 文件 / 57 用例全绿；62 条失败经 `git show HEAD:` 核实**全部为 HEAD 既有失败**（device-pool 与 element-locator 的 `api.spec.ts` 尾斜杠口径、dashboard DTO 漂移、p1 分页来自工作区既有未提交改动），本变更范围内新增失败 0。

## 5. 端到端用例同步

- [x] 5.1 改 `tests/e2e/test_login_e2e.py` 的 `E2E-009`（`test_e2e_009_remember_username_round_trip`）：去掉对 `/login?add=1` 免守卫的依赖，改为「登出后重新打开 `/login`」验证预填与取消勾选清空。验证：`python -m pytest tests/e2e -q -k e2e_009` 通过（需前后端在跑）。
- [x] 5.2 改同文件的 `E2E-012`（`test_e2e_012_logout_returns_to_login`）：断言改为单账号键（`access_token` / `refresh_token` / `username`）已清空且不再存在 `auth_accounts`。验证：`python -m pytest tests/e2e -q -k e2e_012` 通过。
- [x] 5.3 跑端到端全量回归：`python -m pytest tests/e2e -q`，确认 `E2E-013` / `E2E-014`（守卫两条）仍绿。

## 6. 文档与规格同步

- [x] 6.1 改 `dev_docs/ARCH_PRD/PRD-00-登录模块.md`：更新「登出」与「会话与账号管理」两节的 §UI交互 / §业务逻辑 / §数据表单（去掉账号池、切换、`?add` 例外、跨标签页同步，补记单账号与升级后需重登），更新 §测试 中 TC-SESSION-003~006 的期望与覆盖清单里的 `useAuthPool.spec.ts`。验证：`grep -n "账号池\|多账号\|添加账号" dev_docs/ARCH_PRD/PRD-00-登录模块.md` 仅剩明确标注为「已移除」的记述。
- [x] 6.2 改 `dev_docs/DEV_TEST/单元测试文档/单元测试-登录.md`：把第六节「账号池状态层」替换为「单账号会话存储层（`token-storage.spec.ts`）」，更新 TC-FE-LOGIN-005/006 的断言口径，并据 4.5 的实测结果更新文首「N 个 spec / M 个用例」。验证：文档登记的 spec 数与 `npx vitest run tests/login` 输出一致。
- [x] 6.3 改 `dev_docs/DEV_TEST/功能测试用例/功能测试用例-登录.md`：移除「多账号 / 账号切换 / 账号池」相关业务条目或标注其已随本次变更作废。验证：文档中不再有仍被 `tests/e2e` 声称覆盖的多账号条目。
- [x] 6.4 文档一致性门禁：`python tools/gen_arch_stats.py --check-md` 输出无新增 drift。

## 7. 收口验证

- [x] 7.1 架构红线回归：`python tools/gen_arch_stats.py --check-boundaries` 无新增违规。
- [x] 7.2 全仓残留扫描：`grep -rn "useAuthPool\|auth_accounts\|auth_active\|switchAccount\|logoutAccount\|loginAccount\|accountList" frontend/src frontend/tests tests/e2e` 仅剩 6.1/6.2/6.3 中明确记述「已移除」的文档行与 `auth_accounts` 清理代码。
- [x] 7.3 前端门禁：`npm run lint`（0 error）· `npm run lint:styles` · `npx vite build` 通过；`npm run typecheck` 的 30 个错误经过滤后**落在本变更范围内的为 0**（全部在 `case-manager/ProjectTree.vue` 与 dashboard spec，属 HEAD 既有）。
- [x] 7.4 `openspec validate remove-multi-account-pool --strict` 通过。