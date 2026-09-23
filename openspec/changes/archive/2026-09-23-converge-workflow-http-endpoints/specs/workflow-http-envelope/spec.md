## REMOVED Requirements

### Requirement: Legacy 平铺写端点必须可达

**Reason**: 该要求是为「legacy 平铺写端点与 router 并存」而立的临时契约。本变更把页面流写接口收敛为**只有 router 一套**，legacy 平铺视图整体删除，其依赖的平铺响应形状（`{status, prototype|directory|document}`）不再存在，要求随之失效。

**Migration**: 调用方改走标准路由——创建类用集合路由 `POST /api/workflow/{prototypes|directories|documents}/`，导入用动作路由 `POST /api/workflow/documents/import/`，均返回标准信封 `{status, data}`；旧地址 `POST /api/workflow/{prototypes|directories|documents}/create/` 一律 404。前端调用面与本地脚本须同步改造。

## ADDED Requirements

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
