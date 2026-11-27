## Why

本机跑 e2e 时，Playwright 驱动进程抛：

```
EPERM: operation not permitted, mkdtemp 'C:\Users\zhiyan\AppData\Local\Temp\playwright-artifacts-XXXXXX'
```

实测结论（2026-11-27）：

- Python 自己 `tempfile.mkdtemp()` 在 `C:\Users\zhiyan\AppData\Local\Temp` **成功**，`node -e` 也能成功；
- 但 Playwright 通过 Python 启动的驱动进程只能写**工作区**：把 `TEMP` 指到 `D:\Govee\pw-tmp` 仍然 EPERM，
  只有指到 `D:\Github\Android-AutoTests\temps\pw-tmp` 才通过；
- 浏览器目录同理：`%LOCALAPPDATA%\ms-playwright` 连 `__dirlock` 都建不了（`playwright install` 直接失败），
  装到 `temps/pw-browsers` 才成功。

于是「本地 e2e 跑不起来」不是用例问题，而是**临时目录/浏览器目录落在不可写位置**。此前只能靠每条命令手工设
`TEMP` / `PLAYWRIGHT_BROWSERS_PATH`，换一个 shell 就忘。

## What Changes

- 新增 `utils/run_e2e.py`（`python -m utils.run_e2e`）：先创建 `temps/pw-tmp`，把 `TEMP` / `TMP` / `TMPDIR`
  指过去；若 `temps/pw-browsers` 存在且用户没显式设 `PLAYWRIGHT_BROWSERS_PATH`，也一并指过去；然后透传参数调用
  `pytest -c tests/pytest.ini -m e2e`。`--install` 走 `playwright install chromium`。
- `.agents/docs/tests/tests_e2e.md` 的「运行指令」补一段本机 EPERM 的绕法与该脚本用法。

**不改测试用例、不改 pytest 配置、不影响 CI**：CI 仍直接跑 `pytest`，浏览器装在默认目录。

## 关联文档

无 PRD 条目：本地开发/测试工具链修复。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 用例口径与执行方式未变，只是多一个本地入口；`.openspec.yaml` 置 `skip_specs: true`）

## Impact

- **工具**：新增 `utils/run_e2e.py`
- **文档**：`.agents/docs/tests/tests_e2e.md` 一段
- **生产代码/接口**：0
- **本机资产**：`temps/pw-browsers`（约 740MB，已 gitignore）、`temps/pw-tmp`
