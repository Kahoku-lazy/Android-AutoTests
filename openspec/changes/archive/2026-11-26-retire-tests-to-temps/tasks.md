# Tasks: retire-tests-to-temps

> 每条 = **动作 → 完成判据**。0 组是硬门控：未获批准，1 组以后一行不动。
> 全程单分支单 commit（分支命名 `chore/retire-tests-to-temps`），便于 `git revert` 一步回退。

## 0. 前置（硬门控）

- [ ] 0.1 **变更申请获批**：`proposal.md` §变更申请 四要素（改什么/为什么/影响面/怎么回退）经需求方确认。
  判据：需求方回复批准原话记入本文件末尾（或 PR review approve）。
- [ ] 0.2 基线快照：`pytest -c tests/pytest.ini --collect-only -q` 得 541；`cd frontend; npx vitest run` 得
  `1 failed | 88 passed (89)` / `557 passed`（既有 `js-yaml` 失败，属预存，随本变更移出）。
  判据：两行数字与本节一致，记入 PR 描述。
- [ ] 0.3 工作区干净度确认：`git status --short` 的既有改动（backend/apps 等无关修改）**不纳入**本次 commit。
  判据：本变更的 `git add` 只列 `tests/` `frontend/tests/` `frontend/package.json`
  `tests/arch/unit/test_api_path_callers.py` `openspec/**` `AGENTS.md` `tests/AGENTS.md` `.agents/docs/tests/**`。

## 1. 前端用例移出（先做，因 vitest 会立刻变红）

- [ ] 1.1 `git mv frontend/tests/{ai-assistant,bug-manager,case-manager,dashboard,device-pool,login,ops-console,report-generator,serial-log,shared,task-list} temps/frontend-tests-archive/tests/`
  （逐目录 `git mv`，不要 `git add -A`）。判据：`git status --short` 全为 `R`；`Get-ChildItem frontend/tests` 只剩 5 个 `.mjs` + `reports/`。
- [ ] 1.2 `git mv frontend/tests/helpers`、`DESIGN-batch2-3modules.md`、`DESIGN-module-classification.md`、
  `PLAN-batch2-3modules.md`、`PLAN-module-classification.md`、`PRIORITY_TEMPLATE.md` 进同一归档目录。
  判据：`frontend/tests` 无 `*.md`（`README.md` 除外，见 5.4）。
- [ ] 1.3 写 `temps/frontend-tests-archive/README.md`：说明冷备、不可就地运行（`vue`/`@vue/test-utils` 解析失败）、
  恢复命令 `git mv temps/frontend-tests-archive/tests/* frontend/tests/`。
  判据：文件存在且含恢复命令。
- [ ] 1.4 `frontend/package.json` 的 `test` 改 `vitest run --passWithNoTests`。
  判据：`cd frontend; npm test` 退出码 0，且输出 `No test files found`（而非 exit 1）。

## 2. Python 用例移出

- [ ] 2.1 `git mv` `tests/` 下 17 个用例目录到 `temps/tests-archive/`（同名保持相对路径）：
  `ai_assistant api api_kit auth bug_ticket case config dashboard device e2e knowledge_search models ops_console report serial_log task usage_ledger`。
  判据：`git status --short` 全 `R`；`Get-ChildItem tests` 只剩 `AGENTS.md conftest.py pytest.ini test_settings.py __init__.py reports arch`。
- [ ] 2.2 `git mv tests/arch/unit` 保持原位（不动），核对 `tests/` 不含任何 `test_*.py` 之外的用例目录。
  判据：`Get-ChildItem tests -Recurse -Filter "test_*.py"` 的 23 个结果全在 `tests/arch/unit` 下。
- [ ] 2.3 写 `temps/tests-archive/README.md`：冷备、**不可就地运行**（顶层包名 `tests` 与留仓目录冲突）、
  恢复命令 `git mv temps/tests-archive/* tests/`。
  判据：文件存在。
- [ ] 2.4 收集量核对：`pytest -c tests/pytest.ini --collect-only -q` 应为 23（原 541）。
  判据：退出码 0 且数字为 23。

## 3. 门禁核对（不改命令，只验证）

- [ ] 3.1 `python run.py check` 中 `pytest-collect` 通过（23 条）。
- [ ] 3.2 `python run.py check` 中 `vitest` 通过（空跑）。
- [ ] 3.3 `ruff-format` / `ruff-lint` 通过：`RUFF_SCOPES` 仍含 `tests/`（只剩 `arch/unit` 与 4 个根文件），
  归档目录不在 scope（`temps/` 本不在）。
  判据：3.1–3.3 三条 gate 全绿；`git diff utils/check_gates.py` 为空。

## 4. 契约守护降级

- [ ] 4.1 `tests/arch/unit/test_api_path_callers.py` 删除 `TESTS_DIR` / `YAML_CASE_DIR` 两个扫描面及
  `_scan_call_sites("tests", …)` 调用、`MIN_PER_SURFACE` 的 `tests`/`yaml` 项、`AUTH_CALL_FILES` 的
  `tests/api/conftest.py` 与其跨行断言；保留 `frontend` 面（下限 42）与 `EXCEPTIONS`。
  判据：`grep -n "tests/api\|YAML_CASE_DIR" tests/arch/unit/test_api_path_callers.py` 无命中；
  `pytest -c tests/pytest.ini tests/arch/unit -q` 全绿。
- [ ] 4.2 确认另 22 个守护无 `tests/` 路径依赖：`grep -rn "REPO_ROOT / \"tests\"" tests/arch/unit` 仅 0 命中。
  判据：0 命中。

## 5. 文档与规格

- [ ] 5.1 delta spec `openspec/changes/retire-tests-to-temps/specs/api-path-convention/spec.md`：
  MODIFIED「前端与测试调用面遵循唯一写法」收敛为前端面，删「接口测试用例」scenario。
  判据：`openspec validate retire-tests-to-temps --strict` 通过。
- [ ] 5.2 `tests/AGENTS.md`：红线 1/2 的适用域加「用例层已于 2026-11-24 迁至 `temps/`」；「迁移记录」增本条目
  （含回退命令）。**本条属红线措辞变更，须 0.1 已获批**。
  判据：`Select-String tests/AGENTS.md -Pattern "2026-11-24"` 命中迁移记录；红线原文未被删，只加限定。
- [ ] 5.3 根 `AGENTS.md` §文档与工具 第 3 条：改为「契约守护 `python -m pytest -c tests/pytest.ini`（`tests/arch/unit`）；用例存档在 `temps/`，不参与 CI」。
  判据：`Select-String AGENTS.md -Pattern "测试统一入口"` 行不再声称「测试资产全部在 tests/ 下」。
- [ ] 5.4 `.agents/docs/tests/*.md` 4 篇 + `frontend/tests/README.md`：命令样例改指向现存路径或标注「用例已移出」。
  判据：`grep -rn "tests/<模块>" .agents/docs/tests frontend/tests/README.md` 的命中处均有「已移出」标注。
- [ ] 5.5 评估报告回填实施结果：在 `dev_docs/DEV_TEST/REVIEW-测试资产迁移temps风险评估-2026-11-24.md` 末尾加
  「实施结果」节（日期、commit、收集量、留下的门禁）。
  判据：小节存在且数字与 2.4/3.x 一致。

## 6. 验收与收尾

- [ ] 6.1 `python run.py check` 全绿（阻塞项无红）。
  判据：命令退出码 0。
- [ ] 6.2 `git status --short` 与本变更文件清单一致，无 `git add -A` 带入的无关文件。
- [ ] 6.3 **恢复条件登记**：在 `proposal.md` 与 PR 描述写明「`frontend/tests/**` 重新出现 spec 时删除
  `--passWithNoTests`」「系统化测试就位后把用例面重新纳入 `test_api_path_callers` 扫描」。
  判据：两处文本存在。
- [ ] 6.4 PR：分支 `chore/retire-tests-to-temps` → `Kahoku`，标题 `chore(tests): 用例层迁出至 temps，保留配置与契约守护`；
  PR 描述贴基线 vs 终态数字与回退命令。
  判据：PR 创建且 CI 两个 job 全绿。
