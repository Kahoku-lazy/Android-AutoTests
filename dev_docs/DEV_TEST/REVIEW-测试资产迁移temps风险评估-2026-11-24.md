# 测试资产迁入 temps/ 风险评估（py tests/ + frontend/tests/）

> 结论先行版。所有数字来自 2026-11-24 本机实测，命令与输出见「证据」节。
> 评估对象：把根 `tests/`（pytest，126 个受控文件）与 `frontend/tests/`（vitest，104 个受控文件）
> 移到 `temps/` 下，配置留在原地。

## 一、30 秒结论

**能跑，但不是「mv 完就能跑」，而是「移完默认全挂、且必须改 4 类配置 + 6 处规格口径」。**

更关键的是：`temps/` 在 `.gitignore` 里（`temps/` 一行）。所以「移到 temps」= **230 个受控测试文件退出仓库**，
不是「换个目录继续守」。这已经不是目录整理，是一次**测试策略变更**：要么走 OpenSpec + 变更申请，
要么把「移走」改成「留仓但冻结」。

- 移走前守门能力：Python 541 条用例可收集（CI 只收集不执行）；前端 89 个 spec / 557 条用例**真实执行**（当前 88 过、1 挂，见证据 E1）。
- 移走后默认状态：pytest 空收集 `exit 5`（证据 E4）、vitest 无文件 `exit 1`（证据 E3）、前端 `vite build` 直接崩（`vite.config.js` 构建期 import `./tests/module-scan.mjs`）。
- 修复成本：至少 5 项代码/配置补丁 + 2 个 CI gate 改口径 + 6 处规格与文档改口径 + 1 份 `tests/AGENTS.md` 红线变更申请。

## 二、Python 侧：为什么「挪过去默认不能跑」

现状基线：`DJANGO_SETTINGS_MODULE=tests.test_settings`（`tests/pytest.ini:2`）、`testpaths=.`（:4）、
统一入口是根 `AGENTS.md` §文档与工具 第 3 条 `python -m pytest -c tests/pytest.ini`。

四个硬断点：

| # | 断点 | 事实 | 移走后后果 |
|---|---|---|---|
| P1 | 包名 `tests` 硬编码 | 10 个文件 15 处 `from tests.…` 绝对导入（`api_kit.loader`、`e2e.conftest`、`ops_console/api/_helpers` 等）；ini 里也写死 `tests.test_settings` | 移到 `temps/tests/` 后模块名变 `temps.tests.*`（`temps/__init__.py` 存在），`import tests` 解析不到 → 收集期 ModuleNotFoundError |
| P2 | rootdir / testpaths 语义漂移 | `-c tests/pytest.ini` 的 rootdir 由 ini 位置决定，`testpaths=.` 相对 rootdir | 配置留在 `tests/`、用例搬走 → `testpaths` 指向空目录；实测空目录收集 `exit 5` |
| P3 | 契约守护反向依赖 `tests/` | `tests/arch/unit/test_api_path_callers.py:16` 硬编码 `REPO_ROOT/"tests"`，`rglob` 扫 HTTP 字面量，并断言 `tests/api/conftest.py` 存在、`"tests": 32` 条下限 | 用例搬走 → 契约守护扫到 0 条，断言失败；而 **5 份 OpenSpec spec 正是引用这批守护做验收** |
| P4 | 相对 CWD 的产物路径 | `tests/e2e/step_report.py:20` `Path("tests/reports/e2e")` | 不崩（parents=True 建目录），但报告落到空壳 `tests/reports/`，与新位置脱节 |

可用的补救（若坚持移）：在 pypytest 侧加包名垫片 —— `pytest.ini` 增 `pythonpath = ../temps`（相对 rootdir）
或根 `conftest.py` 里 `sys.path.insert(0, "temps")`，让 `tests` 这个名字重新解析到 `temps/tests`；
`arch/unit` 的 `TESTS_DIR` 改成指向新路径。**这不是「配置不用动」，而是「配置必须动，且动的是导入契约」。**

## 三、前端侧：默认更糟，连 build 都会被带崩

现状基线：`npm test` = `vitest run`；`vite.config.js:4` `import { scanModules } from './tests/module-scan.mjs'`；
`test.projects` 用 `scanModules()` 生成 `include: tests/${module}/${prio}/**`。

三个硬断点：

| # | 断点 | 事实 | 移走后后果 |
|---|---|---|---|
| F1 | `vite.config.js` 构建期依赖 `frontend/tests/module-scan.mjs` | 配置文件顶层 import，`scanModules()` 在 config 加载时执行 | 整个 `frontend/tests` 搬走 → config 解析失败 → `vite dev` / `vite build` / `vitest` **三件事一起挂**（CI 的 vite-build、vitest 两个 gate 同时红） |
| F2 | vitest 读 root 之外的文件要先开白 | 实测：`include: ['../temps/…']` 能被收集，但报 `Cannot find module '/@fs/…/x.spec.ts'`；加 `server.fs.allow: ['..']` 后才能加载（证据 E5） | 不改 config 直接 `Cannot find module` |
| F3 | root 外文件解析不到前端依赖 | 实测 `import '@vue/test-utils'` 从 `temps/…` 解析失败（仓库根 `node_modules` 无 `vue`/`@vue/test-utils`；`node probe.mjs` 同样 ERR_MODULE_NOT_FOUND，证据 E2） | 89 个 spec 几乎全要 `vue` / `@vue/test-utils`，全量红；除非给前端依赖做 alias 或建 `node_modules` 软链（Windows/CI 上很脆） |

附带：`frontend/tests/` 里还住着 4 个**工具脚本**（不是用例），`package.json:14-28` 与 CI gate 直接调用：
`check-style-gates.mjs`（style-gates）、`check-dashed-whitelist.mjs`（dashed-whitelist）、
`run.mjs`（7 个 `test:*` 脚本）、`module-scan.mjs`（vite config）。
「移走测试代码」如果不加区分，会把这 4 个 gate 一起搬走 → CI 前端 job 至少 3 个 gate 变红。

## 四、治理风险（比技术风险更硬）

| 风险 | 依据 | 影响 |
|---|---|---|
| R1 测试退出版本控制 | `.gitignore` 含 `temps/` | 230 个受控文件从仓库消失；回退只能靠 git 历史（`git checkout <sha> -- tests frontend/tests`） |
| R2 CI 由「绿」变「红」或「假绿」 | `.github/workflows/ci-phase1.yml:43`（pytest-collect）、`:79`（vitest） | 要么 gate 红，要么被迫把两条 gate 关掉 → 之后合入的代码零测试信号 |
| R3 6 份规格变成空话 | `openspec/specs/api-path-convention`、`auth-form-validation`、`auth-response-shape`、`auth-session` 均写 `tests/arch/unit` 守护；`frontend-doodle-sketched-ui-kit:93` 写 `frontend/tests/check-dashed-whitelist.mjs` 白名单 | 规格里 SHALL 的验收载体不存在；必须走 OpenSpec change 改 delta，否则后续 `openspec` 校验与实现脱节 |
| R4 触到 AGENTS 红线 | `tests/AGENTS.md` 的「只收三类 / 禁止新增单元测试 / 契约守护例外」是子目录 AGENTS 红线；根 `AGENTS.md` 第 3 条写死测试入口 | 按根 `AGENTS.md` §行为规范 第 4 条：**改任何 AGENTS.md（含各级子目录）红线必须先进变更申请**，不得先改后报 |
| R5 本地质量门禁失效 | `utils/check_gates.py:431`（pytest-collect）、`:446`（vitest）、`:28`（ruff scope `tests/`） | `python run.py check` 会红；ruff 对不存在目录只告警不失败（实测 exit 0），不构成保护 |
| R6 文档口径 6+ 处过期 | `AGENTS.md:35`、`.agents/docs/apps/self_test_and_checks.md`（10+ 条命令）、`.agents/docs/tests/*.md`（4 篇）、`frontend/tests/README.md` | 命令照抄即失败，后来者按文档跑不起来 |

## 五、证据（本机实测，2026-11-24）

- E1 vitest 基线：`cd frontend; npx vitest run` → `Test Files 1 failed | 88 passed (89)`，`Tests 557 passed`，
  失败项是**预存问题**：`tests/task-list/p0/yaml-case-titles.spec.ts` → `Failed to resolve import "js-yaml" from src/modules/task-list/helpers/yaml-case-titles.ts`。
  即：动之前就不是全绿，别把这条算到迁移账上。
- E2 root 外模块解析：`temps/…/probe.mjs` → `vue FAIL ERR_MODULE_NOT_FOUND` / `@vue/test-utils FAIL ERR_MODULE_NOT_FOUND`；
  同一文件放 `frontend/tests/` → 两者 `OK`。
- E3 vitest 无匹配文件：`npx vitest run nonexistent-pattern-xyz` → `exit=1`（`--passWithNoTests` 未开）。
- E4 pytest 空目录：`pytest -c tests/pytest.ini temps/probe-move/empty --collect-only` → `no tests collected`，`exit=5`。
- E5 前端 root 外收集：临时 config `include: ['../temps/probe-move/outside/**/*.spec.ts']`
  → 无 `server.fs.allow`：`Cannot find module '/@fs/…'`；加 `fs.allow: ['..']` 后 alias-only 用例 **1 passed**，
  但 `import '@vue/test-utils'` 的用例仍 `Failed to resolve import`。
- E6 pytest 现状：`pytest -c tests/pytest.ini --collect-only -q` → `541 tests collected`，exit 0。

（探针文件全部在 `temps/probe-move/` 下，评估完已可整目录删除；未改动 `tests/`、`frontend/tests/` 任何文件。）

## 六、三个可选方案

### 方案 A：真移出（用户原意）
`git mv tests temps/tests`、`git mv frontend/tests temps/frontend-tests`，配置留原地。必须同时做完：
1. `tests/pytest.ini` 增 `pythonpath` 垫片（或根 `conftest.py` 注入 `temps`）；`arch/unit` 的 `TESTS_DIR` 改新路径。
2. `frontend/vite.config.js`：`module-scan.mjs` 留在 `frontend/tests/`（或改 import 路径）；`server.fs.allow: ['..']`；
   为 `vue`/`@vue/test-utils` 等前端依赖加 alias，或在 `temps/frontend-tests/` 建 `node_modules` 软链。
3. `frontend/package.json` 的 7 个 `test:*` 脚本与 2 个 lint 脚本改路径；CI 的 `vitest` gate 加 `--passWithNoTests` 前先决定它算不算通过。
4. `utils/check_gates.py`：`pytest-collect` 指向新 inifile、`vitest` gate 口径、`ruff` scope 加 `temps/`（否则迁出去的代码无人格式化）。
5. 6 份 OpenSpec spec + 5 篇 AGENTS/文档改口径；`tests/AGENTS.md` 红线先提交变更申请。
6. 回退策略：保留迁移 commit 的 sha，`git checkout <sha> -- tests frontend/tests` 一键回滚（`temps/` 里的副本不受 git 保护，不能当回退源）。

代价：测试停摆期间 CI 无信号；`temps/` 无备份、无 review、无历史。

### 方案 B：留仓冻结（推荐）
不搬目录，把「碎片化」问题按 `tests/AGENTS.md` 已有口径收口：
- 现有 541 + 557 条用例打 `frozen` marker（pytest `-m "not frozen"` 默认不跑；vitest 用独立 project 关掉），CI 只跑白名单；
- 新建 `tests/system/`（或 `tests/<module>/api|integration|e2e` 按现行三类）作为系统化测试的落点，旧用例只读不改；
- 下一个 release 再物理删除，删除时 OpenSpec 与文档同步改，一次变更申请覆盖「冻结 + 最终删除」。
代价：目录暂时更胖；但测试资产留在版本控制、CI 信号不中断、规格不用改。

### 方案 C：先移「非资产」再谈
只把 `frontend/tests/` 里**确属过程产物**的部分（`DESIGN-*.md`、`PLAN-*.md`、`PRIORITY_TEMPLATE.md`、`reports/`）
移到 `temps/`，用例与工具脚本（4 个 `.mjs`）留仓。风险≈0，可立刻做，但不解决「碎片化」主诉。

## 七、需要决策的 4 件事

1. 选 A / B / C 哪条？A 必须配一份「测试策略变更」OpenSpec change + AGENTS 红线变更申请。
2. 若选 A：迁移期间 CI 的 `vitest` / `pytest-collect` 是「改成 passWithNoTests 假绿」还是「暂时摘掉 gate 并记录」？
3. 若选 A：`temps/` 是不可 review、不可回退的目录，是否需要同步把副本放一份到 `dev_docs/DEV_TEST/`（仍不入库）/ 或者打 tag？
4. 若选 B：`frozen` 标记的判定与退出条件（什么算「系统化测试就位」）由谁定？
