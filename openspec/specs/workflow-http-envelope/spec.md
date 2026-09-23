# workflow-http-envelope Specification

## Purpose
规定页面流工作台对 router 实际命中的 HTTP 读路径使用标准信封 `{status, data}`，使成功响应展示列表或详情，而不是误报加载失败或静默空树。

## Requirements

### Requirement: Prototype list consumes standard envelope

打开页面流原型列表时，系统 SHALL 将 `GET /api/workflow/prototypes/` 的成功体解析为 `{status: true, data: <array>}`。`status` 为真且 `data` 为数组时 MUST 渲染该数组（空数组展示空态，不得展示加载失败）。仅当 HTTP 失败或 `status` 为假时 MUST 展示错误态并可重试。

#### Scenario: Successful prototype list

- **WHEN** 用户打开页面流入口且列表接口返回 `{status: true, data: [{id, name, ...}, ...]}`
- **THEN** 页面展示对应原型卡片，不出现「原型列表加载失败」

#### Scenario: Empty prototype list is not an error

- **WHEN** 列表接口返回 `{status: true, data: []}`
- **THEN** 页面展示空态（引导创建），MUST NOT 展示错误态

#### Scenario: HTTP or status failure shows error

- **WHEN** 列表请求抛错，或响应 `status` 为假
- **THEN** 页面展示错误态与重试入口

### Requirement: Prototype detail consumes standard envelope

进入某个原型工作台时，系统 SHALL 将 `GET /api/workflow/prototypes/{id}/` 的成功体解析为 `{status: true, data: <object>}`，并从 `data` 读取名称等字段。MUST NOT 依赖顶层 `prototype` 键。

#### Scenario: Successful prototype boot

- **WHEN** 用户进入已存在原型且详情接口返回 `{status: true, data: {id, name, ...}}`
- **THEN** 工作台使用 `data.name` 作为原型名并继续加载目录树

#### Scenario: Missing prototype remains an error

- **WHEN** 详情接口返回非 2xx 或 `status` 为假
- **THEN** 工作台展示错误态，MUST NOT 当作空工作台继续

### Requirement: Directory and document reads consume nested data

系统 SHALL 按各 router 端点实际 `data` 形状读取：目录列表的 `data.directories`（及如有则 `data.tree`）；文档列表的 `data` 为数组；文档详情与导出从 `data` 取文档字段或 `data.envelope`。成功且形状正确时 MUST 填充资源树或画布；MUST NOT 把缺失的顶层 `documents` / `document` 键当成空成功而静默清空。

#### Scenario: Directory list nested in data

- **WHEN** `GET /api/workflow/directories/?prototype_id=` 返回 `{status: true, data: {directories: [...], tree: [...]}}`
- **THEN** 资源树按 `data.directories` 渲染

#### Scenario: Document list is data array

- **WHEN** `GET /api/workflow/documents/?prototype_id=` 返回 `{status: true, data: [{doc_id, title, ...}, ...]}`
- **THEN** 资源树按该数组中的页面流文档渲染

#### Scenario: Document detail uses data object

- **WHEN** `GET /api/workflow/documents/{doc_id}/` 返回 `{status: true, data: {doc_id, title, config, ...}}`
- **THEN** 画布从 `data.config` 水合，MUST NOT 读取顶层 `document`
