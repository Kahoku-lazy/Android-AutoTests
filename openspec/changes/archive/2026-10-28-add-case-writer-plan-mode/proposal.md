## Why

写用例是一个五阶段长任务（拆原子 → 匹配方法 → 定优先级 → 写 13 字段用例 → E2E 与自检），当前模型只靠自由推理维持进度，容易出现阶段漏做、写到一半忘记覆盖率或 E2E、驳回后不知道改到哪一步。AgentScope 计划模式提供结构化的任务清单工具，可以让编写角色显式跟踪阶段与完成状态。

## What Changes

- 给「写用例」角色装配 AgentScope 计划模式四件套：`TaskCreate`、`TaskGet`、`TaskList`、`TaskUpdate`；规划角色与验收角色不装配。
- 编写提示词新增「计划模式」章节：开始拆需求前先建计划任务，每进入/完成一个阶段更新状态，交付前确认计划全部完成；计划只是过程管理，不能替代七节文档。
- `CASE_WRITER_MAX_ITERS` 从 8 提到 20，为计划创建/更新留出工具轮次。
- 不新增数据库表、不改任务/用例接口、不改前端；计划清单随角色实例的生命周期存在。

## 关联文档

无关联需求编号：本次由用户口头需求驱动；API 参考 AgentScope 2.0.11 计划模式文档（https://docs.agentscope.io/zh/versions/2.0.11/building-blocks/plan）。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `appliance-case-authoring`: 编写角色的工具集与工作流新增计划模式要求；验收角色保持无计划工具。

## Impact

- 引擎：新增 `tools/tool_case_plan.py`；`tools_config.build_case_writer_toolkit`；`role/case_roles.py` 的 writer 装配与轮次预算；`prompts/case_writer_prompt.py` 的计划模式章节。
- 测试：新增工具装配单测、提示词关键词单测、角色装配单测；不涉及数据库与接口契约。
- 前端、任务域、用例管理无变化。
