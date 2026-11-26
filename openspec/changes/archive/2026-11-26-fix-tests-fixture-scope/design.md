# Design: fix-tests-fixture-scope

## Context

- 目录重组提交 `3d39e44d test(layout): 补齐按模块重组后的测试，修复搬迁遗留` 把用例按模块铺开，
  但 `tests/api/conftest.py`、`tests/e2e/conftest.py` 留在原地；两个目录从此没有用例
- pytest 的 conftest 作用域 = 目录子树，**没有向上继承**
- 基线证据见 `dev_docs/DEV_TEST/REVIEW-测试基线红清单-2026-11-26.md`：62 error（auth.api 38 / auth.e2e 15 / device.api 9）
- 模块级 conftest 已有三个（`tests/device/integration/`、`tests/ops_console/api/`、`tests/perf/`），它们只在各自子树用，不动

## Goals / Non-Goals

**Goals**

- 一份夹具定义、全子树可见，且只有一份（不复制）
- 模块 e2e 用例重新拿到失败截图与步骤报告
- 修完可量化：`tests/auth` + `tests/device` 62 error → 0

**Non-Goals**

- 不重构夹具本身（懒初始化、账号复用策略、超时值都不动）
- 不新增用例、不改 `tests/AGENTS.md` 口径、不动 `tests/api/__init__.py` 等包标记
- 不处理基线里另外 25 个 failure（属 `fix-assistant-log-report-id-404` 等在制单）

## Decisions

### D1 上提（move），不是复制

复制会在两个位置各留一份，日后改一处漏一处；而且 `tests/api/conftest.py` 与
`tests/e2e/conftest.py` 所在目录没有用例，留着只会让人误以为还有本地夹具。

### D2 hook 必须一起上提

只搬夹具不搬 hook，模块 e2e 用例依旧拿不到失败截图与步骤报告，且**不会报错**——
这是最难发现的一类失效。上提后 hook 对全仓生效，但两个 hook 都自带守卫：

- `pytest_runtest_makereport`：`item.funcargs.get("steps")` / `get("page")` 为 `None` 时直接 return
- `pytest_sessionfinish`：`report.cases` 为空时直接 return

### D3 删除原 conftest，不留空壳

`tests/e2e/` 仍要保留 `selectors.py` / `step_report.py`（模块，被 hook 与用例引用），
但两个 `conftest.py` 必须删——否则 hook 会被注册两次（截图截两遍、报告写两遍）。

### D4 保持「谁用谁在自己的子树」的既有分工

`tests/device/integration/conftest.py`（`detector` / `registry` / `state_machine`）与
`tests/ops_console/api/conftest.py`（`operator_group` / `normal_user` / `admin_user`）继续留在原处：
它们只在对应子树被用，上提反而污染全局命名空间（两处都定义了 `admin_user`）。

## Risks / Trade-offs

- [hook 全局化影响非 e2e 用例] → 两个 hook 都有 `funcargs` / `report.cases` 守卫，非 e2e 走空分支
- [上提后 `allure` / `playwright` 成为 root conftest 的硬依赖] → 二者本就在 `requirements.txt`，
  且 CI 装全量依赖；`tests/perf/conftest.py` 早已在顶层 import playwright
- [夹具同名冲突] → 已核对：上提清单与模块级 conftest 无重名（`admin_login` 与 `admin_user` 是不同夹具）

## Migration Plan

1. 上提夹具与 hook 到 `tests/conftest.py`，删除两个旧 conftest
2. 验证 `tests/auth` + `tests/device`：62 error → 0
3. 复跑全量，与基线（25 failed / 62 errors）逐项比对，确认没有新增红

**Rollback**：`git revert <sha>`，两个 conftest 原文件在父提交里完整存在。
