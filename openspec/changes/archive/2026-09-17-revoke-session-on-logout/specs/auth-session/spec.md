## ADDED Requirements

### Requirement: 登出作废整个会话

`POST /api/auth/logout` SHALL 作废本次登录签发的**全部**令牌（access 与 refresh），而不只是当前请求携带的 access。

一次登录签发的 access 与 refresh SHALL 共享同一个会话标识 `sid`；登出时服务端 SHALL 以 `sid` 为粒度记录吊销。
令牌校验 SHALL 同时检查 `jti` 与 `sid` 两级吊销。

#### Scenario: 登出后刷新令牌失效

- **WHEN** 用户登录取得 access/refresh，随后登出，再用同一 refresh 请求 `/api/auth/refresh`
- **THEN** 返回 401，且不签发新的 access

#### Scenario: 登出后原 access 失效

- **WHEN** 登出后用同一 access 请求受保护端点 `/api/auth/me`
- **THEN** 返回 401

#### Scenario: 续期保持会话归属

- **WHEN** 用 refresh 换取新 access（此时会话未被吊销）
- **THEN** 新 access 与原 refresh 共享同一 `sid`
- **AND** 该会话登出后，这张新 access 同样返回 401（不因续期而脱离会话管辖）

#### Scenario: 其他会话不受影响

- **WHEN** 同一账号在两处登录（两个不同的 `sid`），其中一处登出
- **THEN** 另一处的 access 与 refresh 仍然有效

#### Scenario: Redis 不可用时拒绝登出

- **WHEN** 吊销记录无法写入（Redis 不可用）
- **THEN** 登出返回 503 且响应体带 `retry`，而不是返回成功
- **AND** 调用方重试后仍可完成登出

#### Scenario: 缺少会话标识的旧令牌

- **WHEN** 请求携带的 access 没有 `sid`（本变更部署前签发）
- **THEN** 登出仍按其 `jti` 吊销该 access
- **AND** 校验端不得因 `sid` 缺失而报错
