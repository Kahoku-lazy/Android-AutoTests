## 1. 复核（已完成）

- [x] 1.1 实测 `python -m ruff check .` → **229 errors**（T201 146 · Q000 58 · I001 20 · F401 5），命令确实红灯
- [x] 1.2 定位来源：224 错在两份 vendored `skill-creator`（`.agents/skills/` 111 + `engines/ai/skills/` 113），5 错在自有代码
- [x] 1.3 确认 `ruff.toml:53` 的 `.claude/skills/**/*.py` 指向不存在路径（旧目录布局残留）
- [x] 1.4 确认 `tools/cli.py` 的 `random` / `string` / `datetime` 三个 import 在文件内无任何其它引用（F401 成立）
- [x] 1.5 纠错：D5-3（`engines/device/connection.py` 直 import uiautomator2）经 `ARCH-00` §1.1 L1c 行核实为**误报**，本单不涉

## 2. 修改

- [x] 2.1 `ruff.toml`：`exclude` 增两份 vendored `skill-creator` 目录
- [x] 2.2 `ruff.toml`：删除 `per-file-ignores` 中 `.claude/skills/**/*.py` 死配置（其上方注释同步去掉 "skill driver"）
- [x] 2.3 `tools/cli.py`：删除未使用的 `random` / `string` / `datetime` import（-4 行，含空行）
- [x] 2.4 `tests/graybox/unit/test_case_manager_ids.py` + `tests/graybox/unit/test_task_progress_persist.py`：`ruff check --fix` 修复 I001

## 3. 验证

- [x] 3.1 `python -m ruff check .` → **All checks passed!**（229 → 0）
- [x] 3.2 `python -m ruff format --check` 改动的 3 个 Python 文件 → 已格式化
- [x] 3.3 `pytest tests/graybox/unit -q` → **82 passed**（与改动前一致，无回归）
- [x] 3.4 `python manage.py check` → 0 issues；范围核对：`git diff --numstat` = ruff.toml 12/4 · tools/cli.py 0/4 · test_case_manager_ids.py 4/1 · test_task_progress_persist.py 1/0

## 4. 遗留（不在本单范围）

- `ruff format --check .` 仍报 9 个既有未格式化文件（`ai_assistant/api.py`、`ai_assistant/rag_service.py`、`dashboard/ai_usage.py`、`element_locator/{admin,api_directories,api_projects,views}.py`、`workflow/{api,serializers}.py`）—— 🟡 格式债，与本单「lint 门禁」不同根因，另行处理
