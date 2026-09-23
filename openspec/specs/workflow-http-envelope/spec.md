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

### Requirement: 页面流写操作只有一套路由且返回标准信封

页面流的全部写操作 SHALL 只由 DRF router 生成的路由承担，MUST NOT 再存在第二套同义实现或平铺信封出口：

- 创建原型 / 目录 / 文档 SHALL 走集合路由 `POST /api/workflow/prototypes/`、`POST /api/workflow/directories/`、`POST /api/workflow/documents/`
- 导入文档 SHALL 走动作路由 `POST /api/workflow/documents/import/`
- 改名 / 删除 / 移动 SHALL 走详情路由或动作路由（`PATCH` / `DELETE` / `POST .../move/`）

成功响应 SHALL 为标准信封 `{status: true, data: ...}`，`data` 为被创建或更新后的资源对象。旧平铺写地址 `POST /api/workflow/{prototypes|directories|documents}/create/` SHALL 返回 404。

#### Scenario: 新建原型走集合路由

- **WHEN** 调用 `POST /api/workflow/prototypes/` 且 body 含合法 `name`
- **THEN** 返回 201，响应体为 `{status: true, data: {id, name, doc_count, ...}}`
- **AND** 该原型出现在 `GET /api/workflow/prototypes/` 的 `data` 数组中

#### Scenario: 新建目录与新建文档走集合路由

- **WHEN** 调用 `POST /api/workflow/directories/` 或 `POST /api/workflow/documents/`
- **THEN** 返回 201，响应体为 `{status: true, data: <该资源对象>}`

#### Scenario: 导入文档走动作路由

- **WHEN** 调用 `POST /api/workflow/documents/import/` 且 body 为合法 envelope
- **THEN** 返回 2xx，响应体为 `{status: true, data: <文档对象>}`

#### Scenario: 旧平铺写地址已下线

- **WHEN** 调用 `POST /api/workflow/prototypes/create/`、`POST /api/workflow/directories/create/` 或 `POST /api/workflow/documents/create/`
- **THEN** 返回 404 或 405 这类「路径或方法不存在」的 4xx，MUST NOT 返回 2xx
- **AND** MUST NOT 由第二套平铺实现应答，且库中不产生任何新资源

#### Scenario: 前端调用面不残留旧写地址

- **WHEN** 检查前端页面流 API 层的调用字面量
- **THEN** 不存在以 `/create/` 结尾的页面流写地址
- **AND** 创建类调用读取响应的 `data` 键，不读取平铺的 `prototype` / `directory` / `document` 顶层键

### Requirement: 文档更新按提交字段合并并支持归属写入

文档的写入 SHALL 按「提交了什么就改什么」处理：

- 创建时提交的 `directory_id` MUST 成为该文档的归属目录
- 更新时提交的 `directory_id` MUST 改写归属，显式提交 `null` MUST 表示移到原型根，未提交时 MUST 保持原归属不变
- 更新时未提交的 `title` / `doc_type` / `config` / `description` MUST 保持原值，MUST NOT 被置空
- 只提交部分字段（例如只提交 `title` 与 `doc_type`）SHALL 成功，MUST NOT 因缺字段被拒

提交的目录不属于该文档所属原型时 SHALL 返回 4xx，且本次请求零落库。

#### Scenario: 创建文档时的归属生效

- **WHEN** `POST /api/workflow/documents/` 的 body 含 `directory_id`
- **THEN** 返回的 `data.directory_id` 等于该目录 id，且该文档出现在该目录下

#### Scenario: 只改标题也能成功（重命名）

- **WHEN** 更新时只提交 `title` 与 `doc_type`，未提交 `config`
- **THEN** 返回 2xx，`data.title` 为新标题
- **AND** 该文档的 `config` 与 `description` 保持更新前的值

#### Scenario: 未提交的描述不被清空

- **WHEN** 更新时提交了 `config`，未提交 `description`
- **THEN** 该文档的 `description` 保持原值

#### Scenario: 更新文档归属

- **WHEN** `PATCH` 或 `PUT /api/workflow/documents/{doc_id}/` 提交新的 `directory_id`
- **THEN** 该文档归属改为新目录

#### Scenario: 显式 null 移到根

- **WHEN** 更新时提交 `directory_id: null`
- **THEN** 该文档归属变为空（原型根）

#### Scenario: 未提交归属则不动

- **WHEN** 更新时只提交 `title`，未提交 `directory_id`
- **THEN** 该文档原归属保持不变

#### Scenario: 跨原型目录被拒

- **WHEN** 提交的 `directory_id` 属于另一个原型
- **THEN** 返回 4xx，且该文档的归属与标题均未改变
