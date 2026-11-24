## Why

AgentScope 的直接调用应当只出现在 `ae_harness`。现在 `backend_bridge` 还有两处自己 `import agentscope`：会话发消息时构造 `UserMsg`，评测假工具时构造 `FunctionTool`。框架类型散在装配层，换框架时要改的不只是原语层。

## What Changes

- 在 `ae_harness` 增加一个构造用户消息的函数，`backend_bridge/session.py` 改为调用它，不再自己 `import agentscope.message`。
- 在 `ae_harness/tools/` 增加一个「同名假工具」构造，`backend_bridge/workflow/fake_world.py` 改为调用它，不再自己 `import agentscope.tool` 与 `agentscope.message`。
- `backend_bridge` 完成后不得再出现 `import agentscope`。导入守卫从「允许 agentscope」改为「禁止 agentscope」。
- 同步两份 `AGENTS.md` 的职责说明：`ae_harness` 承接消息构造与假工具，`backend_bridge` 写明不直接引用 AgentScope。
- 不做：GoalPipeline / TeamPipeline 接线、会话持久化、向量库切换。这三项仍按既有暂缓决定，不在本变更。

## 关联文档

无独立 PRD 编号。本变更是内部依赖收敛：AgentScope 的使用点收到原语层，对外行为不变。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

无。消息构造与假工具的对外行为不变：会话仍按连接键复用同一个角色，评测假工具仍按勾选复制名字与入参、只记账不触达真实设备。本变更只移动实现位置，不改变可观察行为。

## Impact

- 引擎：新增 `ae_harness` 内的消息构造与假工具构造；修改 `backend_bridge/session.py`、`backend_bridge/workflow/fake_world.py`。
- 规则：`engines/ae_harness/AGENTS.md`、`engines/backend_bridge/AGENTS.md` 的职责与依赖边界说明。
- 测试：`tests/engines/backend_bridge/unit/test_import_guard.py` 收紧允许清单；既有 `test_session.py` 与 `test_fake_world.py` 行为不变。
- 不涉及后端 App、前端页面、数据库与接口。
