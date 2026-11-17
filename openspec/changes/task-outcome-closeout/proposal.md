## Why

任务失败和中断现在分不清。工作线程里的任何异常都写成纯文本 `执行异常` 并标成 `failed`，服务重启、崩溃和热重载又把还在跑的任务一律写成「服务重启导致中断」。结果字段还会盖掉提交时写入的 `workflow_id`，关闭后的异常也能把 `cancelled` 改写成失败。

## What Changes

- 不新增任务状态。步骤没过、模型或设备或平台抛错仍是 `failed`；进程没把终态写完、预算超限仍是 `interrupted`；用户关闭仍是 `cancelled`。
- 失败结果改为 JSON，保留已有 `workflow_id`，并写入 `failure_kind`（`verdict` / `provider` / `device` / `platform`）与可读 `reason`。
- 中断结果改为 JSON，写入 `cause`（`stop_timeout` / `process_lost` / `budget`），不再一律写「服务重启」。
- 运行中的任务写心跳。服务进程只把心跳超时且仍为 `running` 的任务收成中断，避免新进程收走旧进程还在跑的任务。
- 终态写入只在当前状态仍为 `running` 时生效。已经是 `cancelled` 或其它终态时，只补费用，不改状态和结果。
- `python run.py stop` 等满 180 秒强制退出前，记下当时仍在跑的任务编号，供下次写成 `stop_timeout`。
- BUG 台账按失败类别分开来源键，同一次失败不建第二张单；中断正文使用 `cause`，不再固定写服务重启。

## 关联文档

无关联 PRD 编号。本次口径来自 2026-11-17 对任务失败与中断的排查：不新增状态，只把原因写进结果，并堵住终态被覆盖的竞态。

## Capabilities

### New Capabilities

- `task-outcome-closeout`: 任务终态的条件收口、失败类别、中断原因、心跳与停机超时标记。

### Modified Capabilities

- `task-execution-lifecycle`: 遗留 `running` 的中断说明不再固定为服务重启；停机超时与进程丢失分开；取消后的异常收口明确为条件更新。
- `ai-task-device-dispatch`: 启动恢复不再无条件收走全部 `running`；心跳仍在的任务保持运行，收尸后仍拉起 `pending`。
- `bug-ticket-management`: 失败按 `failure_kind` 建单，中断正文按 `cause` 说明，不再把所有中断写成服务重启。

## Impact

- `backend/apps/task_list/`：任务模型、`api.py` 收口、`task_runner.py`、`apps.py` 清扫、列表摘要与报告读取。
- `run.py`：强制停止前记录仍在跑的任务编号。
- `backend/apps/bug_manager/extract.py`：按失败类别和中断原因登记。
- `frontend/src/modules/task-list/`：列表摘要读 `reason`；轮询把 `interrupted` 视为终态。状态标签与通过率口径不变。
- 测试：`tests/task/` 收口与清扫，`tests/bug_ticket/` 登记来源键。
- 不改 `TaskStatus` 枚举，不改报告通过率分母，不自动重试模型或设备错误。
