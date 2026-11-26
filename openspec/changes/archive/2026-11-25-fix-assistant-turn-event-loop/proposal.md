# Proposal: fix-assistant-turn-event-loop

## Why

同一个对话栏里，在当前依赖版本（agentscope 2.0.12 + openai 3.55.1 / httpx2 2.16.2）下，第二轮消息会以
`执行异常: Event loop is closed` 收场：每一轮都用 `asyncio.run()` 新建并在结束时销毁事件循环，而智能体
（内含 `openai.AsyncClient` → `httpx2` 连接池）按会话缓存、跨轮复用，上一轮遗留的 keep-alive 连接绑在
**已关闭**的 loop 上，下一轮第一次模型调用就会在连接复用或过期连接清理时调用
`loop.call_soon()` → `RuntimeError: Event loop is closed`。

2026-11-25 11:22:51 的真实会话（thread `919cb9d9b7fd481f`，DB 消息 34/35）就是此问题：请求尚未发出即失败
（`backend.log` 无对应 `httpx2 HTTP Request`，只有 agentscope「exhausted all 1 attempt(s)」告警），
而 9 秒后重发同一条指令在 11:24:12 完整跑通。同进程内实测呈「成功 / 失败 / 成功 / 失败」交替。

## What Changes

- 新增**进程级常驻事件循环**（守护线程 + `asyncio.run_coroutine_threadsafe`）：智能体的创建与每一轮
  `reply_stream` 都在同一个 loop 上执行，回合内不再出现 `asyncio.run`。
- `_run_turn` 改为「ORM 读 → 把协程提交到常驻 loop（建 agent + 跑回复）→ ORM 写」，数据库操作继续留在
  调用线程，不进入 loop 线程。
- 把 `thread_agent()` 与 `_reply()` 合并进**同一个协程**，`thread_observer()` 也在 loop 线程内取，
  消除「agent 在 loop A 建、在 loop B 用」的跨循环。
- 明确保持不变：同一会话复用同一智能体实例（多轮上下文）、取消语义、用量记账、报告落盘、错误文案口径。

## 关联文档

纯缺陷修复，无 PRD 编号与需求单。规格侧只对 `single-agent-chat` 增加一条执行生命周期约束。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `single-agent-chat`: 新增「会话执行的事件循环生命周期」需求 —— 同一会话的智能体实例与其模型客户端
  MUST 在同一个未关闭的事件循环上创建与使用，多轮之间 MUST NOT 重建或关闭该循环。

## Impact

- **代码**：`backend/apps/ai_assistant/services/assistant_threads.py`（`_run_turn` 改走常驻 loop）、
  新增 `backend/apps/ai_assistant/services/agent_loop.py`。`engines/backend_bridge/agents/thread_run.py`
  的会话缓存口径不变（`_AGENTS` 仍按 thread_id 复用），只是首次创建真正与使用同 loop。
- **测试**：`tests/ai_assistant/api/test_assistant_threads.py` 不受影响（`queue_turn` 在 pytest 下本就短路）；
  回归证据用 `temps/` 脚本（跨「回合」复用同一 client 断言不再抛错）+ 本地服务双轮手动验证。
- **行为变化**：稳定进程内同一会话的第二轮不再报 `Event loop is closed`；常驻 loop 线程随进程常驻，
  由守护线程语义保证退出。
- **依赖/数据库**：无新依赖、无迁移、无接口变更。
- **回退**：还原 `assistant_threads.py` 并删除 `agent_loop.py`，行为回到逐轮 `asyncio.run`。
