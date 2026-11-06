## 1. 引擎：取消在事件边界断流

- [x] 1.1 `engines/agents/workflow/ui_auto_workflow.py`：`run_workflow` 增加可选入参 `should_stop: Callable[[], bool] | None = None`，在 `async for event in engine.reply_stream(...)` 的每次循环体里检查，为真即 `raise asyncio.CancelledError`；验证：`python -m pytest -c tests/pytest.ini tests/graybox/unit/test_platform_cancel.py -q` 通过，且「未传 `should_stop` 时照常跑完」的用例保持绿色。
- [x] 1.2 `engines/agents/workflow/platform_run.py`：`_drive_real` 构造 `AgentSOPWorkflow` 时传入 `should_stop=cancel_event.is_set`（`cancel_event` 为空时传 `None`），保留原有 `task.cancel()` 投递与 `clear_cancel` 收口；验证：同一测试文件里「单用例任务取消后返回 `status=cancelled`、不再出现第二次尝试」用例通过。
- [x] 1.3 `engines/agents/config/role_types.py`：`ReActConfig` 增加 `interruption_raise_cancelled_error: bool = True`（并在类 docstring 的 Attributes 里补一行）；验证：`python -c "from engines.agents.config.role_types import ReActConfig as C; print(C().interruption_raise_cancelled_error)"` 输出 `True`。
- [x] 1.4 `engines/agents/agent_builders.py`：`_as_react_config` 透传 `interruption_raise_cancelled_error`；验证：新增断言用例确认 `AsReActConfig().interruption_raise_cancelled_error is True`，并入 1.1 的测试文件。
- [x] 1.5 engines 自检：在 `.agents/skills/engines-docstring-check` 下跑 `python -m scripts.docstrings check`、在 `.agents/skills/engines-agents-style-check` 下跑 `python -m scripts.check_engines_agents_style`；验证：本次新增/修改行无新增告警，存量 23 条告警数量不变。

## 2. 平台：取消不放行设备槽，终态不被覆盖

- [x] 2.1 `backend/apps/task_list/api.py`：`finalize_task` 增加关键字参数 `release_device: bool = True`，仅在为真时调用 `dispatch_device`；`cancel_running_task` 传 `release_device=False` 并改 docstring；验证：`python -m pytest -c tests/pytest.ini tests/api/test_task_cancel_dispatch.py -q` 中「取消后同 serial 的 pending 任务保持 pending」用例通过。
- [x] 2.2 `backend/apps/task_list/task_runner.py`：`spawn_task_thread` 把线程登记进模块级 `_workers`；新增 `schedule_cancel_release(task_id, serial, timeout=60)`，超时且线程仍存活时写一条 `TaskCancelTimeoutEvent`（复用 `TaskEventSink` + `bind_run_context`，与 `_emit_interrupt` 同一机制）并强制放行；验证：同文件用例覆盖「线程已退出→不触发告警」「线程仍存活→写告警并放行」两条分支。
- [x] 2.3 `backend/apps/task_list/api.py` 的 `cancel_running_task` 通过函数内 import 调用 `schedule_cancel_release`；验证：取消接口返回 `{"id", "status": "cancelled"}` 且该调用不影响接口耗时（计时器为 daemon，不阻塞响应）。
- [x] 2.4 `backend/apps/task_list/task_runner.py`：`run_task_async` 的 SOP 分支在 `finalize_task` 前 `refresh_from_db()`，状态已是 `cancelled` 时只回写用量；`finally` 里取消 2.2 的计时器并放行设备；验证：用例覆盖「取消后工作线程跑完→终态仍为 cancelled」「取消后工作线程异常→仍为 cancelled 且不写失败原因」。
- [x] 2.5 后端门禁：`python manage.py check`、`ruff check backend/apps/task_list`、`python -m pytest -c tests/pytest.ini tests/api/test_task_cancel_dispatch.py tests/graybox/unit/test_case_run_continuity.py -q`；验证：全部通过，无 `makemigrations` 变更。
- [ ] 2.6 `backend/apps/task_list/task_reports.py`：`_step_outcome` / `_case_outcome` 增加 `cancelled` 入参，`_flow_cases` 按 `task.status == "cancelled"` 传入；验证：`python -m pytest -c tests/pytest.ini tests/api/test_task_report_cancelled.py -q` 通过（当前步主动关闭、未开始步仍未执行、已判 FAIL 不改写）。
- [x] 2.7 `frontend/src/modules/task-list/components/CaseStepList.vue` 的徽标与图标映射补「主动关闭」，复用既有中性色不新增 CSS；验证：`npm run typecheck` 与 `npx vitest run tests/task-list` 通过。

## 3. 回归与真机验收

- [x] 3.1 `tests/graybox/unit/test_case_run_continuity.py` 增补「单用例任务执行中取消」场景；验证：`python -m pytest -c tests/pytest.ini tests/graybox/unit/test_case_run_continuity.py -q` 通过。
- [x] 3.2 全量相关回归：`python -m pytest -c tests/pytest.ini tests/graybox/unit tests/api/test_task_*.py -q`；验证：无新增失败（既有失败项逐条说明来源）。
- [x] 3.3 真机验收（实跑任务 198「关闭功能测试-01」：5 步用例，第 1 步执行中关闭）：关闭后 0 条事件、0 次模型调用、¥0，工作线程已退出；关闭前最后一条事件早于点击 2.5 秒，故秒级延迟只能给「关闭后无任何新增事件」这一事实。验证：关闭后新增模型调用为 0，任务终态为已关闭。
- [x] 3.4 本地门禁：`python run.py check`；验证：阻塞项通过（`vitest` 若因未提交的前端改动失败，需逐条说明不是本次引入）。
- [x] 3.5 文档：在 `dev_docs/DEV_TEST/UI自动化 问题记录.md` 增补本次事故（任务 197：关闭后仍运行 230 秒、77 次设备操作、¥0.9394）与修复后的行为口径；验证：文档可被 `python utils/gen_arch_stats.py --check-md` 检查通过（若该检查覆盖此文件）。
- [x] 3.6 界面验收：任务详情里被关闭任务的当前步与用例徽标显示「主动关闭」，未执行步骤仍显示「未执行」；验证：真机关闭任务后打开详情页目视确认，且不出现「未完成」。
