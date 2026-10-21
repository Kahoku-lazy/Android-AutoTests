## 1. 用例循环：失败不终止整批

- [x] 1.1 `engines/agents/workflow/platform_run.py`：`_drive_real` / `_drive_stub` 改为维护 `completed` / `failed` 两个清单，非 `completed` 只记失败并继续下一条，`cancelled` 立即返回；新增 `_finished()` 汇总失败标题
- [x] 1.2 `run_platform_sop` 结果字典补齐 `failed` 键（`_fail` / `_succeeded` / `_cancelled` 同形），`status` 在有失败时为 `fail`
- [x] 1.3 `backend/apps/task_list/task_runner.py` 把 `failed` 清单写进任务结果载荷；`python -m pytest -c tests/pytest.ini tests/graybox/unit/test_case_run_continuity.py` 通过

## 2. 执行者轮次预算 60

- [x] 2.1 `_build_role` 增加 `max_iters` 参数，`_drive_real` 给执行者传 60、验收者传 30；`RoleSpecConfig` 默认值仍为 30
- [x] 2.2 新增断言：执行者常量与装配处均为 60，`RoleSpecConfig.max_iters` 默认仍是 30；`python -m pytest -c tests/pytest.ini tests/graybox/unit/test_forced_handover_thinking.py tests/graybox/unit/test_case_run_continuity.py` 通过

## 3. 交卷拦截

- [x] 3.1 新增 `engines/agents/workflow/handover_guard.py`：`handover_self_declares_incomplete()` + `IncompleteHandoverGuard`（包装 `AgentLike`，命中未完成措辞回灌继续指令，最多 2 次，超限放行）
- [x] 3.2 `platform_run._drive_real` 用 guard 包住执行者；回灌不改变步骤序号/尝试序号
- [x] 3.3 新增 `tests/graybox/unit/test_handover_guard.py`：正常交卷只调一次内层、命中断言回灌、超限放行、交互事件透传；pytest 通过

## 4. 提示词：加载语义与 handover 措辞

- [x] 4.1 `engines/agents/prompts/executor_prompt.py`：把“加载超过 10s 即终止”限定为页面整体加载；新增长按/连接加载圈等待规则；handover 禁止“尚未/未完成/请下一步”收尾
- [x] 4.2 扩写 `tests/graybox/unit/test_role_prompt_guardrails.py`：断言上述两条措辞；pytest 通过

## 5. 门禁与归档

- [x] 5.1 `python -m ruff check --no-cache` 与 `python -m ruff format --check --no-cache` 通过；定向回归全通过（新增 20 项、受影响 `tests/engines/agents` 13 项）
- [x] 5.2 `python run.py check` 22/22 阻塞项通过；`openspec validate case-execution-continuity --strict` 通过；全量 `unit or integration` 44 项失败与 HEAD 基线逐条一致（新增失败 0，通过数 354 → 369）
- [x] 5.3 归档变更并提交
