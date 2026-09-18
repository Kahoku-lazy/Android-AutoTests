## Context

- JWT 是无状态的：签名有效 + 未过期即有效，服务端没有可删除的会话记录。本工程已用 Redis 黑名单
  （`jwt:blacklist:<jti>`）实现「提前作废」，`verify_token()` 每次校验都会查一次。
- 因此本工程**并非纯无状态** —— 状态已在热路径上，故「补全会话级吊销」的边际成本很低。
- 现状的缺口不是实现 bug，而是**作用域**：`LogoutView` 的 docstring 写的是「把当前 access 令牌写入黑名单」，
  它从未声称结束会话；而 refresh 只出现在 `/api/auth/refresh` 的请求体里，登出请求根本看不到它。
- `apps/accounts/AGENTS.md` 当前为 0 字节，本模块此前没有登记任何契约。

## Goals / Non-Goals

**Goals**：让「登出 = 退出本次登录」成为服务端事实：登出后本次登录签发的任何令牌都不可用，且不依赖客户端交回 refresh。

**Non-Goals**：不做用户级「登出所有设备」；不做 refresh 轮换；不改前端；不改 API 形状。

## Decisions

**D1：用服务端签发的 `sid`，而不是让客户端把 refresh 交回来。**

| 方案 | 结论 | 理由 |
|---|---|---|
| 登出请求体带 `refresh_token`，两个 `jti` 都拉黑 | ❌ | 依赖客户端**保存并交回** refresh；客户端丢了就撤不掉，撤销范围由客户端决定 |
| 签发时写入 `sid`，登出吊销 `sid`（**采用**） | ✅ | 撤销范围由**服务端签发时**决定，客户端零配合；将来新增同会话令牌自动纳入管辖 |

**D2：吊销记录 TTL = `JWT_REFRESH_TTL`。**

登出请求只携带 access（`exp` = 1h），但同一会话的 refresh 还有至多 `refresh_ttl`（7d）的寿命。
若按 access 的剩余寿命设 TTL，吊销记录会先于 refresh 过期 → refresh 恢复可用。故取 `refresh_ttl`。

**D3：`sid` 与 `jti` 共用一次 Redis 往返。**

`EXISTS key1 key2` 一次返回存在的键数。校验热路径的往返次数与改动前一致（DRF 请求仍是每次校验一次查询，
中间件 + DRF 认证类共两次），因此本变更不给热路径增加开销。

**D4：保留 `jti` 吊销作为兜底。**

部署前签发的 access 没有 `sid`，只能按 `jti` 撤销；登出对两者都写，行为向后兼容。

**D5：接口形状不变。**

`create_token_pair()` 的返回键集不变，`sid` 只存在于令牌内部。前端无需改动，也不需要新字段。

**D6：顺带修掉 `setex` 废弃用法。**

`_blacklist_add` 在本变更中被重构为通用吊销写入，其中 `client.setex(...)` 是 redis-py 已废弃接口
（实测有 `DeprecationWarning`），改为 `client.set(key, "1", ex=ttl)`。

## Risks / Trade-offs

- [过渡期窗口] 部署前签发的 **refresh** 没有 `sid`，无法被 `sid` 吊销；窗口 ≤ `JWT_REFRESH_TTL`（7d）。
  缓解：其配套 access 仍可按 `jti` 撤销；文档登记，不为此引入令牌版本号。
- [Redis 键量增加] 每次登出多一条 `jwt:session_revoked:<sid>`，TTL 7d。键极小且有 TTL 上限，可接受。
- [登出写两次 Redis] `sid` 与 `jti` 各写一次；登出是低频操作，不优化。
- [Redis 不可用] 保持既有 fail-closed 语义：登出返回 503 + `retry`，不假装成功。

## Migration Plan

无需迁移。部署后新签发的令牌自动带 `sid`；旧 access 在 1h 内自然过期（期间仍可按 `jti` 撤销）。
回滚 = 还原 `jwt_auth.py` 与 `views.py`；已写入的 `jwt:session_revoked:*` 键会自行过期，无残留影响。

## Open Questions

1. 是否需要独立的「登出所有设备」（用户级 `token_version`）？语义更重，建议单独变更。
2. 是否把 refresh 轮换（每次续期换发新 refresh）一并做掉？本次不做，保持变更聚焦。
