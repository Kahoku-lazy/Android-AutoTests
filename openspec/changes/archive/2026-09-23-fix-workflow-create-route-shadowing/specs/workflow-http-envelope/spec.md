## ADDED Requirements

### Requirement: Legacy 平铺写端点必须可达

系统 SHALL 让下列写请求命中页面流的 legacy 平铺视图，并返回平铺体 `{status, prototype|directory|document}`：

- `POST /api/workflow/prototypes/create/`
- `POST /api/workflow/directories/create/`
- `POST /api/workflow/documents/create/`
- `POST /api/workflow/documents/import/`

这些路径 MUST NOT 被按主键匹配的详情路由抢占。命中错误视图时，响应 MUST NOT 是因为「该视图不接受此方法」而产生的 405。

#### Scenario: 新建原型成功

- **WHEN** 用户在页面流入口提交合法原型名称 `POST /api/workflow/prototypes/create/`
- **THEN** 返回 2xx，响应体顶层 `status` 为真且含 `prototype` 对象（含 `id`、`name`）
- **AND** 该原型出现在随后 `GET /api/workflow/prototypes/` 的 `data` 数组中

#### Scenario: 新建目录与新建页面流文档成功

- **WHEN** 提交 `POST /api/workflow/directories/create/` 或 `POST /api/workflow/documents/create/`
- **THEN** 返回 2xx，响应体顶层含 `directory` 或 `document`，且资源归属提交的 `prototype_id`

#### Scenario: 导入文档成功

- **WHEN** 提交 `POST /api/workflow/documents/import/` 且 body 为合法 envelope
- **THEN** 返回 2xx，响应体顶层含 `document`，落库归属提交的 `prototype_id`

#### Scenario: 非法入参是业务错误而不是方法错误

- **WHEN** 上述任一写端点收到空名称等非法入参
- **THEN** 返回 4xx 且响应体 `status` 为假并带 `message`
- **AND** 本次请求零落库

#### Scenario: 写端点不返回 405

- **WHEN** 对这四条路径发起 POST
- **THEN** 响应状态码 MUST NOT 为 405

### Requirement: 目录与原型改名删除走标准方法与信封

目录改名 SHALL 通过 `PATCH /api/workflow/directories/{id}/` 提交；目录删除 SHALL 通过 `DELETE /api/workflow/directories/{id}/` 提交；原型改名 SHALL 通过 `PATCH /api/workflow/prototypes/{id}/` 提交。成功响应 SHALL 为标准信封 `{status: true, data: ...}`；删除类响应 MUST 携带可解析的响应体，前端 MUST 以信封 `status` 而非 HTTP 204 空体判定成功。

#### Scenario: 目录改名回显信封

- **WHEN** 前端对某目录提交 `PATCH /api/workflow/directories/{id}/` 且 body 为 `{name}`
- **THEN** 返回 200，`data.name` 为新名称
- **AND** 未提交 `parent_id` 时父级保持不变

#### Scenario: 目录删除成功可判定

- **WHEN** 前端对某目录提交 `DELETE /api/workflow/directories/{id}/`
- **THEN** 返回 2xx 且响应体 `status` 为真
- **AND** 该目录不再出现在目录列表中

#### Scenario: 原型改名回显信封

- **WHEN** 前端对某原型提交 `PATCH /api/workflow/prototypes/{id}/` 且 body 为 `{name}`
- **THEN** 返回 200，`data.name` 为新名称
