## 1. 枚举定义收敛（models/）

- [x] 1.1 `models/test_models.py`：TestRunStatus 合并为 5 值小写（PENDING/RUNNING/COMPLETED/STOPPED/FAILED），docstring 注明与 TaskOutcome 的映射；新增 `TaskOutcome`（含 `terminal_values()`/`fail_values()`）与 `TaskCardStatus`；验证 `python manage.py check && python -m ruff check models/test_models.py`
- [x] 1.2 `models/constants.py`：删除 `TestRunStatus`/`TestResult`/`QueueStatus`；`DeviceStatus` 收敛 ONLINE/BUSY 两态；验证 `grep -rn "from models.constants import" apps/ models/` 无消费 + `python manage.py check`

## 2. 模型与迁移（apps/test_runner/）

- [x] 2.1 `apps/test_runner/models.py`：`TaskCard.status` choices 改引 `TaskCardStatus.choices()`、`outcome` 改引 `TaskOutcome.choices()`；`makemigrations` 验证：choices 为 callable 不参与反解构，**无需 AlterField 迁移**
- [x] 2.2 手写数据迁移 `0019_backfill_lowercase_run_status.py`（大写→小写幂等回填，含 PASSED/SUCCESS 别名归并）；验证 `python manage.py makemigrations --check` 无残留

## 3. 执行链路枚举化（apps/test_runner/）

- [x] 3.1 `state_machine.py`：`_VALID_TRANSITIONS` 键值引 `TaskCardStatus`/`TaskOutcome`；`dequeue`/`complete`/`fail`/`recover_orphans` 写库改引 `TestRunStatus.*.value`；`fail()` 校验改 `TaskOutcome.fail_values()`，映射表按 L1b §4.1；`repair_queued_terminal_drift` 引 `TaskOutcome.terminal_values()`；验证 `python -m ruff check apps/test_runner/state_machine.py`
- [x] 3.2 `views/execution_steps.py`（255、317-321）、`views/helpers.py`（204/213/216）、`views/ai_execution.py`（76）、`views/execution.py`（316/336）、`recovery_helpers.py`（55）硬编码 outcome/status 改引枚举；验证 `python -m ruff check apps/test_runner/views apps/test_runner/recovery_helpers.py`
- [x] 3.3 `executors/ui/connect.py:55`：删除 OFFLINE/DISCONNECTED 幽灵状态死分支；验证 `python -m ruff check apps/test_runner/executors/ui/connect.py`
- [x] 3.4 核实：`views_drf.py:642` 为 `ai_tasks.status` 过滤（TaskStatus 域），与 tr_test_runs 无关——**无需改动**，登记核实结论

## 4. 基线断言显式更新（tests/）

- [x] 4.1 `tests/test_runner/test_state_machine_baseline.py`：`test_state_machine_writes_uppercase_completed` 改为断言写库 `"completed"`（小写）；`TestRunStatusDualDefinitionAnchor` 改为断言唯一定义（constants 无 TestRunStatus）与 5 值口径；删除"现状行为"注释中已收敛项
- [x] 4.2 新增枚举单元测试：`TaskOutcome.fail_values()` 不含 completed、`TaskCardStatus` 4 值、TestRunStatus↔TaskOutcome 映射（可并入 test_state_machine_baseline.py 或新文件 `tests/test_runner/test_enums_baseline.py`）；验证 `python -m pytest tests/test_runner/ --nomigrations -m "unit or integration" -q`

## 5. 全量门禁与文档同步

- [x] 5.1 全量门禁：`python manage.py check`（0 issues）+ `python -m ruff check models apps/test_runner tests/test_runner`（全过）+ `python -m pytest -m "unit or integration" --nomigrations -q`（**255 passed / 201 deselected**，基线 247 → 255，+8 为新增枚举测试，其余变化为预期断言更新）
- [x] 5.2 架构红线：`--check-boundaries` 零违规；`class TestRunStatus` 仅 `models/test_models.py` 一处；`"COMPLETED"` 大写仅存 `ai_assistant/views_drf.py:642`（ai_tasks 域，合规）；test_runner 内 outcome 硬编码清零
- [x] 5.3 文档同步：L1b 详档 §四/§六 标注"已落地"；Checklist §五 P0 枚举行勾选；本 change 完成说明记录基线对比
