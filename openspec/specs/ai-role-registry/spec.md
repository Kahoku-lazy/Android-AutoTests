# ai-role-registry Specification

## Purpose
给「AI 助手」提供一张干净的角色注册表与它的增删改查接口：一条记录只描述一个角色（叫什么、用哪个模型、系统提示词是什么、对外用哪个短标识），不含模型线路、密钥、任务类型等其它关注点，供后续重设计在此基础上生长。

## Requirements

### Requirement: 角色记录只描述角色本身

系统 SHALL 用一个独立于 `ai_agents` 的存储位置保存角色，每条记录 MUST 只包含以下字段：对外短标识 `role_id`、角色名称 `name`、模型名称 `model_name`、系统提示词 `system_prompt`、创建时间 `created_at`、更新时间 `updated_at`。系统 MUST NOT 在该记录上保存模型密钥、模型线路、任务类型、头像、密钥状态或提示词分段等其它关注点。

`name` MUST 为非空字符串，长度上限 200 字符，且首尾空白 MUST 被去除后再判断是否为空。`model_name` MUST 为非空字符串，长度上限 200 字符；系统 MUST NOT 按引擎模型表校验其取值，MUST NOT 限制其格式。`system_prompt` MUST 允许为空，且 MUST 按原样保存（不改写、不裁剪内部换行）。

#### Scenario: 创建一条最小角色

- **WHEN** 提交角色名称「页面执行」、模型名称「deepseek-flash」与一段系统提示词
- **THEN** 记录被保存，且读回的名称、模型名称、系统提示词与提交值逐字一致

#### Scenario: 系统提示词允许为空

- **WHEN** 提交角色名称与模型名称，系统提示词留空
- **THEN** 记录被保存，读回的系统提示词为空字符串
- **AND** 不因提示词为空而拒绝创建

#### Scenario: 空名称或空模型名称被拒

- **WHEN** 提交的角色名称为空、只含空白字符，或模型名称为空
- **THEN** 接口返回 400 与可读的中文错误说明
- **AND** 不写入任何记录

#### Scenario: 模型名称不做取值校验

- **WHEN** 提交的模型名称是任意非空字符串（例如「随便写的模型」）
- **THEN** 记录被保存，接口不因该值不在引擎模型表中而拒绝

### Requirement: role_id 以日期为前缀生成且全表唯一

每个角色的 `role_id` SHALL 在创建时生成，格式 MUST 为「当天日期 `YYYYMMDD`（8 位数字）+ 3 位随机字符」，随机字符 MUST 取自 `[0-9a-z]`（36 个字符），总长 MUST 为 11 位。生成时 MUST 保证全表唯一：若生成的标识已存在，系统 MUST 重新生成直到得到未占用的标识；同一角色的 `role_id` MUST NOT 因名称或内容变更而改变，且 MUST NOT 被更新接口修改。

日期的取值口径 MUST 为服务器所在时区的当天日期。同一天可用标识上限为 36 的 3 次方（46656）个；当该空间耗尽且重试仍无法得到未占用标识时，系统 MUST 返回可读错误，MUST NOT 写入重复标识或无限重试。

#### Scenario: 标识格式

- **WHEN** 在 2026-11-15 创建任意角色
- **THEN** 返回的 `role_id` 为 `20261115` 加 3 位 `[0-9a-z]` 字符，共 11 位

#### Scenario: 标识不重复

- **WHEN** 连续创建多条角色
- **THEN** 任意两条记录的 `role_id` 都不相同

#### Scenario: 标识不被更新

- **WHEN** 对某角色提交名称、模型名称或系统提示词的修改
- **THEN** 该角色的 `role_id` 与创建前一致

### Requirement: 角色名称全表唯一

同一时刻系统 MUST NOT 存在两条同名角色。`name` 比较 MUST 在去除首尾空白后按精确值比较（区分大小写）。名称已被占用时，创建与更新请求 MUST 被拒绝，接口 SHALL 返回 409 与可读的中文错误说明，且 MUST NOT 写入或改动任何记录。更新时提交与自身相同的名称 MUST 视为合法。

#### Scenario: 创建重名被拒

- **WHEN** 已存在名称为「页面执行」的角色，再提交同名角色
- **THEN** 接口返回 409
- **AND** 记录总数不变

#### Scenario: 更新成他人名称被拒

- **WHEN** 把角色 A 的名称改为现有角色 B 的名称
- **THEN** 接口返回 409
- **AND** 角色 A 的名称保持原样

#### Scenario: 更新保持自身名称可通过

- **WHEN** 只修改角色 A 的模型名称，名称原样提交
- **THEN** 更新成功，不与自身冲突

### Requirement: 角色列表与创建接口

`GET /api/ai/roles/` SHALL 返回全部角色的 `data` 数组，按创建时间倒序。`POST /api/ai/roles/` SHALL 创建角色并返回 201 与完整记录（含生成的 `role_id`）。两个方法的路径 MUST 以 `/` 结尾，成功响应 MUST 为 `{status: true, data: ...}` 信封。

#### Scenario: 列表按创建时间倒序

- **WHEN** 已存在三个角色，依次创建
- **THEN** `GET /api/ai/roles/` 的 `data` 为三条记录，最后创建的在最前

#### Scenario: 创建返回完整记录

- **WHEN** `POST /api/ai/roles/` 提交合法字段
- **THEN** 返回 201，`data` 含 `role_id` 与提交的 `name`、`model_name`、`system_prompt`

### Requirement: 角色详情、更新与删除接口

`GET /api/ai/roles/{role_id}/` SHALL 返回单个角色。`PATCH /api/ai/roles/{role_id}/` SHALL 只更新提交的字段，未提交字段 MUST 保持原值。`DELETE /api/ai/roles/{role_id}/` SHALL 物理删除并返回 200 与 `{status: true, data: {role_id}}`。`role_id` 不存在时这三个方法 MUST 返回 404 与可读错误，MUST NOT 以空 `data` 冒充成功。

#### Scenario: 部分更新只改提交字段

- **WHEN** `PATCH /api/ai/roles/{role_id}/` 只提交 `model_name`
- **THEN** 该字段被更新
- **AND** `name` 与 `system_prompt` 保持原值

#### Scenario: 删除后不可再读

- **WHEN** 删除某角色后再次请求该 `role_id` 的详情
- **THEN** 返回 404

#### Scenario: 未知标识返回 404

- **WHEN** 请求一个不存在的 `role_id`
- **THEN** 返回 404 与可读错误，MUST NOT 返回空 `data` 冒充成功

### Requirement: 角色响应字段与鉴权

角色记录 MUST 以下发字段表示：`role_id` / `name` / `model_config_id` / `provider` / `api_key_env` / `model_name` / `base_url` / `api_protocol` / `system_prompt` / `kinds` / `created_at` / `updated_at`，时间 MUST 为 ISO 8601 字符串。`kinds` MUST 为字符串数组，元素取值为 `executor` / `verifier` / `planner`，未分类时 MUST 为空数组。全部角色接口 MUST 需要登录态：未携带有效凭证时 MUST 返回 401。

#### Scenario: 响应只含约定字段

- **WHEN** 请求某角色详情
- **THEN** `data` 恰好含上述十二个字段
- **AND** 不出现自增主键 `id`

#### Scenario: 未登录被拒

- **WHEN** 不带有效凭证请求任一角色接口
- **THEN** 返回 401

### Requirement: 配置类型标签存放在独立关联表

角色的「类型」（执行者 / 验收者 / 规划者）MUST NOT 写进角色记录本表；系统 SHALL 用一个独立的关联表保存类型标签，一行 MUST 只表示「一条配置的一个类型」，包含自增主键、指向角色记录的外键、类型取值与创建时间四个字段。

关联 MUST 以角色记录为父（外键指向角色），角色被删除时其类型标签 MUST 随之删除，MUST NOT 留下孤儿标签。角色记录本身的字段清单 MUST NOT 因为本需求而增加类型字段。

#### Scenario: 带类型创建后角色记录不出现类型字段

- **WHEN** 创建一条类型为「验收者」的角色，并读取该角色记录
- **THEN** 角色记录本表字段中不含任何类型字段
- **AND** 关联表中存在一行指向该角色的「验收者」标签

#### Scenario: 删除角色连带删除标签

- **WHEN** 删除一条已带类型的角色
- **THEN** 该角色的类型标签同时被删除
- **AND** 关联表中不存在指向已删角色的行

#### Scenario: 存量角色允许没有类型

- **WHEN** 读取一条尚未打类型的存量角色
- **THEN** 该角色正常出现在列表里
- **AND** 其类型以空数组下发，不因此报错或被隐藏

### Requirement: 类型取值与唯一性

类型取值 MUST 只允许 `executor`（执行者）、`verifier`（验收者）、`planner`（规划者）三者之一，其它取值 MUST 被拒绝（400）且 MUST NOT 写入任何记录。

同一时刻一条角色 MUST NOT 拥有多个类型（一份配置不能同时是执行者与验收者）。创建角色时 `kinds` MUST 恰好包含 1 项，缺失、空数组或多于 1 项 MUST 被拒绝（400）。更新角色时 `kinds` 缺省 MUST 表示类型不变，显式提交 1 项 MUST 整体替换原类型，显式提交空数组 MUST 把该角色置为未分类。

类型变更 MUST NOT 改变角色的 `role_id`、名称、模型配置与系统提示词。

#### Scenario: 合法类型创建成功

- **WHEN** 创建角色时提交 `kinds: ["verifier"]`
- **THEN** 创建成功，读回的 `kinds` 为 `["verifier"]`

#### Scenario: 非法取值被拒

- **WHEN** 创建或更新角色时提交 `kinds: ["reviewer"]`
- **THEN** 接口返回 400 与可读的中文错误说明
- **AND** 记录与标签都不发生变化

#### Scenario: 一条配置两个类型被拒

- **WHEN** 创建角色时提交 `kinds: ["executor", "verifier"]`
- **THEN** 接口返回 400
- **AND** 该角色不会被创建

#### Scenario: 新建缺少类型被拒

- **WHEN** 创建角色时不提交 `kinds` 或提交 `kinds: []`
- **THEN** 接口返回 400，且不写入角色记录

#### Scenario: 更新替换类型

- **WHEN** 把一条「执行者」角色的 `kinds` 改为 `["verifier"]`
- **THEN** 读回的 `kinds` 只有 `["verifier"]`
- **AND** 该角色的 `role_id`、名称与系统提示词保持原值

#### Scenario: 更新清空类型

- **WHEN** 对一条已带类型的角色提交 `kinds: []`
- **THEN** 该角色变为未分类，`kinds` 读回为空数组
- **AND** 角色记录本身不被删除
