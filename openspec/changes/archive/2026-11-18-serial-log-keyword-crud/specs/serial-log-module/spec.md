## ADDED Requirements

### Requirement: 关键词维护接口（仅超管）

平台 SHALL 在 `/api/serial-log/keywords/` 下提供关键词维护接口，且 MUST 仅限超级管理员：`POST /api/serial-log/keywords/`（新建）、`PATCH /api/serial-log/keywords/<int:row_id>/`（部分更新）、`DELETE /api/serial-log/keywords/<int:row_id>/`（删除）。路径 MUST 以 `/` 结尾；响应 MUST 遵循平台信封 `{status, data}` 与 snake_case。`GET /api/serial-log/keywords/` 的功能点条目 MUST 带 `row_id`（条目主键）。全部写入 MUST 经串口日志模块的 api；非超管请求 MUST 返回 403 且不产生写入。业务错误（重复新建、编辑撞车、条目不存在）MUST 返回可读 400；删除 MUST NOT 影响日志文件与采集。

#### Scenario: 超管新建关键词

- **WHEN** 超级管理员 `POST /api/serial-log/keywords/`，body 为 `{"keyword": "h6601_boot", "module": "设备开关", "feature": "H6601开机完成", "scope": "H6601"}`
- **THEN** 返回 201，条目落库且范围为 H6601，功能点编号按全表续编

#### Scenario: 新建缺省通用与续编

- **WHEN** 超级管理员新建时不带 scope 与 feature_id
- **THEN** 条目范围为通用（`*`），功能点编号为全表 max+1，行序追加表尾

#### Scenario: 重复新建被拒

- **WHEN** 超级管理员 POST 已存在的「关键词 + 功能点编号 + 范围」组合
- **THEN** 返回可读 400，表内不产生第二行

#### Scenario: 非超管被拒

- **WHEN** 普通登录用户请求 POST / PATCH / DELETE 关键词接口
- **THEN** 返回 403，关键词表不发生任何变化

#### Scenario: 编辑部分更新

- **WHEN** 超级管理员 `PATCH /api/serial-log/keywords/<row_id>/`，body 为 `{"feature": "打开设备成功（改）"}`
- **THEN** 返回 200，仅该字段更新，其余字段与行序不变

#### Scenario: 编辑撞车被拒

- **WHEN** 超级管理员 PATCH 把条目改成另一行已有的「关键词 + 功能点编号 + 范围」
- **THEN** 返回可读 400，两行均保持原样

#### Scenario: 编辑或删除不存在条目

- **WHEN** 超级管理员 PATCH 或 DELETE 一个不存在的 row_id
- **THEN** 返回可读 400，不返回服务端错误

#### Scenario: 删除单条不影响采集

- **WHEN** 超级管理员 `DELETE /api/serial-log/keywords/<row_id>/`
- **THEN** 返回 200，该条目移除，日志文件与端口监听状态不变

#### Scenario: 目录带 row_id

- **WHEN** 已登录用户 `GET /api/serial-log/keywords/`
- **THEN** 每个功能点条目带 `row_id`，与表内主键一致
