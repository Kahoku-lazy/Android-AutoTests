## 1. 删除零消费符号（D0-1~4）

- [x] 1.1 删除 `config/agentscope_config.py`（62 行死模块）。验证：文件已不存在；全仓 grep `agentscope_config` **0 命中**（含删除前最后一次复测亦为 0）
- [x] 1.2 删除 `config/settings.py` 的 `# ── AgentScope ──` 整块（5 个符号）。验证：`AGENTSCOPE_SERVICE_{PORT,URL,TITLE,VERSION}` + `AGENTSCOPE_WORKSPACE_DIR` 在 `config/settings.py` 及全仓均 **0 命中**
- [x] 1.3 删除 `AIRTEST_ENABLED`（含注释行）与 `SCREENSHOT_INTERVAL`。验证：两者在 `config/` 及全仓 **0 命中**；`DEVICE_SERIAL` / `SERVER_PORT` 保留（各有真实消费）

## 2. 文档同步

- [x] 2.1 ARCH-00 §七「关键开关（环境变量）」移除 `AIRTEST_ENABLED` 行。验证：`ARCH-00` 内 `AIRTEST_ENABLED` **0 命中**

## 3. 验证与关单

- [x] 3.1 `python manage.py check`。验证：**System check identified no issues (0 silenced)**，exit 0
- [x] 3.2 `python -m ruff check config/`。验证：**All checks passed!**，exit 0（注：`ruff` 裸命令不在 PATH，须用 `python -m ruff`）
- [x] 3.3 `$env:PYTHONIOENCODING="utf-8"; python tools/gen_arch_stats.py --check-boundaries`。验证：**✅ 模块边界检查通过 — 零违规**，exit 0（该编码要求为既有门禁缺陷，见 D0 检测的 P1 项，不在本变更范围）
- [x] 3.4 全符号终检（8 个）。验证：`agentscope_config` · `AGENTSCOPE_SERVICE_{PORT,URL,TITLE,VERSION}` · `AGENTSCOPE_WORKSPACE_DIR` · `AIRTEST_ENABLED` · `SCREENSHOT_INTERVAL` 全仓**逐个 0 命中**（本地 `.env` 被 gitignore，不在搜索范围）
- [x] 3.5 运行相关测试。验证：`pytest tests/arch -q` → **6 passed**；`pytest -m "unit or integration" -q` → **1 failed / 65 passed**，失败项 `test_case_manager_ids.py::test_next_case_id_increments_same_day`（`cm_test_definitions.file_id` NOT NULL）经 `git stash` 还原 `config/settings.py` 后**同样失败** → **既有问题，与本次删除无关**
- [x] 3.6 `openspec validate remove-dead-d0-config --strict`。验证：Change is valid
