# Tasks: fix-task-runtime-p0-defects

## 1. 费用回写改源（P0-1）

- [ ] 1.1 修改 `backend/apps/task_list/api.py` `rollup_task_cost`：改调 `summarize_ledger_cost(task_id)` 回写 `cost_*`，notes 非空记 warning；`summarize_ledger_cost` except 分支补 `backend_log.exception`。验证：新增/更新 `tests/task/unit/test_task_sweep.py` 用例——造账本记录后 sweep 收口，断言 `cost_total` 等于账本合计而非 0；`python -m pytest -c tests/pytest.ini tests/task/unit/test_task_sweep.py -q` 通过
- [ ] 1.2 核对 `tests/task/unit/` 与 `tests/ai_assistant/unit/test_ai_startup_recovery.py` 中以 TaskEvent 造费用数据的断言，改为账本造数或调整断言口径。验证：`python -m pytest -c tests/pytest.ini tests/task/unit tests/ai_assistant/unit/test_ai_startup_recovery.py -q` 通过

## 2. 心跳容错（P0-4）

- [ ] 2.1 修改 `backend/apps/task_list/task_runner.py` `_beat`：except 分支记日志后继续调度下一拍（不再永久停跳），同步 docstring。验证：新增 unit 用例——monkeypatch `touch_heartbeat` 第一拍抛异常、第二拍恢复，断言计时器仍被重新挂起且任务未被置终态；`python -m pytest -c tests/pytest.ini tests/task/unit -q -k heartbeat` 通过

## 3. 设备锁身份（P0-3）

- [ ] 3.1 修改 `backend/apps/device_pool/views.py` `lock_device`：删除 `request.data.get("user_id")` 回退，空身份返回 401。验证：新增 `tests/device/api` 用例——请求体携带伪造 `user_id` 时 `locked_by` 仍为 JWT 用户；`python -m pytest -c tests/pytest.ini tests/device -q` 通过

## 4. 清空收敛与 result 写原语（P0-5）

- [ ] 4.1 `backend/apps/task_list/api.py` 增 `init_task_result` 写原语（复用 `merge_task_result`）；`views.py` 两处 View 内 `task.save(update_fields=["result"])` 改调该原语。验证：`python -m pytest -c tests/pytest.ini tests/task -q` 通过，grep 确认 views.py 无 `.save(` 直写
- [ ] 4.2 `AgentTaskClearAPIView.post` 改调 `api.clear_agent_tasks()`，删除 View 内 `Task.objects.all().delete()`；响应形状不变。验证：新增 integration 用例——造带媒体任务后清空，断言表行与媒体目录均被清理；`python -m pytest -c tests/pytest.ini tests/task -q` 通过

## 5. 关单门禁

- [ ] 5.1 跑本地门禁并核对边界：`python run.py check` 退出码 0；`python utils/gen_arch_stats.py --check-boundaries` 零违规；`ruff check backend/apps/task_list backend/apps/device_pool` 与 `ruff format --check` 通过
- [ ] 5.2 按根 AGENTS 提交规范逐文件暂存、Conventional Commits 提交（fix(task_list) / fix(device_pool) 分提交），推特性分支提 PR，确认 ci-phase1.yml 的 python 与 frontend 两个 job 全绿后合并