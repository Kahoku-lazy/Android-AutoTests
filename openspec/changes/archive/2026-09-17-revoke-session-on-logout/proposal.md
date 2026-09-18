## Why

`POST /api/auth/logout` 的语义是「退出当前账号」，但它实际只作废了当前请求携带的 **access** 令牌：
`LogoutView` 从 `Authorization` 头取令牌并按其 `jti` 拉黑，而 **refresh 从未出现在请求头里**，
因此它的 `jti` 从未被吊销。实测（`temps/login-backend-map` 采集器）：

```
[1] 登录                              -> 200
[2] 登出                              -> 200
[3] 登出后用同一 access 再请求         -> 401   （黑名单生效）
[4] 登出后用同一 refresh 换新 access   -> 200   ← 会话并未结束
```

后果有二：
1. **语义缺口**：端点叫 `logout`，实现的是 `revoke_access`；系统里没有任何东西实现 `end_session`。
   用户以为退出了，服务端仍认这张 refresh（剩余最长 7 天）。
2. **可复活会话**：登出流程是「先调 `/auth/logout`、再清本地令牌」。在这两步之间的窗口内，
   任何在途请求若先收到 401，前端拦截器会用仍在本地池里的 refresh 自动续期成功 ——
   **已登出的会话被静默复活**。

## What Changes

- **会话粒度**：一次登录签发的 access 与 refresh 共享同一 `sid`（uuid4，签发时生成，写进两个令牌）
- **校验**：`verify_token()` 在原有 `jti` 吊销检查之外，同时检查 `sid` 吊销
- **登出**：`LogoutView` 以 `sid` 为粒度吊销 → 同一会话的 **access 与 refresh 一起失效**
  （同时保留按 `jti` 吊销，覆盖部署前签发、没有 `sid` 的旧令牌）
- **续期**：`RefreshView` 换发新 access 时**透传同一 `sid`** —— 否则续期后新 access 会脱离会话管辖
- **接口形状不变**：`create_token_pair()` 返回键集不变（仍 `access_token`/`refresh_token`/`token_type`），
  `sid` 只存在于令牌内部，因此**前端零改动**
- **吊销记录 TTL**：默认取 `JWT_REFRESH_TTL`（登出只看得到 access 的 1h，但同会话 refresh 还有至多 7d 寿命，
  吊销记录必须覆盖它）
- **合并 Redis 往返**：`jti` 与 `sid` 两级检查用一次 `EXISTS key1 key2` 完成，热路径往返次数不变
- 顺带修掉 `_blacklist_add` 里的 `redis.setex` 废弃告警（该函数在本变更中被重构为通用吊销写入）

**Non-goals**：
- 不做「登出所有设备」（用户级令牌版本号）—— 那是独立功能，不混进普通登出
- 不改前端：`sid` 对客户端不可见，登出请求体仍为空
- 不引入 refresh token 轮换（`RefreshView` 仍只换 access）
- 不为「部署前签发的 refresh」补历史吊销能力（见 `design.md` 的过渡期说明）

## Capabilities

### New Capabilities

- `auth-session`：登录会话的建立、续期与登出吊销契约（会话级吊销、续期保持会话归属、Redis 不可用时拒绝登出）

### Modified Capabilities

（无）

## Impact

- 后端：`shared/auth/jwt_auth.py`（签发 / 校验 / 吊销）、`apps/accounts/views.py`（`LogoutView`、`RefreshView`）
- 前端：**无**
- API 契约：路径、请求体、响应体形状均不变；**行为**变化仅在于「登出后 refresh 不再可用」
- 测试：新增 `tests/graybox/unit/test_logout_session_revocation.py`
- 证据产物：`temps/login-backend-map/` 需重跑（其 F 节结论会从「断点」变为「已闭合」）
