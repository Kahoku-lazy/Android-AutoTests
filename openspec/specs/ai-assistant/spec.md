# ai-assistant Specification

## Purpose
智能体配置接口：按可见性列出智能体与线路，只下发页面展示所需字段（名称、标签、描述、模型与线路名），不再下发头像等 MB 级大字段。

## Requirements

### Requirement: 智能体接口不下发头像大字段

`GET /api/ai/agents/` 与 `GET /api/ai/agents/{id}/` MUST NOT 返回 `avatar` 字段与 `route_configs.*.avatar` 字段中的大字段内容。单次列表响应 MUST 小于 64KB（当前约 1 万条记录规模下）。响应其余字段（id / name / tags / description / model_* / task_kind / route_configs 的 name 与模型信息 / status / created_at）MUST 保持不变。

#### Scenario: 列表响应不再包含头像

- **WHEN** 客户端请求 `GET /api/ai/agents/`
- **THEN** 响应体不包含 `avatar` 键，`route_configs` 下每个线路也不含 `avatar`
- **AND** 响应体小于 64KB

#### Scenario: 详情响应不再包含头像

- **WHEN** 客户端请求某个智能体详情
- **THEN** 响应体同样不包含 `avatar` 与线路 `avatar`
- **AND** 名称、标签、描述、模型信息与线路名照旧

### Requirement: 历史超长头像在写入侧被清理

系统 MUST 把存量 `ai_agents.avatar` 与 `route_configs.*.avatar` 中长度超过 4096 字符的值清空，并在写入路径拒绝超过 4096 字符的头像值。清理 MUST 可重复执行且不影响其他字段。

#### Scenario: 存量超长头像被清空

- **WHEN** 数据迁移执行完毕
- **THEN** 超过 4096 字符的头像字段为空
- **AND** 同一行的名称、标签、描述、模型与线路名不变

#### Scenario: 超长头像写入被拒

- **WHEN** 保存智能体时提交超过 4096 字符的 avatar
- **THEN** 接口返回可读校验错误
- **AND** 数据库不写入该值
