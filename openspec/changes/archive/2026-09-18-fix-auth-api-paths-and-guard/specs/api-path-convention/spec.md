## ADDED Requirements

### Requirement: 前端调用面与路由表的一致性由默认测试守护

前端代码中作为 HTTP 调用参数出现的 `/` 开头路径字面量 SHALL 以 `/` 结尾；该字面量拼上
`api-client` 的 `baseURL`（`/api`）后 SHALL 能在 Django 路由表中解析命中。
仅指向前端自身路由的字面量（如 `/login`）不在本约束内。

该一致性 SHALL 由 `tests/graybox/unit` 下的默认单元测试断言，MUST NOT 依赖运行中的前端或后端服务，
MUST NOT 依赖需要显式开启的环境变量或凭据。

#### Scenario: 前端路径字面量全部带尾斜杠

- **WHEN** 扫描 `frontend/src` 中作为 `.get`/`.post`/`.put`/`.patch`/`.delete(` 或 `fetch(` 首个参数出现的 `/` 开头字面量
- **THEN** 每一条都以 `/` 结尾（前端自身路由除外）

#### Scenario: 每条字面量都能命中后端路由

- **WHEN** 把每条字面量拼上 `baseURL=/api` 后调用 `django.urls.resolve()`
- **THEN** 每条都命中视图，不出现 `Resolver404`

#### Scenario: 认证链路五个调用全部命中

- **WHEN** 检查认证调用面 `frontend/src/shared/api/auth.ts` 与 `frontend/src/shared/api-client.ts`
- **THEN** `login` / `register` / `logout` / `me` / `refresh` 五个调用全部带尾斜杠
- **AND** 分别命中 `LoginView` / `RegisterView` / `LogoutView` / `MeView` / `RefreshView`

#### Scenario: 前端自身路由不参与断言

- **WHEN** 扫描到 `/login`、`/dashboard` 这类前端自身路由字面量
- **THEN** 不纳入尾斜杠与 resolve 断言

#### Scenario: 守护测试不依赖运行中的服务

- **WHEN** 在未启动前端与后端、且未设置任何测试环境变量的环境中运行默认单元测试
- **THEN** 该守护测试执行并通过，而不是被 skip
