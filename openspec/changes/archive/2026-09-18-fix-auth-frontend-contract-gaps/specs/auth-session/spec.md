## ADDED Requirements

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
