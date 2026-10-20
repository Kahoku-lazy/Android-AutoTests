## 1. 锁定现有时间线

- [x] 1.1 在 `tests/graybox/unit/test_agent_events_show.py` 用假事件（类名即事件类型）调用 `AgentEventsShow.show(event, buf)`，覆盖：`CustomEvent` 原文、`ReplyStartEvent` 清空上一轮缓冲、思考碎片拼合、工具入参截断 300、工具返回截断 400、图片只打媒体类型与 base64 长度、`ModelCallEndEvent` 的 token 行、未识别类型只打印一次 `· {类型名}`。验证：在改实现之前，`python -m pytest tests/graybox/unit/test_agent_events_show.py -q` 因现有草稿无法按该入口消费事件而失败。

## 2. 收成无状态分派

- [x] 2.1 重写 `AgentEventsShow`：去掉绑定单条事件的 `__init__`，`show` 为静态方法；阶段方法按「流程边界 → 一轮发言 → 思考与正文 → 工具调用 → 工具返回 → 仅 `ModelCallEndEvent`」返回是否已消费，未消费才在 `show` 末尾打印类型名。打印文案、截断与 `buf.clear()` 时机与现有 `UiAutoWorkflow.show` 一致，字段注释随分支搬走。验证：同一条 pytest 通过。
- [x] 2.2 `UiAutoWorkflow.show` 改为把 `(event, buf)` 委托给 `AgentEventsShow.show`。不改 `dump`、`run`、`AgentSOPWorkflow`、`__main__`。验证：`run` 仍调用 `self.show(event, buf)`；`UiAutoWorkflow.show` 内不再保留按事件类名分支的 `if / elif`。

## 3. 定向检查

- [x] 3.1 对改动文件做静态检查。验证：`ruff check engines/agents/workflow/ui_auto_workflow.py tests/graybox/unit/test_agent_events_show.py` 通过（本文件既有的 `print` 放行除外，不得新增其它告警）。不跑全量回归。
