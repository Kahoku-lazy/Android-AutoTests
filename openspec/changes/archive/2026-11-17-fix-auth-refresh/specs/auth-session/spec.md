## ADDED Requirements

### Requirement: 访问凭证在过期前主动续期

前端 SHALL 在访问凭证已过期或将在 60 秒内过期时先续期再使用，MUST NOT 带着已知过期的访问凭证发起请求或建立 WebSocket。续期 MUST 经同一「单飞」入口：同一时刻的多次续期 MUST 只产生一次 `POST /api/auth/refresh/`。续期成功 SHALL 写回新的访问凭证；续期失败 SHALL 交由调用方处理（HTTP 走既有清会话并跳转登录页，WebSocket 走可读提示），MUST NOT 在没有续期凭证时反复重试。

#### Scenario: 建连前凭证已过期

- **WHEN** 本地访问凭证已过期，用户点击「开始对话」
- **THEN** 前端先发起一次 `POST /api/auth/refresh/`，拿到新凭证后再建立 WebSocket 连接
- **AND** 用户不需要重新登录

#### Scenario: 并发续期只发一次刷新请求

- **WHEN** 一次 HTTP 401 与一次 WebSocket 4401 同时触发续期
- **THEN** 只产生一次 `POST /api/auth/refresh/`
- **AND** 两条调用路径拿到同一个新访问凭证

#### Scenario: 没有续期凭证时不重试

- **WHEN** 本地只有访问凭证、没有续期凭证，且访问凭证已过期
- **THEN** 不发起续期请求
- **AND** 由下游的 401 / 4401 走各自的失败路径
