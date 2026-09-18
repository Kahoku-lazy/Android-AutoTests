## MODIFIED Requirements

### Requirement: 端到端调用方遵循唯一写法

全部调用方的 `/api/` 路径 SHALL 带尾斜杠，且 SHALL 能在 Django 路由表中解析命中：

- **前端 API 层**：`frontend/src` 中作为 HTTP 调用参数的路径字面量
- **测试调用面**：`tests/` 中的 HTTP 调用字面量，以及 `tests/api/case/*.yaml` 的 `path:` 字段
- **端点资产目录**：`tools/seed_api_endpoints.py` 中的端点路径

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

#### Scenario: 端点资产目录

- **WHEN** 检查 `tools/seed_api_endpoints.py` 中的端点路径
- **THEN** 每条都带尾斜杠，且能命中后端路由
- **AND** 该面与其余三个面由同一个默认单元测试守护

#### Scenario: 负向用例显式登记

- **WHEN** 某测试需要断言"缺失尾斜杠返回 404"
- **THEN** 该路径出现在守护测试的显式例外清单中，并注明理由
