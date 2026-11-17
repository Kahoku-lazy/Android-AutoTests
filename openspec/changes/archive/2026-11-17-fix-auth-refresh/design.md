## Context

动机见 `proposal.md - Why`。方案需要的现状事实：

- access TTL 1 小时、refresh TTL 7 天（`backend/shared/auth/jwt_auth.py`：`access_ttl = 3600`）。
- HTTP 侧已有 401 → 续期 → 重试（`frontend/src/shared/api-auth-interceptors.ts`，带并发锁）。
- WebSocket 侧：前端 `new WebSocket(url?token=...)`，不经过 axios；服务端在 `connect()` 里校验一次，失败即 `accept()` → 发 `{"type":"error"}` → `close(4401)`（`backend/apps/knowledge_assistant/consumer.py:121-131`）。
- 前端 `useAssistantSession.start()` 只读一次 `getToken()`；`onclose` 一律 `fail(KB_SOCKET_ERROR)`；`onmessage` 收到 `error` 立即 `fail()`。
- 该页面除首次进入的 `status` 外不发任何 HTTP；`onActivated` 还要 `!status.value` 才重拉。

约束：后端鉴权语义（4401、不建模型会话、不写日志）不改；不改令牌 TTL；不引入浏览器端解析/验签以外的密码学动作。

## Goals / Non-Goals

**Goals:**

- 凭证过期不再让知识库助手变成死循环：建连前续期，4401 自动重连一次。
- 续期只有**一个**单飞入口，HTTP 与 WS 并发续期不产生两次刷新请求。
- 同一类错误前后端一句话，不再让用户去「重新登录」。

**Non-Goals:**

- 不改 access / refresh 的 TTL（治标但要动安全参数，另案）。
- 不做「每个请求前预续期」：会改变 `authRequestInterceptor` 的同步签名，且刷新挂起时会把所有业务请求一起卡住；本轮不做，记入 Risks。
- 不改 4401 的状态码与「不创建会话、不写日志」的行为。
- 不为文字模式新增独立通道（仍复用同一条 WS）。

## Decisions

**1. 续期抽成 `shared/auth/token-refresh.ts`，HTTP 与 WS 共用。**

`refreshAccessToken()` 内部持有单飞 Promise：并发调用只发一次 `POST /api/auth/refresh/`，成功后 `setToken()`。`ensureFreshToken(minTtl=60)` 先读 `exp`（JWT 只解码不验签），已过期或即将过期才续期；没有 refresh 凭证时直接返回当前凭证，让下游的 401/4401 走各自的失败路径。

备选：在拦截器里加第二份刷新逻辑 → 否，会出现两把锁、并发时两次刷新；把拦截器整体搬进新模块 → 否，拦截器靠依赖注入做单测，搬家会破坏既有测试与可测性。折中：拦截器保持依赖注入，只把 `api-client.ts` 的 `refreshRequest` 换成 `refreshAccessToken()`，从而共用同一把单飞锁。

**2. 建连前 `await ensureFreshToken()`，不带着已知过期凭证建 WS。**

这是主修复：绝大多数失败发生在「凭证已过期」，此时先续期再建连即可。`start()` 已经是 async，改动成本一行。凭证为空（未登录）仍走既有 `KB_UNAUTHORIZED_ERROR`。

**3. 4401 自动重连一次，用 `authRetried` 防循环。**

`onclose` 收到 4401 且本次会话未重试过 → `refreshAccessToken()` → 用新凭证重连；重连再 4401 或续期失败 → `fail(KB_UNAUTHORIZED_ERROR)`。`authRetried` 在 `start()` 里重置，保证「一次会话最多补偿一次」，不会形成重连风暴。

**4. 建连阶段的错误帧延后到 close 决定。**

服务端先发 `error` 帧再 `close(4401)`；如果 `onmessage` 立刻 `fail()`，状态变 `error`，`onclose` 的重连分支就永远进不去。改为：`state === "connecting"` 时把消息记进 `pendingError` 不落错误态，由 `onclose` 决定「重连」还是「用这条消息失败」；已 `ready` 之后的错误（模型/会话中途）仍立即呈现，行为不变。

**5. 文案统一为「登录状态已过期，请刷新页面后重试」。**

前后端同一句。服务端这条消息只是兜底（正常情况下前端已重连成功），去掉误导性的「请重新登录」——用户不需要重新登录，refresh 还有 7 天。

**6. 不做每请求预续期。**

`authRequestInterceptor` 现在是同步函数，改成 async 会让所有请求多一次 await，且续期挂起时（axios 120 秒超时）会把整个应用卡住。已知代价：凭证过期后的第一个 HTTP 请求仍会先吃一次 401 再自动重试（浏览器控制台会留一条红字）。这是观感问题、不是功能问题，记入 Risks，需要时另案。

## 模块防火墙自检

- 跨 App import：无。后端只改 `knowledge_assistant` 的一句文案。
- `INSERT/UPDATE/DELETE`：无。
- 前端不直连数据库：遵守，续期仍打既有 `POST /api/auth/refresh/`。
- 通道：不新增 HTTP 端点、不新增 WebSocket；续期复用既有认证端点。
- 模块边界：`token-refresh` 放 `shared/auth/`（已被 HTTP 与知识库助手两个消费方共用），不在 `knowledge-assistant` 内自建第二套。

## Risks / Trade-offs

- **每请求预续期未做，HTTP 侧仍偶发一条 401 红字** → 功能自愈（续期后重试成功），只是观感；需要彻底消除时另开变更改请求拦截器。
- **`ensureFreshToken` 在续期失败时会让「开始对话」多等一次网络往返** → 仅在建连时发生，且失败后立刻给可读提示，可接受。
- **JWT `exp` 解码依赖令牌格式** → 只解码不验签，解析失败时按「无法判断」返回当前凭证，交给 401/4401 兜底，不会误判为已过期。
- **重连一次仍失败时会话终止** → 符合预期；用户看到的提示与手动「开始对话」一致，重新点一次会重新走 `ensureFreshToken()`。
- **并发续期（HTTP 401 与 WS 4401 同时触发）** → 单飞锁保证只发一次刷新；两次拿到的都是同一个新凭证。

## Migration Plan

纯前端 + 一句后端文案，无数据迁移、无接口变更、无部署顺序要求。上线后硬刷新生效；回滚为单次 `git revert`。
