# auth-response-shape Delta

## MODIFIED Requirements

### Requirement: 前端认证 DTO 不声明后端不返回的字段

前端认证 DTO 中声明的每个字段 SHALL 出现在其对应端点的后端响应里。
同一 DTO 被多个端点复用时，MUST NOT 用一个宽泛的可选字段掩盖端点之间的形状差异。

该一致性 SHALL 由 `tests/arch/unit` 下的契约守护断言，MUST NOT 依赖运行中的服务。

#### Scenario: 登录与注册响应 DTO 的字段都在响应里

- **WHEN** 比较 `AuthTokenData` 声明的字段与 `/api/auth/login/`、`/api/auth/register/` 响应的 key 集合
- **THEN** 声明集合是响应 key 集合的子集

#### Scenario: 刷新响应 DTO 的字段都在响应里

- **WHEN** 比较 `AuthRefreshData` 声明的字段与 `/api/auth/refresh/` 响应的 key 集合
- **THEN** 声明集合是响应 key 集合的子集

#### Scenario: 身份接口 DTO 与响应一致

- **WHEN** 比较 `MeUser` 声明的字段与 `/api/auth/me/` 响应中 `user` 对象的 key 集合
- **THEN** 两者相同
