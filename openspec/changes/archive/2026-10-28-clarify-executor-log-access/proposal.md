# 执行提示词声明：日志检查只属于验收模型

## Why

执行模型与验收模型的工具集不同：`check_device_log` 只装配给验收模型，执行模型没有日志工具。执行提示词目前没有说明这一点，模型可能尝试查日志、凭猜测写日志结论，或在 handover 里把「没查日志」当成已完成。

## What Changes

- 执行提示词新增一条约束：设备串口日志检查由验收模型通过日志工具完成，只有验收模型有该权限；执行模型禁止尝试检查、推测或声称检查过日志，也不在 handover 里写日志结论。
- 执行模型只需在 handover 里给出每次操作的 `action_time`，供验收模型核对日志。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `role-prompt-guardrails`：新增「执行提示词声明日志检查不属于执行模型」的需求。

## Impact

- 提示词：`engines/agents/prompts/executor_prompt.py`。
- 测试：`tests/graybox/unit/test_role_prompt_guardrails.py`。
- 不影响工具装配（`check_device_log` 本来就只在验收角色）、后端、前端、数据库。
