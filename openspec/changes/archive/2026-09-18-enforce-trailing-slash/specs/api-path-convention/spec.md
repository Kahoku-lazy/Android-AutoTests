## ADDED Requirements

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

### Requirement: 端到端调用方遵循唯一写法

前端与测试用例中的 `/api/` 路径 SHALL 带尾斜杠；端点资产目录（`tools/seed_api_endpoints.py`）中的路径 SHALL 与实际路由一致。

#### Scenario: 前端 API 层

- **WHEN** 检查前端 api 层的请求路径
- **THEN** 每条 `/api/` 路径均以 `/` 结尾

#### Scenario: 接口测试用例

- **WHEN** 运行 `tests/api` 的接口用例
- **THEN** 全部通过（路径与路由一致）
