## Context

见 `proposal.md` 的 Why。代码已落在 `engines/agents/role/base.py` 与 `engines/agents/tools_config.py`。本变更单补记已实现的行为。AgentScope 版本为 2.0.9。

## Goals / Non-Goals

**Goals:**

- 模型连接与角色参数分成两份配置。
- 执行角色用名字表选择工具。
- 中断覆盖「正在回复」和「暂停等待确认」两种状态。

**Non-Goals:**

- 不改 `engines/ai/agents/base.py` 的 `AgentRole`。
- 不改 `role/executor.py`。
- `EXECUTOR_SKILLS_NAMES` 只是名字列表，本次不把它接进 `build_toolkit`。

## Decisions

1. `RoleConfig` 与 `ModelConfig` 同一风格：构造时写入字段，`BaseRole(config, role)` 使用。ReAct 与上下文的默认值留在 `RoleConfig`（30 / 3 / True，0.7 / 0.2 / 400000 / 5）。
2. 工具选择放在 `tools_config.select_tools`。顺序跟名字表走，未知名字抛 `ValueError` 并列出可选名。
3. 中断按 2.0.9 文档：`reply` / `reply_detail` 记下当前任务；运行中用 `loop.call_soon_threadsafe(task.cancel)`；没有运行中的任务时，用 `UserInterruptEvent(reply_id=agent.state.reply_id)` 走 `reply_stream`。未在等待工具确认时，框架把这次调用当作空操作。

## 模块防火墙自检

- 不新增跨 App import，不写库。
- 不改前端。
- 设备工具仍经已有 `device_tool_specs` 与 `build_toolkit`。

## Risks / Trade-offs

- [运行中的 `reply` 堵住当前线程，同线程无法调用 `interrupt`] → 从另一条线程调用；取消后该轮抛出 `CancelledError`。
- [`executor.py` 仍是旧拷贝] → 本次明确不改它，避免和 `BaseRole` 的新构造参数混用。
