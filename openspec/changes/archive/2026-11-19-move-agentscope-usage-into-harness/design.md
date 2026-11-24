## Context

见 proposal.md 的 Why。与本设计相关的现状：

- `ae_harness` 已是 AgentScope 的主要落点：`agents/creator.py` 造 Agent，`agents/models.py` 造模型，`middleware/`、`workflow/sop/`、`tools/`、`knowledge/` 都在这里直接引用框架。
- `backend_bridge` 里只有两处直接引用框架：`session.py` 用 `UserMsg` 发一轮消息；`workflow/fake_world.py` 用 `FunctionTool`、`ToolChunk`、`TextBlock` 做评测假工具。其余文件只引用 `ae_harness` 的原语。
- `tests/engines/backend_bridge/unit/test_import_guard.py` 的 `ALLOWED_ROOTS` 显式允许 `agentscope`。这是当前唯一放行的地方。
- `backend_bridge/AGENTS.md` 红线 10 规定运行取消归 `backend_bridge`，不在 `ae_harness` 另立。本变更不动取消。

## Goals / Non-Goals

**Goals:**

- `backend_bridge` 内不再出现 `import agentscope`。
- 会话逐轮行为与评测假工具行为不变。

**Non-Goals:**

- 不实现 GoalPipeline、TeamPipeline、会话持久化、向量库切换。
- 不移动 `backend_bridge` 的角色装配、工具勾选、报告路径与取消登记。这些是平台语义。
- 不改后端 App 与前端。

## Decisions

### 1. 用户消息构造放 `ae_harness/agents/messages.py`

新增一个函数 `user_message(content: str)`，返回框架的 `UserMsg(name="user", content=content)`。`session.py` 的 `run_turn` 改为调用它，删除 `from agentscope.message import UserMsg`。

不把整个会话搬进 `ae_harness`：`UiExecutorSession` 还负责报告目录、事件面板、用量汇总和设备序列号前缀，这些属于平台装配。只把框架类型的构造收进去。

备选是把 `session.py` 整体搬进 `ae_harness`。否决：那样 `ae_harness` 就要知道报告根目录和平台事件面板，违反「原语层不接平台」。

### 2. 假工具构造放 `ae_harness/tools/scripted.py`

新增 `scripted_tool(name, input_schema, respond)`：按给定名字与入参形状造一个 `FunctionTool`，调用时执行传入的 `respond` 并返回文本块。`fake_world.py` 保留「按勾选取真工具、复制名字、记账、取剧本正文」这些平台逻辑，只把框架对象的构造换成这个函数。

`respond` 由 `fake_world` 传入，这样 `ae_harness` 不知道评测剧本、不知道 `select_tools`。

备选是把 `scripted_tools` 整体搬进 `ae_harness`。否决：它依赖 `backend_bridge.agents.tool_selection`，搬过去会让原语层反向依赖装配层。

### 3. 导入守卫从允许改为禁止

`test_import_guard.py` 的 `ALLOWED_ROOTS` 去掉 `agentscope`，并在 `FORBIDDEN_PREFIXES` 增加 `agentscope`。这样 `backend_bridge` 再直接引用框架时测试失败。

`json` 仍留在允许清单：`fake_world.py` 记账后仍要自己组返回正文，只是不再组框架对象。

### 4. 规则文本与代码同一提交

- `ae_harness/AGENTS.md` 目录结构补两行：`agents/messages.py` 只造用户消息；`tools/scripted.py` 只造按名字回放的假工具。
- `backend_bridge/AGENTS.md` 增加一条：本目录不得 `import agentscope`，框架类型经 `ae_harness` 的函数取得。

两条都是职责与依赖边界，范围以上面两句为界，不改其它红线。

## 模块防火墙自检

- 不新增跨 App 依赖。`ae_harness` 仍不 import `apps.*` 与 `django.*`。
- `backend_bridge` 对 `ae_harness` 的依赖只增加两个函数调用，方向不变。
- 无数据库读写。

## Risks / Trade-offs

- [假工具的返回形状变了] → `scripted_tool` 的返回块与现在逐字段一致：一个 `TextBlock(type="text")`，正文由调用方给。既有 `test_fake_world.py` 继续断言同名、只记账、无真实副作用。
- [会话消息的 name 变了] → `user_message` 固定 `name="user"`，与现在的 `UserMsg(name="user", ...)` 相同。
- [守卫误伤注释里的 agentscope 字样] → 守卫扫的是 `import` 语句，不扫注释与字符串。

## Migration Plan

1. 先加两个原语函数及各自的单测。
2. 再改 `session.py` 与 `fake_world.py` 的调用点。
3. 最后收紧导入守卫并改两份 AGENTS。顺序反过来会让守卫在改完前就失败。

## Open Questions

无。
