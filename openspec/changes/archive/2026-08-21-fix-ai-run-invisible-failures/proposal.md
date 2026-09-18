## Why

AI 助手执行用例（TC-NAV-004）两次均以"已达最大推理次数"失败：`run_test` 返回 `{status: true}`，但执行协程在设备锁处**静默死亡**——`tr_test_runs` 从未落库，`get_run_status` 只能回答"run 不存在"，AI 反复换 run_id 重试直至耗尽 20 次迭代。诊断（详见对话记录）确认两个 P0 根因：① `device_pool.api.acquire_device` 用 `device_obj.occupied_by != user_id` 比较，CharField 存的 `"1"` 与传入的 `int(1)` 恒不相等，AI 自锁被判"他人占用"而抛错；② 执行链在 `_execute_tests._persist_run_start` 之前的所有失败路径（锁失败/连接失败）都不落任何记录、只发无人订阅的 WS 事件，AI 与用户零可见性。

## What Changes

1. **P0** `apps/device_pool/api.py`：`acquire_device` 占用者比较改为 `str(device_obj.occupied_by) != str(user_id)`——恢复"同一用户重入刷新锁"的设计意图。
2. **P0** `apps/test_runner/api.py`：`start_run` 在投递协程前同步预建 `PENDING` 状态的 `TestRunRecord`（含用例快照）——`get_run_status` 立即可查；新增 `mark_run_failed(run_id, error, status)` 供失败路径调用。
3. **P0** `apps/test_runner/views/execution_steps.py`：`_persist_run_start` 的 AI 路径（无 TaskCard）复用已有记录升级为 `running`，不再盲目 `create`（避免与预建记录唯一冲突）。
4. **P0** `apps/test_runner/views/ai_execution.py`：acquire 失败分支返回前调用 `mark_run_failed` 并写文件日志（不再只发无人订阅的 WS 事件）。
5. **P0** `apps/test_runner/views/helpers.py`：`_abort_run_before_execute` 在 AI 路径（`client_task_id` 为空）同步标记 FAILED/STOPPED——覆盖连接失败、中途停止等执行前退出。
6. **P1** `apps/ai_assistant/agent_scope/tool_registry.py`：`run_test` 描述改为"无需先 acquire_device（工具自行锁定设备）"；`get_run_status` 描述补充 PENDING/FAILED 语义与查询时机。

无 **BREAKING** 变更。

## 关联文档

- `dev_docs/02-PRD需求/PRD-06-执行引擎.md`（TestRunRecord / 执行生命周期）、`PRD-08-AI助手.md` §4.1（`run_test`/`get_run_status` 工具）
- `apps/device_pool/AGENTS.md`（占用/释放必须走本 App api.py）、`apps/test_runner/AGENTS.md`（状态机勿绕过、设备锁经 device_pool api）
- `models/test_models.py` `TestRunStatus`（小写五值，唯一真相源）
- 诊断证据：`ai_messages` 对话 211（msg 403/405 blocks）、`logs/backend.log`（16:11–16:16）、`ai_execution.py:48-55`、`device_pool/api.py:82-93`

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

> 纯 Bug 修复 + 工具描述校准：恢复到 PRD 已定义行为（run 记录可查、AI 工具语义正确），无需求级行为变化，`.openspec.yaml` 已设 `skip_specs: true`。

## Impact

- 后端：`apps/device_pool/api.py`（1 行）、`apps/test_runner/api.py`（+~30 行）、`apps/test_runner/views/execution_steps.py`（AI 分支改写）、`apps/test_runner/views/ai_execution.py`（失败分支 +~6 行）、`apps/test_runner/views/helpers.py`（+~8 行）、`apps/ai_assistant/agent_scope/tool_registry.py`（2 处描述字符串）
- 数据：修复后首次执行 TC-NAV-004 将产生真实 `tr_test_runs`/`tr_test_results` 记录（预期 completed）
- 测试范围：`manage.py check` + `ruff` + `--check-boundaries` + 同用户重锁单测式验证 + 真实设备端到端（start_run → 轮询 get_run_status → completed + 结果落库）
