## 1. 修复

- [x] 1.1 `task_views.py`：白名单抽 `KNOWN_STEP_TYPES` + 补 9 个 adb_* 新名；`package_name` 判定补新名；验证 `python manage.py check && python -m ruff check apps/test_runner/views/task_views.py`
- [x] 1.2 新增 `tests/test_runner/test_run_step_types.py`（unit）：新名全含、旧名兼容、未知名不含；验证 `python -m pytest tests/test_runner/test_run_step_types.py -m unit --nomigrations -q`

## 2. 回归

- [x] 2.1 全量后端：`python -m pytest -m "unit or integration" --nomigrations -q`（基线 308 + 3 白名单单测 = **311 passed**）
- [x] 2.2 真机：run-step 返回 `status=true, result=pass`，真机前台切到 `com.govee.home` ✅（UI 层连接态受 observe 占用残留影响另行处理，修复核心已验证）
