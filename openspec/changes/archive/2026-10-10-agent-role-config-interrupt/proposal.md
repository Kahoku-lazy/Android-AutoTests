## Why

`engines/agents` 里模型连接、角色参数和工具清单搅在一起，执行角色也无法在回复进行中干净停掉。实验角色需要能单独配模型、单独配角色，并按 AgentScope 2.0.9 的方式中断。

## What Changes

- `ModelConfig` 只保留模型连接；`CreateModel` 分别创建 DeepSeek、OpenAI、DashScope。DeepSeek 看图仍走 OpenAI 兼容客户端。DashScope 的 `base_url` 为空时不覆盖框架默认地址。
- 新增 `RoleConfig`：名称、系统提示词、工具包、是否看图、是否流式，以及 ReAct 与上下文参数。`BaseRole` 只接收 `ModelConfig` 与 `RoleConfig`。
- `tools_config.py` 用 `EXECUTOR_TOOL_NAMES` 选择设备工具，未知名字直接报错，再包装成 `EXECUTOR_TOOLKITS`。
- `BaseRole.interrupt()`：回复进行中取消当前任务；已暂停等待工具确认时发送 `UserInterruptEvent`。未调用 `start()` 时中断会失败。
- 不改 `engines/ai/`，不改 `engines/agents/role/executor.py`。

## 关联文档

无关联需求编号。这是 `engines/agents` 实验角色的配置与中断，不进入平台规格。

## Capabilities

### New Capabilities

### Modified Capabilities

## Impact

- `engines/agents/role/base.py`
- `engines/agents/tools_config.py`
- 不改 `apps/`、前端、`engines/ai/`。
