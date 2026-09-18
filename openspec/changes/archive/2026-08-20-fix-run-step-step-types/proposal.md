## Why

真机验证（浏览器单步调试，场景 6）发现：`POST /api/runner/run-step` 返回 `Unknown step type: adb_start_app`。根因：Step 1 枚举收敛后用例步骤为新名（`adb_start_app` 等，STEP_TYPE_META 唯一真相源），但 `run_single_step` 的硬编码白名单仍是旧名（`start_app` 等）——**Step 1 遗漏的同步点，mock 测试无法覆盖（白名单是字符串面）**。影响：单步调试对新名步骤全部失效。

## What Changes

- `apps/test_runner/views/task_views.py`：白名单抽为模块级常量 `KNOWN_STEP_TYPES`，补 9 个 `adb_*` 新名（与 STEP_TYPE_META 对齐）；`package_name` 判断同步补 `adb_start_app`/`adb_kill_app`
- 新增 `tests/test_runner/test_run_step_types.py`：常量含全部新名、不含未知名、旧名兼容保留
- 真机回归：浏览器单步调试重跑验证（场景 6）

## 关联文档

- 真机验证发现 #3；基线：`2026-08-20-converge-state-enums`（本变更修复其遗漏同步点）
- Bug 修复，无需求级行为变化：`skip_specs: true`

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

## Impact

- `apps/test_runner/views/task_views.py`、`tests/test_runner/test_run_step_types.py`
- 前端零改动
