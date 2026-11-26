# Proposal: fix-tests-fixture-scope

## Why

全量套件 587 条里有 **62 个 setup error**，全部是同一个根因：

```
tests/api/conftest.py  → api_session / unique_username / admin_login / auth_session
tests/e2e/conftest.py  → frontend_url / e2e_services / e2e_account / login_page / steps / …
```

pytest 的 conftest 只对**自身目录及子目录**生效。测试按模块重组后，用例落在
`tests/auth/api/`、`tests/auth/e2e/`、`tests/device/api/`，而这两个 conftest 的目录
（`tests/api/`、`tests/e2e/`）里**已经没有任何用例**，于是夹具对所有模块用例都不可见：

- 62 条用例直接 `fixture 'api_session' / 'login_page' / 'e2e_account' not found` 报 error；
- 连带的 `tests/e2e/conftest.py` 里两个 hook（失败截图 + 步骤报告）也只在空目录生效，
  **模块 e2e 用例的留痕能力等于零**，而且不报错、无声失效。

CI 的 python job 只跑 `pytest-collect`（不执行用例），所以这个问题一直没被拦住，
但任何人本地跑 `tests/auth`、`tests/device` 都会撞 62 条红。

## What Changes

- 把 `tests/api/conftest.py` 的 4 个夹具与 `tests/e2e/conftest.py` 的 8 个夹具**上提到** `tests/conftest.py`
- 把 `tests/e2e/conftest.py` 的两个 hook（`pytest_runtest_makereport` 失败截图、`pytest_sessionfinish` 步骤报告）一并上提
- 删除 `tests/api/conftest.py` 与 `tests/e2e/conftest.py`（两个目录内已无用例，留空壳会重复注册 hook）
- 同步 `tests/arch/unit/test_api_path_callers.py` 里**唯一一处样例路径**（`tests/api/conftest.py` → `tests/conftest.py`）：
  该守卫拿这个文件当「跨行调用被扫到」的样本，文件搬走后样本自然失效；断言逻辑与扫描器一字未改
- **不改任何用例语义、不改夹具行为、不改 `tests/AGENTS.md` 口径**

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 纯测试夹具作用域修复，无行为规格变更，故 `skip_specs: true`）

## Impact

- 代码：`tests/conftest.py` 增约 90 行；删除 2 个 conftest 文件
- 执行面：`tests/auth` + `tests/device` 的 62 个 error → 0；全量套件基线不新增红
- 风险：hook 全局化后，非 e2e 用例也会进 `pytest_runtest_makereport`；该 hook 只在
  `item.funcargs` 里存在 `steps` / `page` 时才动作，非 e2e 用例两者都没有，等价无操作
- 回退：`git revert` 单 commit 即可（两个 conftest 原文件完整存在于父提交）
