## 1. 复核（已完成）

- [x] 1.1 实测 `python -m ruff format --check .` → 20 个文件待重排
- [x] 1.2 范围口径修正：先按 `apps/ config/ gateway/ shared/ models/` 量得 9 个，改用门禁原命令 `.` 后追加发现 `engines/` ×5 与 `tests/` ×6
- [x] 1.3 确认 20 个文件均为**既有债**（`dashboard/ai_usage.py` 等目录不在本会话改动清单内）
- [x] 1.4 确认根因是行宽口径遗留：格式化 diff 主体是「把折行合并回单行」，与 `line-length = 100` 一致
- [x] 1.5 量化改动面：20 个文件合计 **135 增 / 100 删 = 235 行**

## 2. 修改

- [x] 2.1 对 20 个文件运行 `python -m ruff format`（先备份到 `temps/fmt_backup/`）
- [x] 2.2 用「去空白逐字节比对」核对内容：15 个文件 SAME；5 个 DIFF 且全部为格式化构造（尾随逗号 ×3：`rag_service.py` / `element_locator/admin.py` / `test_example_unit.py`；折行括号化 ×2：`workflow/api.py` 的 `if (...)` · `test_device_detector.py` 的 `with (...)`）

## 3. 验证

- [x] 3.1 `python -m ruff format --check .` → **243 files already formatted**（0 待重排）
- [x] 3.2 `python -m ruff check .` → **All checks passed!**
- [x] 3.3 `pytest tests/graybox/unit -q` → **82 passed**；`pytest tests/arch -q` → **6 passed**
- [x] 3.4 `pytest --collect-only -q` → **150 tests collected**（含 `tests/e2e` / `tests/graybox/integration`，证明格式化未破坏任何语法 / import）
- [x] 3.5 `python manage.py check` → 0 issues；范围核对：diff 仅涉这 20 个文件

## 4. 说明

- 格式化前副本保留在 `temps/fmt_backup/`（20 份，临时目录，不随仓库保留），用于回滚与比对复核
