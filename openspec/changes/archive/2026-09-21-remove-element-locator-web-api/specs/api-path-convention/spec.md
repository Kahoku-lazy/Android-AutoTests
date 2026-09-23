## ADDED Requirements

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

## REMOVED Requirements

### Requirement: 端到端调用方遵循唯一写法

**Reason**: 该需求的调用面枚举第三项为「端点资产目录」（`tools/seed_api_endpoints.py`）。该载体随 Web/API 域下线退役，其对应场景不再可能成立；MODIFIED 语义不允许丢弃既有场景，故以「移除 + 新增收窄后的需求」表达。

**Migration**: 由新增需求「前端与测试调用面遵循唯一写法」承接，约束范围收窄为前端 API 层与测试调用面两面；守护侧由四面收敛为三面（`frontend` / `tests` / `yaml`），原 `catalog` 面及其规模下限一并移除。
