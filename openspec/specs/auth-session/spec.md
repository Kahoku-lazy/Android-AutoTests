# auth-session Specification

## Purpose
TBD - created by archiving change revoke-session-on-logout. Update Purpose after archive.

## Requirements

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

### Requirement: 认证端点显式声明鉴权姿态

`apps/accounts` 的每个 APIView SHALL 满足：`permission_classes` 含 `AllowAny`
**当且仅当** `authentication_classes` 为空列表。公开端点因此必须同时声明「允许任何人」与「不做 DRF 鉴权」；
需要身份的端点 MUST NOT 出现二者只成立其一的状态。

该不变量 SHALL 由测试断言，以防止公开端点误继承鉴权类、或受保护端点被误开放。

#### Scenario: 公开端点两者成对

- **WHEN** 检查 `login` / `register` / `refresh` 三个端点
- **THEN** `permission_classes` 为 `AllowAny`
- **AND** `authentication_classes` 为空列表

#### Scenario: 受保护端点两者成对

- **WHEN** 检查 `logout` / `me` 两个端点
- **THEN** `permission_classes` 不含 `AllowAny`
- **AND** `authentication_classes` 非空（沿用 `REST_FRAMEWORK` 默认的 `shared.auth.drf_auth.JWTAuthentication`）

#### Scenario: 覆盖认证模块全部端点

- **WHEN** 遍历 `apps/accounts` 中的全部 APIView
- **THEN** 每个都满足上述不变量，没有一个落在「仅 AllowAny」或「仅空鉴权类」的中间态

### Requirement: 公开认证端点的 401 不触发令牌刷新

前端全局 401 处理 SHALL 区分端点：公开认证端点（登录 / 注册 / 刷新）返回的 401 表示凭证或令牌本身无效，
MUST NOT 触发令牌刷新，也 MUST NOT 因刷新失败而清除本地令牌。

需要令牌的端点返回的 401 仍 SHALL 触发一次刷新并重试原请求（保持既有行为）。

公开端点清单 SHALL 与网关公开路径清单中的 `/api/auth/*` 部分保持一致，
且该一致性 SHALL 由 `tests/graybox/unit` 下的默认单元测试断言。

#### Scenario: 登录返回 401 时不刷新

- **WHEN** `POST /api/auth/login/` 返回 401（凭证错误）
- **THEN** 不发起 `POST /api/auth/refresh/`，直接拒绝该请求

#### Scenario: 需要令牌的端点 401 仍会刷新

- **WHEN** 受保护端点返回 401（access 过期）
- **THEN** 发起一次刷新并重试原请求，行为与变更前一致

#### Scenario: 刷新请求自身不被再次刷新

- **WHEN** `POST /api/auth/refresh/` 返回 401
- **THEN** 不再次发起刷新（不递归）

#### Scenario: 公开端点清单与网关一致

- **WHEN** 比较拦截器声明的公开端点清单与网关公开路径清单中的 `/api/auth/*` 部分
- **THEN** 两者相同
