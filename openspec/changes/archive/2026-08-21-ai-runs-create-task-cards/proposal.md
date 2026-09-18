## Why

AI 助手发起的执行任务在"执行引擎"页面没有任何历史记录：8 条 AI 运行都有 `TestRunRecord`，但 `TaskCard` 数量为 0——执行引擎页面（test-runner 模块）展示的是 `GET /runner/tasks` 的任务卡列表，而 AI 执行路径（`start_run` → `_run_ui_for_ai` → `_execute_tests`）从一开始就声明"不含调度/队列/TaskCard"、全程 `client_task_id=""`，绕过了任务卡生命周期。用户因此看不到 AI 发起任务的任何痕迹（用户此前也问过"新建执行任务卡片，执行这条用例"）。

## What Changes

1. **P0** `apps/test_runner/api.py` `start_run`：投递前经 `save_task_card` 创建任务卡（task_id=run_id、名称取用例标题、creator 解析为用户名、mode=immediate、task_type=ui_automation），并在进程内登记 `_run_client_task[run_id]=run_id`；预建的 PENDING 记录 `client_task_id` 同步写入 run_id。
2. **P0** `apps/test_runner/state_machine.py` `dequeue`：改为 `get_or_create`（复用 AI 路径预建的 PENDING 记录升级为 running，保留其 started_at；队列路径行为不变）——避免预建记录与 dequeue 创建撞 `run_id` 唯一约束。
3. **P0** `apps/test_runner/views/ai_execution.py`：`_run_ui_for_ai` 读取 `_run_client_task` 得到真实 client_task_id，传给 `_abort_run_before_execute` 与预检登记——执行前失败时任务卡走 `enqueue→dequeue→fail` 终态（`_abort_run_before_execute` 的 mark_terminal 既有逻辑）。

经此三处，AI 运行完整进入任务卡生命周期：idle → queued → running → done（`_persist_run_start`/`_finalize_run`/`_abort_run_before_execute` 既有的状态机分支全部复用），任务卡携带 outcome/case_items/通过率等历史信息出现在执行引擎任务列表。

无 **BREAKING** 变更。

## 关联文档

- `dev_docs/02-PRD需求/PRD-06-执行引擎.md`（TaskCard 生命周期 / 状态机）
- `apps/test_runner/AGENTS.md`（状态机勿绕过、WS 事件、任务列表 camelCase）
- 现场证据：`tr_task_cards` 计数 0 vs `tr_test_runs` 计数 8（AI 运行）；`test-runner/index.vue` 读取 `GET /runner/tasks`

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

> 缺陷修复：补齐 AI 运行与既有任务卡生命周期的集成，无需求级行为变化，`.openspec.yaml` 已设 `skip_specs: true`。

## Impact

- 后端：`apps/test_runner/api.py`（start_run +~20 行）、`apps/test_runner/state_machine.py`（dequeue 幂等化）、`apps/test_runner/views/ai_execution.py`（+~6 行）
- 数据：修复后每次 AI 执行都会产生 `tr_task_cards` 记录（task_id=run_id），历史可见
- 测试范围：`manage.py check` + ruff + `--check-boundaries`；dequeue 幂等验证（预建记录不再冲突）；真实对话端到端（AI 执行后任务卡出现在任务列表且终态 done/completed）
