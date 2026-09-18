# ai-agent-model-config Specification

## Purpose
TBD - created by archiving change agent-model-config-consolidation. Update Purpose after archive.
## Requirements
### Requirement: 配置页统一管理三类模型

系统 SHALL 在智能体配置页的模型配置区块提供三类模型配置：主推理模型、视觉模型、强模型，管理员可分别指定，且保存后配置持久化并在后续对话构建时生效。

#### Scenario: 管理员配置三类模型

- **WHEN** 管理员打开智能体配置页的模型配置区块
- **THEN** 可见主推理模型、视觉模型、强模型三个配置项，可分别选择或输入模型名

#### Scenario: 保存后三类模型生效

- **WHEN** 管理员保存智能体配置
- **THEN** 后续对话构建按保存的主推理 / 视觉 / 强模型配置生效

### Requirement: 强模型开关控制路由

系统 SHALL 用独立开关控制强模型是否启用：关闭时不使用强模型，开启时将对话下发给强模型 Harness 执行。

#### Scenario: 关闭强模型

- **WHEN** 强模型开关为关闭状态
- **THEN** 系统不启用强模型 Harness，对话按意图在视觉与推理 Harness 之间路由

#### Scenario: 开启强模型

- **WHEN** 强模型开关为开启状态
- **THEN** 系统将对话下发给强模型 Harness，使用配置的强模型名执行

### Requirement: 强模型名留空回退视觉模型

系统 SHALL 在强模型开启但强模型名为空时，回退使用视觉模型作为强模型 Harness 的模型。

#### Scenario: 强模型名留空

- **WHEN** 强模型开关开启且强模型名为空
- **THEN** 强模型 Harness 使用视觉模型名执行

### Requirement: 卡片页收敛为对话配置测试

系统 SHALL 在智能体卡片页移除模型切换与删除操作，卡片仅保留「对话 / 配置 / 测试」三个操作，模型修改只能通过配置页完成。

#### Scenario: 卡片操作收敛

- **WHEN** 用户查看智能体卡片
- **THEN** 卡片仅展示「对话 / 配置 / 测试」三个操作，无模型下拉与删除按钮

