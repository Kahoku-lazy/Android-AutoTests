## MODIFIED Requirements

### Requirement: 端到端调用方遵循唯一写法

全部调用方的 `/api/` 路径 SHALL 带尾斜杠，且 SHALL 能在 Django 路由表中解析命中：

- **前端 API 层**：`frontend/src` 中作为 HTTP 调用参数的路径字面量
- **测试调用面**：`tests/` 中的 HTTP 调用字面量，以及 `tests/api/case/*.yaml` 的 `path:` 字段
- **端点资产目录**：`tools/seed_api_endpoints.py` 中的路径
  （该目录与路由表的一致性当前**不成立**，属独立缺口；本能力只约束它的写法）

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

## ADDED Requirements

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
