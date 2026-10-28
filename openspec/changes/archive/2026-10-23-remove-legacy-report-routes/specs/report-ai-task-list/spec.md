## MODIFIED Requirements

### Requirement: 报告接口返回标准信封

`/api/reports/`、`/api/reports/{filename}/content/` MUST 返回标准信封 `{status, data}`，业务负载放在 `data` 中且 MUST NOT 自带 `status` 字段。`/api/reports/{filename}/` MUST 继续以附件形式返回文件（`FileResponse`），不套 JSON 信封。系统 MUST NOT 提供 `/api/reports/cases/` 与 `/api/reports/run/{run_id}/`。

#### Scenario: 报告列表使用信封

- **WHEN** 登录用户请求 `GET /api/reports/`
- **THEN** 响应为 200 且顶层只有 `status` 与 `data`
- **AND** `data` 含 `summary`、`trend`、`runs`

#### Scenario: 用例分解缺参数返回错误信封

- **WHEN** 请求 `GET /api/reports/cases/`（带或不带 `result`）
- **THEN** 响应为 404，MUST NOT 再返回 400、200 或空组负载

#### Scenario: 文件内容查看使用信封

- **WHEN** 请求 `GET /api/reports/{filename}/content/` 且文件存在
- **THEN** 响应为 200，`data` 含 `name`、`type`、`size`、`content`、`rows`、`headers`

#### Scenario: 文件不存在返回错误信封

- **WHEN** 请求 `GET /api/reports/{filename}/content/` 且目标不存在
- **THEN** 响应为 404，响应体为 `{status: false, message}`

#### Scenario: Run 详情端点不再存在

- **WHEN** 请求 `GET /api/reports/run/{run_id}/`
- **THEN** 响应为 404，MUST NOT 返回信封或任何报告负载

## ADDED Requirements

### Requirement: 报告工作台不提供报告详情与用例分解路由

测试报告工作台 MUST 只注册列表页 `/reports` 一个路由。系统 MUST NOT 注册 `/reports/:runId`、`/reports/cases/:resultType` 或等价路径；列表行、任务编号与 KPI 卡 MUST NOT 链到这两个路径。任务级详情 MUST 由任务清单的 `/tasks/:taskId` 提供。

#### Scenario: 直接访问已删的报告详情路由

- **WHEN** 用户直接打开 `/reports/143`
- **THEN** 前端不渲染报告详情页，落到 404 页

#### Scenario: 用例分解路由不可打开

- **WHEN** 用户直接打开 `/reports/cases/pass`
- **THEN** 前端落到 404 页，MUST NOT 渲染用例分解页

#### Scenario: 列表行仍进入任务详情

- **WHEN** 用户点击测试报告列表中的一行
- **THEN** 浏览器进入 `/tasks/` 加上该行的任务编号
