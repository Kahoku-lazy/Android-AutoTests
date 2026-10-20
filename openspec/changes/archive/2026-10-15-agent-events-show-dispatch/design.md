## Context

见 `proposal.md` - Why。

现状（`engines/agents/workflow/ui_auto_workflow.py`）：`UiAutoWorkflow.show`（约 151–238 行）是唯一被 `run` 调用、且能跑通的时间线实现。文件顶部的 `AgentEventsShow` 是未接入的草稿：`__init__` 绑住单条事件，`_start_events` 使用未定义的 `kind` / `event` / `buf`，`_model_usage_events` 的 `else` 会对几乎每条事件再打印一次类型名。`buf` 由 `run` 跨事件持有；`ReplyStartEvent` 时清空。

本模块在 import 时会构造 `executor` / `verifier`（`engines/agents/role/agents.py` 的模块级副作用）。本次不拆文件，因此单测导入可视化类时会连带执行这段构造，但不调用这两个角色。

## Goals / Non-Goals

**Goals:**

- `AgentEventsShow` 无实例状态，唯一入口 `show(event, buf)` 按事件类名分派。
- 每个阶段方法返回是否已消费该事件；兜底打印只出现在 `show` 末尾。
- `UiAutoWorkflow.show` 委托上述入口，`run` 的调用方式不变。
- 单测用假事件锁定现有打印文本。

**Non-Goals:**

- 不改 `dump`、`run`、空壳 `AgentSOPWorkflow`、`__main__`。
- 不改打印文案、入参截断 300、返回截断 400、图片只打长度、`ReplyStart` 清空 `buf` 的时机。
- 不把可视化类拆到新模块，不消除 `executor` / `verifier` 的模块级构造。

## Decisions

**D1：`AgentEventsShow` 不保存 `event` 或 `buf`，`show` 为静态方法。**

备选是无字段实例，由 `UiAutoWorkflow` 持有。没有需要跨事件保存的状态（缓冲仍在调用方），实例没有职责。静态方法让 `UiAutoWorkflow.show` 直接委托，也不必在 `__init__` 里多挂一个对象。

**D2：阶段方法返回布尔值，`show` 命中即返回。**

顺序与现有 `if / elif` 一致：流程边界（`CustomEvent`）→ 一轮发言（`ReplyStartEvent` / `ReplyEndEvent`）→ 思考与正文 → 工具调用 → 工具返回 → 模型用量（只认 `ModelCallEndEvent`）→ 兜底 `print(f"    · {kind}")`。

草稿把用量方法的 `else` 当成兜底，导致已处理的事件被打两遍。布尔返回把「未识别」收口到唯一一处。

备选是类名到函数的分派表。思考块与正文块、工具调用的三段事件共享处理，表会拆得很碎，不如按阶段返回布尔值。

**D3：`UiAutoWorkflow.show` 保留为委托，不改 `run`。**

`run` 继续 `buf = {}` 后调用 `self.show(event, buf)`。委托方法把同一对参数交给 `AgentEventsShow.show`。事件字段注释随对应分支搬进阶段方法。

**D4：单测只喂假事件并捕获标准输出。**

事件用动态类名构造（与 `tests/graybox/unit/test_agent_event_stream.py` 的 `_event` 相同手法）。覆盖：自定义事件、`ReplyStart` 清空上一轮碎片、思考块拼合、工具入参截断、工具返回文本截断、图片只打长度与类型、模型用量、未识别类型只出现一次。不跑 `SOPEngine`，不连设备。

## 模块防火墙自检

- 不新增跨 App import，不写任何表，不碰 `api.py`。
- 不改前端，不新增 HTTP / WebSocket。
- 改动限制在 `engines/agents/workflow/ui_auto_workflow.py` 与一条单元测试。`engines/ai/**` 不改。

## Risks / Trade-offs

- [搬分支时改动打印文案或截断长度] → 单测按现有格式断言关键行，包含截断与「只打一次类型名」。
- [导入工作流模块会构造两个角色] → 接受为既有副作用；单测不调用它们。若导入失败，停止并报告，不把类拆到新文件来绕过。
- [兜底再次漏进某个阶段的 `else`] → 用量阶段只在 `ModelCallEndEvent` 时返回已消费，其它类型返回未消费。

## Migration Plan

无部署。回退是把 `UiAutoWorkflow.show` 的分支还原，并删掉无状态分派与对应单测。

## Open Questions

无。是否以后把可视化类拆出本模块、以免导入时构造角色，不改变本单做法，需要时另立。
