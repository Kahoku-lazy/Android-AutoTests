## ADDED Requirements

### Requirement: 执行提示词声明日志检查不属于执行模型

执行角色的系统提示词 MUST 声明：设备串口日志检查由验收模型通过日志检查工具完成，只有验收模型具有该权限；执行模型 MUST NOT 尝试检查日志、MUST NOT 推测日志结论、MUST NOT 声称自己检查过日志，也 MUST NOT 在 handover 里写日志结论。执行模型只需在 handover 里给出每次操作的 `action_time`，供验收模型核对日志。

#### Scenario: 提示词声明日志权限

- **WHEN** 读取执行角色的系统提示词常量
- **THEN** 其中明确日志检查只属于验收模型，执行模型不需要处理该任务

#### Scenario: 提示词禁止声称查过日志

- **WHEN** 检查执行角色提示词中关于设备日志的表述
- **THEN** 其中禁止执行模型检查日志、推测日志结论、声称检查过日志或把日志结论写进 handover
