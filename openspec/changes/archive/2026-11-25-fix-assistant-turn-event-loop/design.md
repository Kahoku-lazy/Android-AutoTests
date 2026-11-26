# Design: fix-assistant-turn-event-loop

## Context

现状执行链（`backend/apps/ai_assistant/services/assistant_threads.py`）：

```
queue_turn → 新线程 _run_turn
   → asyncio.run(thread_agent(...))      # loop A：建 agent（内含 openai.AsyncClient）
   → asyncio.run(_reply(agent, ...))     # loop B：跑 reply_stream，HTTP 连接建在 loop B
   → loop A/B 结束时都被关闭
下一轮：同一 agent（命中 _AGENTS 缓存）在新 loop C 上被复用
   → 上一轮 loop B 的 keep-alive 连接仍在 httpx2 池里
   → 首次请求要么复用（http11._response_closed）、要么被当作过期连接清理（connection_pool._close_connections）
   → transport.abort() → loop_b.call_soon() → RuntimeError: Event loop is closed
```

约束：`single-agent-chat` 要求「同一连接内 MUST 复用同一个智能体实例，以保留多轮上下文」（会话缓存不能砍）；
`engines/` 禁止随意新增自定义异常类；错误文案 `执行异常: {exc}` 与 `已取消` 是既有对外口径。

## Goals / Non-Goals

**Goals**

- 智能体的创建与使用发生在同一个、且不会被后续回合关闭的事件循环上。
- 同一进程内同一会话连续多轮稳定成功（含长空闲后继续对话）。
- 取消、用量记账、报告落盘、错误文案口径不变。
- 零新依赖、零迁移、零接口变更。

**Non-Goals**

- 不调「模型调用失败自动重试」口径（另一条线，涉及钱与配额口径，需单独请示）。
- 不改 `_AGENTS` 会话缓存与内存回收策略。
- 不动 `engines/backend_bridge/run.py`、`task_list/task_runner.py`、`eval_suite.py` 等其它
  `asyncio.run` 调用点（他们每轮自建 agent，没有跨轮复用的客户端）。

## Decisions

### D1 进程级共享常驻 loop，而不是每会话一个 loop、也不是每轮重建 agent

- **每会话一个 loop** 需要额外的线程与生命周期回收逻辑，收益只是故障隔离，而当前没有隔离需求。
- **每轮重建 agent** 会丢掉多轮上下文（`_reply` 只把当前 `user_text` 交给 agent，历史存在 agent 实例里），
  直接违反 `single-agent-chat` 的既有要求。
- 共享常驻 loop 与现有「会话级 agent 生命周期」天然同寿，改动集中在一个模块，异步 I/O 在单 loop 上
  并发多路复用，不需要额外线程池。

### D2 一个回合只提交一个协程

把「建 agent」和「跑回复」合并成 `_turn(...)`：`await thread_agent(...)` 之后立刻取
`thread_observer(...)` 再 `await _reply(...)`。这样既修掉跨轮复用，也修掉**同轮内** agent 在 loop A 建、
在 loop B 用的问题（当前第一轮侥幸成功只是因为那时连接池还是空的）。

### D3 ORM 全部留在调用线程，loop 线程只跑 agent 与文件写入

`_run_turn` 保持「读 thread/最新 user_text → 提交协程 → `finish_message` / `_record_chat_usages`」的形状。
loop 线程不碰数据库：避免 Django 连接被多协程共享，也避免 `close_old_connections()` 在并发回合间互相踩。
`thread_agent` / `_reply` 本身不写库（已核对：只操作 agent、事件记录器与文件），符合这条边界。

### D4 调度层不包装异常，也不新增异常类

`agent_loop` 只提供「提交协程并阻塞取结果」；协程异常经 future 原样抛回 `_run_turn`，沿用现有
`RunCancelled` / `except Exception` 两条分支与文案。`engines/` 红线与对外错误口径都不动。

### D5 取消仍靠 `threading.Event`

`request_thread_cancel()` 从请求线程 set 事件，`CancelMiddleware` 在 loop 线程的每次模型调用前检查，
与 loop 归属无冲突；`cancel_thread()` 改库状态的行为不变。

## Risks / Trade-offs

- **单 loop 串行**：`AlignedReportRenderer().save()` 等同步文件写入会短暂阻塞其它会话的协程（一次报告
  数 MB，量级 10~100ms）。先接受并在真机双轮里观察；若出现可见卡顿，再把落盘挪到 `asyncio.to_thread`。
- **常驻线程**：多一个守护线程 + 一个 forever loop，`atexit` 停 loop；不阻止进程退出，也不需要迁移。
- **未来的工具写库**：若某个工具将来在 loop 线程里直接走 ORM，会占用该线程的 Django 连接。约束写进
  模块说明与设计：工具内写库要么留在 loop 外调用，要么 `asyncio.to_thread`。
- **内存**：`_AGENTS` 仍按会话常驻（现状），本次不扩大范围。

## Migration Plan

纯运行时改造，无数据/接口/配置迁移，发布即生效。回退 = 还原 `assistant_threads.py` 并删除
`agent_loop.py`，行为回到逐轮 `asyncio.run`。

## Verification

1. `temps/` 回归脚本：在常驻 loop 上连续两次提交同一个 `httpx2.AsyncClient` 请求（模拟两轮），断言两次
   都成功；对照组用两次 `asyncio.run` 必失败（排查阶段已复现 `RuntimeError: Event loop is closed`）。
2. 本地服务双轮：同一对话栏连发两条消息，第二条不再出现 `执行异常: Event loop is closed`；第 3、4 轮同样成功。
3. `python -m pytest -c tests/pytest.ini tests/ai_assistant -q`、`ruff check` / `ruff format --check`、
   `python utils/gen_arch_stats.py --check-boundaries`、`openspec validate fix-assistant-turn-event-loop`。

## Open Questions

无。
