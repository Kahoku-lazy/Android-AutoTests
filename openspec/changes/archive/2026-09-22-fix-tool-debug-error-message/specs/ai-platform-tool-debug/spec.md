## ADDED Requirements

### Requirement: 调试失败展示服务端可读错误

调试页加载入参 schema 或执行工具失败时，系统 MUST 展示服务端错误信封中返回的可读 `message`（存在时），MUST NOT 只展示 HTTP 状态码原文（如 `Request failed with status code 400`）。服务端未提供 `message` 时，系统 SHALL 展示按状态码归类的可读提示，MUST NOT 静默忽略错误。本地参数校验失败（如缺少必填参数）MUST 展示其自身的本地提示文案，MUST NOT 被上述服务端错误格式化覆盖。

#### Scenario: 展示服务端返回的失败原因

- **WHEN** 用户执行工具，服务端返回带 `message` 的失败响应
- **THEN** 调试页展示该 `message` 文本
- **AND** MUST NOT 只显示 `Request failed with status code` 一类状态码原文

#### Scenario: schema 加载失败同样展示服务端原因

- **WHEN** 调试页加载某工具 schema 失败且响应带 `message`
- **THEN** 页面错误区展示该 `message`

#### Scenario: 本地参数校验提示不被覆盖

- **WHEN** 用户未填写必填参数即点击执行
- **THEN** 页面提示「请填写必填参数」一类本地文案
- **AND** MUST NOT 变成网络类兜底文案
