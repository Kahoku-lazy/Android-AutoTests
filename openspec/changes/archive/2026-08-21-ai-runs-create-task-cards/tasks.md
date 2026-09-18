## 1. 后端：AI 运行接入任务卡生命周期

- [x] 1.1 `apps/test_runner/api.py` `start_run`：投递前 `save_task_card` 建卡（task_id=run_id、name=用例标题、creator=resolve_creator(user_id)）、登记 `_run_client_task[run_id]=run_id`、预建 PENDING 记录的 `client_task_id=run_id`——验证 `manage.py check` + `ruff check apps/test_runner` 通过
- [x] 1.2 `apps/test_runner/state_machine.py` `dequeue` 幂等化（get_or_create + 复用分支升级 running，保留 started_at）——验证 shell：预建 PENDING 后连续 dequeue 不冲突、队列路径新建语义不变
- [x] 1.3 `apps/test_runner/views/ai_execution.py` `_run_ui_for_ai` 读取 `_run_client_task`，将真实 client_task_id 传给 `_abort_run_before_execute` 与预检登记——验证 ruff + 人工核对三条 abort 调用

## 2. 端到端与门禁

- [x] 2.1 端到端：经 `start_run` 发起一次 TC-NAV-004 执行——验证 `tr_task_cards` 出现 task_id=run_id 的记录且终态 done/completed、case_items 含通过率、TestRunRecord 的 client_task_id 一致
- [x] 2.2 真实对话复核：对话 211 请求执行——验证执行引擎任务列表可见该任务卡（GET /runner/tasks 返回该卡）
- [x] 2.3 全部门禁：`manage.py check` + `ruff check apps/test_runner` + `python tools/gen_arch_stats.py --check-boundaries` 全绿
- [x] 2.4 `openspec archive ai-runs-create-task-cards` 归档本 change
