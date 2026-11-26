# Design: retire-tests-to-temps

## Context

见 `proposal.md`（Why/What）与 `dev_docs/DEV_TEST/REVIEW-测试资产迁移temps风险评估-2026-11-24.md`（实测证据）。
本设计只记录「怎么移」与「为何这样移」，不重复动机。

现状约束（全部实测，2026-11-24）：

- `vite.config.js:4` 顶层 `import { scanModules } from './tests/module-scan.mjs'`，`scanModules()` 在 config 加载期执行
  → `frontend/tests/` 整个搬走会让 `vite dev` / `vite build` / `vitest` 一起挂
- `package.json` 有 7 个 `test:*` + 2 个 `lint:*` 脚本直接 `node tests/*.mjs`
- 前端 spec 从 `frontend/` 外运行：不加 `server.fs.allow` 报 `Cannot find module '/@fs/…'`；
  加了之后 `import '@vue/test-utils'` 仍 `Failed to resolve import`（仓库根 `node_modules` 无 `vue`）
- Python 侧 10 个文件 15 处 `from tests.…`，`pytest.ini` 写死 `DJANGO_SETTINGS_MODULE = tests.test_settings`
  → 归档目录里不可能再叫 `tests` 包（与留仓的 `tests/` 同名冲突）
- `.gitignore` 含 `temps/`；`git mv` 进 ignored 目录后文件**仍受跟踪**（实测 `R  tests/a.py -> temps/a.py`）

## Goals / Non-Goals

**Goals**

- 用例层退出维护面与 CI，守门层（契约守护 + 前端工具脚本）留在仓库继续工作
- 移动可机械回退（`git mv` 对称），历史不丢
- 移动后 `python run.py check` 仍能跑完（不因空收集/空跑而红）

**Non-Goals**

- 不重写用例、不修 `js-yaml` 预存失败（该失败随 spec 一起移走）
- 不新建系统化测试骨架（另单）
- 不删除 `tests/arch/unit`、不删前端 5 个工具脚本
- 不做「全量 mv」（`tests/` 连 `pytest.ini`/`arch/unit` 一起搬）——那会把 4 份规格的验收载体一起搬空，另议

## Decisions

### D1 只移「用例层」，留守门层

`tests/arch/unit`（23 条零 I/O 守护）与前端 5 个 `.mjs` 工具留仓。理由：
① 4 份 OpenSpec 规格与 `tests/AGENTS.md` 的「契约守护例外」都指向它们；
② 它们是构建期/CI 的依赖（`vite.config.js`、`package.json`、`check_gates.py`），移走等于把门禁一起关掉；
③ 它们本来就不是「碎片化」的对象——按模块分目录的是用例，不是守护。

代价：`tests/` 目录仍在，用户视角的「根 tests 挪走」只完成到用例层。这是有意为之，见 Open Questions。

### D2 `git mv`，不做「复制 + git rm」

`git mv` 保留 rename 历史，回退是一次反向 `git mv`；`temps/` 虽被 `.gitignore` 声明，但已跟踪文件不受忽略规则影响
（实测见 Context）。**不做** `git rm --cached`：那会让归档目录里的文件既不可 review 也不可 `git checkout` 恢复，
与「评估风险」的结论（R1）冲突。

副作用（必须在 tasks 里写明）：归档目录内**新增**文件会被忽略，将来「往存档里补一条用例」这件事在 git 层面不允许。

### D3 归档 = 冷备，明确声明「不可就地运行」

Python 归档不能就地跑：`tests` 包名被留仓的 `tests/` 占用，`from tests.api_kit …` 会解析到残留目录。
前端归档不能就地跑：`vue` / `@vue/test-utils` 在 `frontend/` 外解析失败（实测 E2/E5）。

因此**不提供**归档 runner，只在归档目录放一份 `README.md` 写明「恢复方法 = 反向 `git mv`；就地运行不支持」。
理由：造一个软链垫片的「能跑」比「明确不能跑」更贵、更容易腐坏，且会诱导后人继续维护存档。

### D4 前端 gate 用 `--passWithNoTests`（临时假绿，带恢复条件）

备选：① 从 CI 与 `build_gates()` 删掉 `vitest` gate —— 不可逆遗忘；② 保留 gate 但让它红 —— 主干长期红；
③ 保留 gate + `--passWithNoTests`（选定）。恢复条件写进 tasks 的**收尾项**：
「当 `frontend/tests/**` 重新出现 spec 时，删除 `--passWithNoTests` 并在 PR 说明里点名」。

### D5 契约守护降级最小化

`test_api_path_callers.py` 只删依赖被移走文件的三个锚点：`TESTS_DIR` / `YAML_CASE_DIR` 的扫描面、
`MIN_PER_SURFACE` 的 `tests`/`yaml` 下限、`AUTH_CALL_FILES` 里的 `tests/api/conftest.py` 与其跨行断言。
`frontend/src` 面（42 条下限）与 `EXCEPTIONS`（指向留仓的 `test_api_path_convention.py`）原样保留。
规格侧只改 `api-path-convention` 一条 requirement，不新增 capability。

### D6 顺序：先移前端、再移 Python、最后改门禁

前端移动后 `vitest` 立刻变红（无文件），所以 `package.json` 改动必须紧跟；Python 移动后 `pytest-collect` 仍有 23 条，
天然是绿的，所以放后面。每步独立可验证，失败只回退一步。

## Risks / Trade-offs

- [覆盖净下降：灰盒/b2b/前端单测归零] → 变更申请里显式写明；恢复条件挂在 D4 与 tasks 6.3
- [归档不可运行 → 将来想「捞回来跑一次」成本高] → 归档 `README.md` 给反向 `git mv` 命令；不提供 runner
- [`temps/` 被清理丢失] → 归档只是工作区副本，回退源是 git 历史；若需长期保存，另行备份
- [D5 删面让守护变窄] → spec delta 明确「测试调用面退出扫描」，并写「系统化测试就位后须重新纳入」
- [团队仍按旧文档跑 `npm run test:p0`] → tasks 5 组同步文档，且 `run.mjs` 保留后该命令仍可执行（只是收集 0 条）

## Migration Plan

1. 基线快照：`pytest -c tests/pytest.ini --collect-only -q`（541）、`npx vitest run`（89 文件 / 557 条）
2. 前端：`git mv` 11 个 spec 目录 + `helpers/` + 4 份 md → `temps/frontend-tests-archive/`；`package.json` 加 `--passWithNoTests`
3. Python：`git mv` 17 个用例目录 → `temps/tests-archive/`；两份归档 `README.md`
4. 守护降级：改 `test_api_path_callers.py`；跑 `pytest -c tests/pytest.ini -q`（应 23 条全绿）
5. 文档与规格：spec delta、`tests/AGENTS.md`、根 `AGENTS.md`、`.agents/docs/tests/*.md`、`frontend/tests/README.md`
6. 验收：`python run.py check` 全绿（`vitest` 空跑、`pytest-collect` 23 条）

**Rollback**：单 commit 内完成，`git revert <sha>` 一步回退；或分组回退 = 反向 `git mv` + 还原 `package.json` /
守护 / 文档。归档目录不承载回退责任。

## Open Questions

- 「根 `tests/` 挪到 `temps/`」是否还包含 `arch/unit` 与 `pytest.ini`？本设计按 D1 只移用例层；
  若需求方要连守护层一起移，需追加 4 份规格的 delta 并接受「无零 I/O 守门」。
- 归档目录保留期限（下个 release 删 / 长期保留）——本变更不设期限，删除另开 change。
