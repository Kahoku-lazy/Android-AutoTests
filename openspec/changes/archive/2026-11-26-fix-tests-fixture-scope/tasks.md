# Tasks: fix-tests-fixture-scope

> 格式：**动作 → 完成判据**。

## 1. 上提

- [x] 1.1 `tests/conftest.py` 收编 `tests/api/conftest.py` 的 4 个夹具：`api_session` / `unique_username` / `admin_login` / `auth_session`。
  判据：`pytest --fixtures tests/auth/api` 能列出 `api_session`，且 `tests/api/conftest.py` 已删除。
- [x] 1.2 同文件收编 `tests/e2e/conftest.py` 的 8 个夹具：`frontend_url` / `e2e_services` / `e2e_account` / `e2e_step_report` / `login_page` / `steps` / `login_requests` / `held_login_requests`。
  判据：`pytest --fixtures tests/auth/e2e` 能列出 `login_page` / `steps`。
- [x] 1.3 同文件收编两个 hook：`pytest_runtest_makereport`（失败截图 + 步骤留痕）、`pytest_sessionfinish`（步骤报告）。
  判据：模块 e2e 用例跑完，`tests/reports/e2e/index.html` 存在且含用例标题。
- [x] 1.4 删除 `tests/api/conftest.py` 与 `tests/e2e/conftest.py`（保留 `tests/e2e/{selectors,step_report}.py`）。
  判据：`Get-ChildItem tests -Recurse -Filter conftest.py` 只剩 `tests/conftest.py`、`tests/device/integration/`、`tests/ops_console/api/` 三份。

## 2. 验证

- [x] 2.1 62 个 setup error 归零。
  实测：`.venv\Scripts\python.exe -m pytest -c tests/pytest.ini -q -p no:deepeval tests/auth tests/device`
  → **90 passed / 2 failed / 0 error**（基线为 62 error、其余用例根本跑不起来）。
- [x] 2.2 全量复跑并与基线逐项比对。
  判据：`error` 归零（基线 62）；`failed` 允许**上升**——原来被 setup error 掩盖的用例现在会真跑，
  每一条新增失败都要给出归因（已见 2 条：`/api/auth/me/` 响应比 jsonschema 多 `is_operator` / `is_assistant_author`；
  `test_update_status_protects_busy_device` 断言 1 == 0，基线里本来就是红的）。

## 3. 门禁与关单

- [x] 3.1 CI 门禁：python 20 条 + frontend 10 条（`utils/check_gates.py --only …`）。
  判据：两批全 PASS。
- [x] 3.2 记录本次修复与复验数字。
  判据：`dev_docs/DEV_TEST/DEV-测试夹具作用域修复-2026-11-26.md` 写明根因、改法、62 → 0 的前后账。
  备注：`REVIEW-测试基线红清单-2026-11-26.md` 随 `add-page-load-perf-budget` 的 PR 提交，本单不动该文件（避免两笔 PR 同时新增同一文件冲突），
  待两单合并后再把「已修」段回填到基线与清单。

## 4. 环境备注（不属本单，避免下次再踩）

- 本机 Python playwright 需要 `chromium_headless_shell-1255`，而 `%LOCALAPPDATA%\ms-playwright` 里只有 1228/1234，
  且该目录 ACL 拒绝写入（`EPERM mkdir __dirlock`）。本次用
  `PLAYWRIGHT_BROWSERS_PATH=temps\ms-playwright` 装到项目内可写目录后，e2e 全部可跑。
  另可选 `--browser-channel chrome` 复用系统 Chrome。
