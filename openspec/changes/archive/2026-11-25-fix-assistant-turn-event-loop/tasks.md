# Tasks: fix-assistant-turn-event-loop

## 1. 常驻执行循环

- [x] 1.1 新增 `backend/apps/ai_assistant/services/agent_loop.py`：懒启动一个守护线程与
  `asyncio.new_event_loop()`，提供 `run_in_loop(coro)`（`asyncio.run_coroutine_threadsafe(...).result()`）
  与 `atexit` 停止逻辑；不自建线程池、不包装异常。
  - 验证：`temps/agent_loop_regression.py` 连续 4 次提交同一 `httpx2.AsyncClient` 的请求，4 轮均 200，退出码 0
- [x] 1.2 同脚本对照旧写法：两次 `asyncio.run` 复用同一个 `httpx2.AsyncClient` 必抛
  `RuntimeError: Event loop is closed`；新写法两次都返回 200
  - 验证结果：旧写法第二轮 `RuntimeError: Event loop is closed`；新写法 1~4 轮全部 200，脚本打印 PASS

## 2. 回合改造

- [x] 2.1 `assistant_threads.py` 新增 `_turn(...)` 协程：`await thread_agent(...)` → `thread_observer(...)`
  → `await _reply(...)`，一个回合只在一个协程里完成建 agent 与回复
  - 验证：线下真机 4 轮（`temps/live_turn_check.py`）全部 `status=done`
- [x] 2.2 `_run_turn` 改为 `run_in_loop(_turn(...))`，删除两处 `asyncio.run`；ORM 读写（`get_thread`、
  最新 user_text、`finish_message`、`_record_chat_usages`）仍留在调用线程
  - 验证：同一进程连续 4 轮对话全部成功（第 2、3 轮之间留 35s 越过连接保活期），无 `Event loop is closed`
- [x] 2.3 取消与失败口径回归：`RunCancelled` → `已取消`、其它异常 → `执行异常: {exc}` 两条分支代码路径不变
  - 验证：`temps/test_turn_failure_semantics.py`（2 条，`-p tests.conftest` 补齐 sqlite collation）全绿——
    失败轮落 `执行异常: Event loop is closed` + `interrupted`；取消轮落 `已取消` + `cancelled`

## 3. 关单

- [x] 3.1 本地服务双轮实测：同一对话栏连发 4 条消息，4 轮都产出正常回复（覆盖保活过期与未过期两种间隔）
  - 验证结果：`temps/live_turn_check.py` 退出码 0，4 轮 `status=done`；`logs/backend.log` 在 15:4x 无
    `Event loop is closed`、无 Traceback；运行中的后端已随改动正常热重载（15:42:31 ONLINE）
- [x] 3.2 `python -m pytest -c tests/pytest.ini tests/ai_assistant -q` 全绿
  - 实际：48 passed / 20 failed。20 条失败全部是与本改动无关的既有红，已逐条定位：
    `test_roles` / `test_role_kinds` 因在途的 `AIRole` 模型重构（`AIRole() got unexpected keyword arguments:
    'model_name'`、创建端点 403）、`test_eval_run` 因在途评测改造（服务模块被删）、
    `test_assistant_thread_logs::test_unknown_report_is_404` 是 `fix-assistant-log-report-id-404` 已登记的缺陷（401 vs 404）。
    本改动相关用例全绿：`test_assistant_threads.py` 9/9。
- [x] 3.3 `python -m ruff check backend/apps/ai_assistant` + `ruff format --check` 通过
  - 实际：`ruff check` 全包通过；`ruff format --check` 对本次两个文件通过。全包 format 检查仍有 1 处既有问题
    `services/eval_scores.py`（另一在途变更的未跟踪文件，未触碰）
- [x] 3.4 `python utils/gen_arch_stats.py --check-boundaries` 退出码 0（零违规）
- [x] 3.5 `openspec validate fix-assistant-turn-event-loop` 通过
