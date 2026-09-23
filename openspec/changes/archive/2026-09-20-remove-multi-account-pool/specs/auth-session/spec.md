## ADDED Requirements

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
