## 1. 后端：设备锁修复与可见性记录

- [x] 1.1 `apps/device_pool/api.py` `acquire_device` 占用者比较改 `str(...) != str(...)`——验证同用户二次 acquire 不再抛 ValueError（shell：连续两次 acquire 同 user_id 成功、锁行叠加、随后 release）
- [x] 1.2 `apps/test_runner/api.py` `start_run` 投递前预建 `PENDING` TestRunRecord（含 `_build_case_snapshots` 快照），新增 `mark_run_failed(run_id, error, status)`——验证 `manage.py check` + `ruff check apps/test_runner apps/device_pool` 通过
- [x] 1.3 `apps/test_runner/views/execution_steps.py` `_persist_run_start` AI 分支复用已有记录升级 running——验证预建后再执行不触发唯一冲突（真实执行见 3.1）
- [x] 1.4 `apps/test_runner/views/ai_execution.py` acquire 失败分支调 `mark_run_failed` 并写文件日志；`apps/test_runner/views/helpers.py` `_abort_run_before_execute` 在 AI 路径（client_task_id 为空）标记 failed/stopped——验证 ruff + 人工核对两条失败路径代码

## 2. AI 工具描述校准（P1）

- [x] 2.1 `apps/ai_assistant/agent_scope/tool_registry.py`：`run_test` 描述改为"无需先 acquire_device"、`get_run_status` 描述补 PENDING/FAILED 语义——验证 ruff 通过且 `TOOL_SCHEMAS` 加载正常

## 3. 端到端验证与门禁

- [x] 3.1 真实设备端到端：shell 调 `start_run('RUN-FIX-001', 'RF8N21MSW7A', ['TC-NAV-004'])` → 立即可见 PENDING 记录 → 轮询 `get_run_status` 至终态（completed/failed）→ `get_run_results` 有结果行、设备最终被释放——验证 AI 链路"run 不存在"不再出现
- [x] 3.2 全部门禁：`manage.py check` + `ruff check apps/device_pool apps/test_runner apps/ai_assistant` + `python tools/gen_arch_stats.py --check-boundaries` 全绿
- [x] 3.3 `openspec archive fix-ai-run-invisible-failures` 归档本 change
