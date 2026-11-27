## 1. 本地 e2e 入口

- [x] 1.1 新增 `utils/run_e2e.py`：`prepare_temp()` / `prepare_browsers()` / `install_browsers()` / `run_pytest()`，支持 `--install` 与透传 pytest 参数。
  验证：`python -m utils.run_e2e --help` 正常；`python -m utils.run_e2e` 能跑完 15 条 e2e。
- [x] 1.2 `.agents/docs/tests/tests_e2e.md` 补「本机 EPERM 的绕法」段（含 `--install` 首次安装说明）。

## 2. 关单

- [x] 2.1 `python -m utils.run_e2e` → `15 passed`。
- [x] 2.2 `python -m ruff check utils/run_e2e.py` + `ruff format --check` 通过。
- [x] 2.3 `python -m run check` 阻塞项 30/30；`openspec validate add-local-e2e-runner` 通过。
