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

### Requirement: 前端会话为单账号

前端 SHALL 在浏览器本地只保留**一个**账号的会话凭证：`access_token`、`refresh_token` 与 `username`。
前端 MUST NOT 维护账号列表，MUST NOT 维护逐标签页的「当前账号」选择，也 MUST NOT 提供在多个已存账号之间切换的能力。
当新账号认证成功时，系统 SHALL 用新账号的凭证**覆盖**原会话，而不是与其并行保留。

#### Scenario: 登录成功后本地只有一个账号

- **WHEN** 用户先以账号 A 登录成功，随后以账号 B 登录成功
- **THEN** 本地只保留账号 B 的 access / refresh / username
- **AND** 本地不存在账号 A 的任何残留凭证，也不存在账号列表结构

#### Scenario: 刷新页面后仍是同一账号

- **WHEN** 用户登录成功后在工作台任意页面刷新
- **THEN** 后续请求仍携带该账号的 access 令牌
- **AND** 侧栏呈现的当前账号名与该账号一致

### Requirement: 登出即清空本地会话并回登录页

用户登出时，系统 SHALL 清空本地保存的会话凭证并导航到 `/login`。
系统 MUST NOT 保留其他账号，也 MUST NOT 因「本地还有备用账号」而停留在工作台。

#### Scenario: 登出后回到登录页且本地无凭证

- **WHEN** 用户点击侧栏「退出」且登出接口返回成功
- **THEN** 浏览器跳转到 `/login`
- **AND** 本地不再有该账号的 access / refresh / username

#### Scenario: 登出接口不可用时保留登录态

- **WHEN** 登出接口返回 `503` 且响应体带 `retry`
- **THEN** 前端提示稍后重试
- **AND** 本地会话凭证被保留，用户仍处于登录态

### Requirement: 路由守卫对已登录用户一律跳转工作台

当本地存在访问令牌时，用户访问 `/login` SHALL 被重定向到 `/dashboard`。
系统 MUST NOT 为「添加账号」保留任何绕过该重定向的入口或查询参数例外。
当本地没有访问令牌时，用户访问 `/login` 以外的任意页面 SHALL 被重定向到 `/login`。

#### Scenario: 已登录访问登录页被送回工作台

- **WHEN** 已登录用户导航到 `/login`
- **THEN** 浏览器地址变为 `/dashboard`

#### Scenario: 携带旧的添加账号参数仍被送回工作台

- **WHEN** 已登录用户导航到 `/login?add=1`
- **THEN** 浏览器地址变为 `/dashboard`
- **AND** 系统不呈现任何「添加账号」语义的界面

#### Scenario: 未登录访问工作台被送回登录页

- **WHEN** 未登录用户导航到 `/dashboard`
- **THEN** 浏览器地址变为 `/login`

### Requirement: 续期失败无条件清空会话并跳转登录页

当请求指向需要令牌的端点、返回 `401`、且本地存在 refresh 令牌时，前端 SHALL 发起一次刷新并重试原请求。
若刷新请求失败，前端 SHALL 清空本地会话凭证并跳转 `/login`。
该跳转 MUST NOT 以「本地是否还有其他账号」为条件。

#### Scenario: 续期失败清空凭证并跳转登录页

- **WHEN** 受保护端点返回 `401` 且刷新请求失败
- **THEN** 本地会话凭证被清空
- **AND** 浏览器跳转到 `/login`
- **AND** 原请求不被重试

#### Scenario: 续期成功时不跳转

- **WHEN** 受保护端点返回 `401` 且刷新请求成功
- **THEN** 原请求携带新 access 被重试
- **AND** 浏览器不跳转到 `/login`

### Requirement: 设备页当前用户取自单账号会话

设备管理页用于判断「是否本人锁定」的当前用户 SHALL 取自本地单账号会话保存的 `username`。

#### Scenario: 当前用户即登录账号

- **WHEN** 用户以账号 A 登录后进入设备管理页
- **THEN** 设备卡片与操作区使用的当前用户为 A
