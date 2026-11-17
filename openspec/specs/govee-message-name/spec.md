# govee-message-name Specification

## Purpose
约束 govee 网关发出的 OpenAI 兼容消息，避免非 user 角色携带 `name` 被上游拒绝。

## Requirements

### Requirement: govee strips name from non-user messages

govee 创建的聊天模型 SHALL 在请求发出前，从 `system` 与 `assistant` 消息中删除 `name` 键。该行为 MUST 覆盖该通道上的全部模型名，MUST NOT 按模型名前缀分支。`user` 消息的 `name` MUST 保留。`tool` 消息的 `name` MUST 保留。

#### Scenario: system name is removed

- **WHEN** govee 模型收到一条带 `name` 的 system 消息
- **THEN** 发出的对应消息没有 `name` 键
- **AND** 消息正文保持不变

#### Scenario: assistant name is removed

- **WHEN** govee 模型收到一条带 `name` 的 assistant 消息
- **THEN** 发出的对应消息没有 `name` 键

#### Scenario: user and tool names stay

- **WHEN** govee 模型收到带 `name` 的 user 消息和 tool 消息
- **THEN** 两条消息的 `name` 都保留

#### Scenario: other providers are unchanged

- **WHEN** 调用方以 `deepseek` 或 `dashscope` 创建模型
- **THEN** 本需求不改变它们现有的消息格式
