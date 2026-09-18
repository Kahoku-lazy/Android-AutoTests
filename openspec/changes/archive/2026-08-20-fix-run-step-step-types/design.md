## Context

`run_single_step`（task_views.py:37-55）白名单硬编码旧步骤名；Step 1 后 executor 与 STEP_TYPE_META 均已新名（adb_*）。旧名保留兼容（历史用例仍可能含旧名，StepExecutor 侧亦有别名处理）。

## Goals / Non-Goals

**Goals:**

- 新名步骤可单步调试（白名单与 STEP_TYPE_META 对齐）
- 旧名不回归

**Non-Goals:**

- 不重构 run_single_step 执行链（executor 分发已支持新名）

## Decisions

- 白名单抽 `KNOWN_STEP_TYPES` 模块级常量（可单测）；新名 9 个：adb_start_app/adb_kill_app/adb_perf_element_time/adb_wait_toast/adb_if_appear/adb_if_disappear/adb_loop_n/adb_loop_elements/adb_poll_text
- `package_name` 判定补 adb_start_app/adb_kill_app

## 模块防火墙自检

- 本 App 内部修改；通过

## Risks / Trade-offs

- [白名单与 STEP_TYPE_META 未来再次漂移] → 单测列出期望集合；后续可改为后端 STEP_TYPE_META 派生（另行评估）
