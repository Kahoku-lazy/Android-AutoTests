## ADDED Requirements

### Requirement: 启动时组装执行与验收模型

系统 SHALL 在启动控制设备任务时，从所选助手的控制设备线路读取执行模型与验收模型，并交给 SOP。系统 MUST NOT 再调用旧规划引擎，也 MUST NOT 要求规划角色存在。执行或验收缺少模型名、密钥为空，或 provider 不是 DeepSeek 与阿里百炼之一时，任务 MUST 以失败结束，并且 MUST NOT 开始步骤。provider 不合法时，错误 MUST 指出该 provider 与合法集合。

#### Scenario: 执行与验收模型进入 SOP

- **WHEN** 控制设备线路上执行与验收都有合法的模型名、密钥与 provider，且 YAML 通过格式检查
- **THEN** 任务启动 SOP，使用这两份模型，不调用规划模型

#### Scenario: 缺少规划角色仍可启动

- **WHEN** 控制设备线路没有规划角色，但执行与验收配置合法
- **THEN** 任务仍能启动 SOP

#### Scenario: 模型配置不合法时失败

- **WHEN** 执行或验收的模型名为空、密钥为空，或 provider 不是 DeepSeek 与阿里百炼之一
- **THEN** 任务状态为失败，不开始第一步，错误说明指出缺失或非法的项
