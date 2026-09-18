## ADDED Requirements

### Requirement: /api 请求的尾斜杠双向容错

对以 `/api/` 开头的请求，网关 SHALL 在**原路径无法解析**时，尝试补/去尾斜杠，
并在其中一种形式可解析时把请求重写为该形式；两种形式都不可解析时 SHALL 保持 404。
非 `/api/` 前缀的请求 SHALL NOT 被改写。

改写 SHALL NOT 改变 API 契约：路由定义本身与 OpenAPI schema 中的路径不变。

#### Scenario: 带斜杠调用无斜杠路由

- **WHEN** 请求 `POST /api/auth/login/`，而该端点定义为 `login`
- **THEN** 命中视图并返回 400（空请求体），**不是 404**

#### Scenario: 无斜杠调用带斜杠路由

- **WHEN** 请求 `GET /api/dashboard/stats`，而该端点定义为 `stats/`
- **THEN** 命中视图并返回 200
- **AND** 不产生 301 重定向（避免客户端重定向时丢失 `Authorization` 头）

#### Scenario: 原路径可解析时不改写

- **WHEN** 请求路径本身即可解析（例如同一资源同时注册了 `x` 与 `x/`）
- **THEN** 不做任何改写，按原路径命中

#### Scenario: 两种形式都不存在时保持 404

- **WHEN** 补/去尾斜杠后仍无法解析
- **THEN** 返回 404，且不改写路径

#### Scenario: 非 /api 前缀不受影响

- **WHEN** 请求 `/admin/` 等非 `/api/` 前缀路径
- **THEN** 不做任何改写
