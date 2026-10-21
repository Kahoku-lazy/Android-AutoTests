## ADDED Requirements

### Requirement: 报告接口返回标准信封

`/api/reports/`、`/api/reports/cases/`、`/api/reports/run/{run_id}/`、`/api/reports/{filename}/content/` MUST 返回标准信封 `{status, data}`，业务负载放在 `data` 中且 MUST NOT 自带 `status` 字段。`/api/reports/{filename}/` MUST 继续以附件形式返回文件（`FileResponse`），不套 JSON 信封。

#### Scenario: 报告列表使用信封

- **WHEN** 登录用户请求 `GET /api/reports/`
- **THEN** 响应为 200 且顶层只有 `status` 与 `data`
- **AND** `data` 含 `summary`、`trend`、`runs`

#### Scenario: 用例分解缺参数返回错误信封

- **WHEN** 请求 `GET /api/reports/cases/` 且未给 `result`（或给了 pass/fail 以外的值）
- **THEN** 响应为 400，响应体为 `{status: false, message}`
- **AND** `message` 说明 `result` 必须为 pass 或 fail

#### Scenario: 文件内容查看使用信封

- **WHEN** 请求 `GET /api/reports/{filename}/content/` 且文件存在
- **THEN** 响应为 200，`data` 含 `name`、`type`、`size`、`content`、`rows`、`headers`

#### Scenario: 文件不存在返回错误信封

- **WHEN** 请求 `GET /api/reports/{filename}/content/` 或 `/api/reports/run/{run_id}/` 且目标不存在
- **THEN** 响应为 404，响应体为 `{status: false, message}`
