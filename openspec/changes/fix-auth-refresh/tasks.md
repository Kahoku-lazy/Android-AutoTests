## 1. 共享续期入口

- [x] 1.1 新增 `frontend/src/shared/auth/token-refresh.ts`：`tokenExpiresAt(token)`（只解码 JWT `exp`，不验签，解析失败返回 null）、`isTokenExpired(token, skewSeconds = 60)`、`refreshAccessToken()`（单飞：并发只发一次刷新，成功后 `setToken`，失败抛出且不自行清会话）、`ensureFreshToken(minTtlSeconds = 60)`（无凭证或无 refresh 凭证时返回当前值，不下发请求）。续期传输层由 `api-client` 通过 `configureTokenRefresh()` 注入，避免 `shared/auth` 直接依赖 axios（HTTP 唯一出口约束）。验证结果：`tests/login/p0/tokenRefresh.spec.ts` 7 条全绿。
- [x] 1.2 新增 `frontend/tests/login/p0/tokenRefresh.spec.ts`：覆盖「未过期不续期」「已过期续期并写回」「并发只发一次」「无续期凭证不发请求」「解析不出按原凭证返回」「临近过期提前续期」「响应缺凭证时抛出且不写回」七条。验证结果：全绿。
- [x] 1.3 `frontend/src/shared/api-client.ts`：注入 `configureTokenRefresh`（真实 `POST /api/auth/refresh/`），并把拦截器的 `refreshRequest` 改为 `refreshAccessToken()`，HTTP 401 与 WS 4401 共用同一把单飞锁。验证结果：`tests/login` 66 条中 64 通过，失败 2 条为既有 `LoginView.hero.spec.ts`（工作区登录页文案改动）。

## 2. 知识库助手：建连前续期

- [x] 2.1 `useAssistantSession.start()`：`getToken()` 换成 `await ensureFreshToken()`（续期抛错按无凭证处理），凭证为空仍 `fail(KB_UNAUTHORIZED_ERROR)`；麦克风与播放器仍在内层、仅凭证有效后才申请。验证结果：`ws-auth-retry.spec.ts` 的「建连前先续期，用续期后的凭证连接」「没有可用凭证时不建连并提示过期」全绿。
- [x] 2.2 新增 `authRetried` 标记（`start()` 重置），保证一次会话最多为 4401 补偿一次。验证结果：同 spec 的「重连仍被拒时提示过期，且不再循环」全绿。

## 3. 4401 自动重连一次

- [x] 3.1 `useAssistantSession`：建连阶段（`state === "connecting"`）的 `error` 帧只记入 `pendingError`，`onclose` 收到 4401 且未补偿过时 `refreshAccessToken()` 并用新凭证重连；重连再 4401 或续期失败才落错误态；非 4401 的关闭仍按 `pendingError || KB_SOCKET_ERROR` 失败（`onerror` 触发的 1006 走同一分支）。验证结果：单测覆盖两条主路径。
- [x] 3.2 新增 `frontend/tests/knowledge-assistant/p0/ws-auth-retry.spec.ts`：用假 `WebSocket` 覆盖上述两条（文字方式，避免音频依赖）。验证结果：4 条全绿。

## 4. 文案统一

- [x] 4.1 `KB_UNAUTHORIZED_ERROR` 与 `consumer.py` 的 WS 错误文案统一为「登录状态已过期，请刷新页面后重试」。验证结果：`grep "请重新登录"` 在 `frontend/src` 与 `backend/apps/knowledge_assistant` 已无命中（`shared/types/api-error.ts` 的通用 HTTP 401 文案不在本单范围：那里「重新登录」确实是正确动作）；`python -m pytest -c tests/pytest.ini tests/graybox/integration/test_knowledge_assistant_ws.py -q` 通过（该用例只断言包含「登录」）。

## 5. 门禁

- [x] 5.1 `npx vitest run tests/login tests/knowledge-assistant` + `npm run typecheck` + `npm run build:check`。验证结果：89 条中 87 通过（失败 2 条为既有登录页 spec）；`vue-tsc --noEmit` 无输出；构建通过。
- [x] 5.2 `python run.py check`：验证结果 **22/23**，唯一失败为 `vitest`（即上面的 `LoginView.hero.spec.ts`）；`eslint` 一度因 `shared/auth` 直接 import axios 失败，已改为注入传输层后通过。全量 vitest 487/489。
- [ ] 5.3 人工验证：凭证过期后点「开始对话」自动续期并连上、控制台无 4401 红字；删掉 refresh 凭证后再点应提示「登录状态已过期」且不循环。**（待用户执行；需页面挂满 1 小时或手动改 localStorage 里的 access 触发）**
