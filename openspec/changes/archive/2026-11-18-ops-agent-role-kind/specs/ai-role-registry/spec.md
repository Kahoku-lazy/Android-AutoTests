# ai-role-registry Delta

## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: 角色响应字段与鉴权

角色记录 MUST 以下发字段表示：`role_id` / `name` / `model_config_id` / `provider` / `api_key_env` / `model_name` / `base_url` / `api_protocol` / `system_prompt` / `kinds` / `created_at` / `updated_at`，时间 MUST 为 ISO 8601 字符串。`kinds` MUST 为字符串数组，元素取值为 `executor` / `verifier` / `planner`，未分类时 MUST 为空数组。全部角色接口 MUST 需要登录态：未携带有效凭证时 MUST 返回 401。

#### Scenario: 响应只含约定字段

- **WHEN** 请求某角色详情
- **THEN** `data` 恰好含上述十二个字段
- **AND** 不出现自增主键 `id`

#### Scenario: 未登录被拒

- **WHEN** 不带有效凭证请求任一角色接口
- **THEN** 返回 401
