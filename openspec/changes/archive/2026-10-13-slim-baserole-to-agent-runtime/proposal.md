## Why

`engines/agents/role/base.py` 的 `BaseRole` 现在 301 行、一个类扛四件事：**创建智能体**、**运行入口**（`reply` / `reply_detail`）、**日志上屏**（`print_result`、`scope_label` / `mark_scope`）、**用量与费用**（`usage` / `cost` / `_cost_calculator`）。后两件与"角色运行"没有关系，读这个类时要穿过一堆计费与打印代码才能看清运行链路。

实测调用面进一步说明问题：

- 有调用方的只有 `start()`（`agents.py:189-190`）与 `register_skills()`（`executor.py:29` + 4 处测试）。
- `reply` / `reply_detail` / `print_result` / `usage` / `cost` / `interrupt` / `scope_label` / `mark_scope` 在脚手架内**全部 0 调用**。
- `self._scope` **只写不读** —— 过程日志已在归档单 `2026-10-12-retire-agents-pipe-log` 退役，`scope_label` / `mark_scope` 成了纯死代码。

## What Changes

- `engines/agents/messaging/messages.py` 新增四个函数：`reply_usage(result)`、`reply_cost(provider, model_name, result, *, created_at=None)`、`print_result(result)`、`async render_reply_stream(agent, user_msg)`；模块 docstring 由"工具返回 → 可读文本"扩为"可读文本 + 用量与费用 + 上屏"。
- `engines/agents/role/base.py`：
  - 删除 `usage` / `cost` / `_cost_calculator` / `print_result` / `scope_label` / `mark_scope` 与 `self._scope`。
  - `reply_detail` 改名为 **`reply_stream`**（仍是同步方法，内部 `asyncio.run`）；`_reply_stream` 退化为「登记任务 + 调 `render_reply_stream`」两行。
  - 清理失效导入：`ConsoleRenderer`、`DeepSeekBilling`、`datetime`、`ZoneInfo` 与 `_SHANGHAI` 常量（`Msg` 以 ruff `F401` 判定）。
  - 模块 docstring 改为与 `role/config.py` 对齐的格式：`python -m 调试路径: …` + 「本模块的业务功能如下：」+ 编号清单。
- `engines/agents/messaging/__init__.py`：导出四个新函数。
- **Non-goals**：不动 `register_skills`、`interrupt`、`_reply` / `_running` / `_require_agent`、`_react_config` / `_context_config`、`_tool_group` 系列、`_user_msg`；不拆新模块（用量与费用按用户指定放在 `messages.py`，不另立 `metrics.py`）。

## 关联文档

无关联需求编号。本次是纯重构 + 脚手架内部 API 调整（删的都是零调用方法、改名的也是零调用方法），运行链路行为不变，不进入 PRD / ARCH 编号体系。按 schema 约定设 `skip_specs: true`。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

无。被移动/删除/改名的成员在脚手架内 0 调用，可观察行为不变（`agents.py` 走 SOP runner，不直接调角色 reply）。故以 `skip_specs: true` 退出 specs 阶段。

## Impact

- 代码：`engines/agents/messaging/messages.py`、`engines/agents/messaging/__init__.py`、`engines/agents/role/base.py`（三者均未被 git 跟踪）。
- 调用方：**零改动** —— 移动与改名的成员无调用方；`start` / `register_skills` 保持原样。
- 依赖新增：`messages.py` → `..billing`（`engines.agents.billing`）。已核实 `billing.py` 只依赖标准库与 `chinese_calendar`、**不 import role**，故无循环；同时要更新 `messages.py` 那句"只依赖标准库与 AgentScope 消息类型"的自述。
- 测试：`tests/graybox/unit/test_executor_tool_groups.py` 只用 `register_skills`，不受影响；`tests/graybox/unit/test_agent_event_stream.py:177` 的 `mark_scope` 属**平台侧** `engines.ai.agents.AgentRole`，不受影响。
- 平台侧零改动：`engines/ai/**`、`apps/**`、`frontend/**` 不动。
