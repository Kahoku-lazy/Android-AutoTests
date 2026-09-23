# api-path-convention Specification

## Purpose

`/api/` 路由与它的全部调用方共用**一种**写法：路径以 `/` 结尾，缺失即 404。
本能力规定路由定义、网关重定向策略，以及端到端调用面（前端 API 层、测试用例）
与该约定的一致性要求，使"路径写错"表现为确定的 404，而不是被网关静默纠正成另一种写法。

## Requirements

### Requirement: API 路径统一带尾斜杠

`config/urls.py` 汇总的每个业务路由 SHALL 以 `/` 结尾。路由定义不得存在"同一资源同时注册带斜杠与不带斜杠两种写法"。

`settings.APPEND_SLASH` SHALL 为 `False`：网关不得通过 301 重定向纠正缺失的尾斜杠。

#### Scenario: 带尾斜杠命中

- **WHEN** 请求 `POST /api/auth/login/`
- **THEN** 命中视图

#### Scenario: 缺失尾斜杠返回 404

- **WHEN** 请求 `POST /api/auth/login`
- **THEN** 返回 404（不再被重定向或改写）

#### Scenario: 不存在 301 重定向

- **WHEN** 请求任何缺失尾斜杠的 `/api/` 路径
- **THEN** 响应状态码不是 3xx

#### Scenario: 路由表内不存在无斜杠路由

- **WHEN** 遍历 `get_resolver()` 的全部 `/api/` 路由
- **THEN** 每一条都以 `/` 结尾

### Requirement: 前端与测试调用面遵循唯一写法

全部调用方的 `/api/` 路径 SHALL 带尾斜杠，且 SHALL 能在 Django 路由表中解析命中：

- **前端 API 层**：`frontend/src` 中作为 HTTP 调用参数的路径字面量
- **测试调用面**：`tests/` 中的 HTTP 调用字面量，以及 `tests/api/case/*.yaml` 的 `path:` 字段

该一致性 SHALL 由 `tests/graybox/unit` 下的默认单元测试断言，MUST NOT 依赖运行中的服务，
MUST NOT 依赖需要显式开启的环境变量或凭据。

故意使用无尾斜杠的负向用例 SHALL 登记在守护测试的显式例外清单中并注明理由。

#### Scenario: 前端 API 层

- **WHEN** 检查前端 api 层的请求路径
- **THEN** 每条 `/api/` 路径均以 `/` 结尾

#### Scenario: 接口测试用例

- **WHEN** 检查 `tests/` 中的 HTTP 调用字面量与 `tests/api/case/*.yaml` 的 `path:` 字段
- **THEN** 每条 `/api/` 路径均以 `/` 结尾，且能命中后端路由
- **AND** 该检查由默认单元套件执行，不需要启动前后端服务

#### Scenario: 负向用例显式登记

- **WHEN** 某测试需要断言"缺失尾斜杠返回 404"
- **THEN** 该路径出现在守护测试的显式例外清单中，并注明理由

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

### Requirement: 调用面扫描的完整性与显式例外

守护 SHALL 逐条枚举被扫描面中的**每一个** HTTP 调用点，MUST NOT 因源码格式差异
（例如调用与路径字面量分处两行、或换行缩进不同）而漏扫。

扫描出的调用点数量明显低于登记规模时，守护 SHALL 失败并提示检查识别规则，
MUST NOT 在漏扫的情况下给出"全部一致"的结论。

#### Scenario: 跨行书写的调用被扫到

- **WHEN** 某个 HTTP 调用的路径字面量写在调用括号之后的下一行
- **THEN** 该调用点仍被纳入尾斜杠与 resolve 断言

#### Scenario: 识别规则失效不静默通过

- **WHEN** 扫描出的调用点数量低于登记下限
- **THEN** 守护失败并提示检查识别规则，而不是通过

#### Scenario: 例外清单之外的违规必须失败

- **WHEN** 任意被扫描面出现未登记的缺尾斜杠路径
- **THEN** 守护失败，并在错误信息中列出文件、行号与原文字面量
