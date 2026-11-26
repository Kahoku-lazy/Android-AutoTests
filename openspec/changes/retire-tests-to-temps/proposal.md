# Proposal: retire-tests-to-temps

## Why

测试资产碎片化到不可维护：`tests/` 的 541 条灰盒/接口/b2b 用例散在 17 个模块目录，`frontend/tests/` 的
89 个 spec（557 条用例）散在 11 个模块目录，两套都靠「按模块建目录 + 手工维护 helpers」演进。
需求方 2026-11-24 决定：把两套**用例层**移出维护面，配置与守门设施留原地，后续用系统化测试重建。

风险评估与实测证据见 `dev_docs/DEV_TEST/REVIEW-测试资产迁移temps风险评估-2026-11-24.md`。
关键事实（实测）：前端 `vite.config.js` 在 **构建期** import `./tests/module-scan.mjs`；`temps/` 在 `.gitignore` 里；
前端 spec 移出 `frontend/` 后 `vue` / `@vue/test-utils` 解析失败；Python 用例 15 处依赖顶层包名 `tests`。

## What Changes

**移出（`git mv`，保留历史；不是复制后删除）**

- `tests/` 下 17 个用例目录（`ai_assistant` `api` `auth` `bug_ticket` `case` `config` `dashboard` `device`
  `knowledge_search` `models` `ops_console` `report` `serial_log` `task` `usage_ledger` `e2e` `api_kit`）
  → `temps/tests-archive/`
- `frontend/tests/` 下 11 个 spec 模块目录（`ai-assistant` `bug-manager` `case-manager` `dashboard`
  `device-pool` `login` `ops-console` `report-generator` `serial-log` `shared` `task-list`）+ `helpers/`
  + `DESIGN-*.md` / `PLAN-*.md` / `PRIORITY_TEMPLATE.md` → `temps/frontend-tests-archive/`

**留仓（守门层，不在本次移动范围）**

- `tests/{pytest.ini, conftest.py, test_settings.py, __init__.py, AGENTS.md, reports/}` 与 `tests/arch/unit/**`（23 个契约守护）
- `frontend/tests/{module-scan,run,generate-html-report,check-style-gates,check-dashed-whitelist}.mjs`、`reports/.gitignore`
  —— 这 5 个是**工具脚本**：`vite.config.js`、`package.json` 的 7 个 `test:*`、2 个 `lint:*` 与 CI 的
  `style-gates` / `dashed-whitelist` 直接调用它们，移走会连带打断 `vite build`

**门禁适配**

- `frontend/package.json`：`test` = `vitest run --passWithNoTests`（**临时假绿**，恢复条件见 design D4）
- `utils/check_gates.py`：不动命令；`pytest-collect` 仍收集 `tests/`（缩到 23 条守护），保持绿
- `tests/arch/unit/test_api_path_callers.py`：去掉 `tests` 与 `yaml` 两个扫描面，只守 `frontend/src`

**规格**

- `api-path-convention`：1 条 MODIFIED requirement（移除「测试调用面」）
- 其余 4 份引用 `tests/arch/unit` 的规格（`auth-form-validation` / `auth-response-shape` / `auth-session` /
  `frontend-doodle-sketched-ui-kit`）不变——守护与 `check-dashed-whitelist.mjs` 都留仓

## 变更申请（AGENTS 红线，按根 `AGENTS.md` §行为规范 第 4 条：先批后改）

| 项 | 内容 |
|---|---|
| **改什么** | ① `tests/AGENTS.md`：红线「只收三类」「禁止新增单元测试」的适用域改为「用例层已于 2026-11-24 迁至 `temps/`，`tests/` 只留契约守护」；② 根 `AGENTS.md` §文档与工具 第 3 条测试入口改为「契约守护：`python -m pytest -c tests/pytest.ini`；用例存档在 `temps/`，不参与 CI」 |
| **为什么必须改** | 不改则两条红线描述一个已空掉的目录：后来者按红线「新增灰盒用例」会与「用例已停维护」直接冲突；根文档的「测试资产全部在 `tests/` 下」在移动后为假 |
| **影响面** | 所有读 AGENTS 的 AI/人（口径源）；CI 两条 gate 的语义（`vitest` 空跑通过、`pytest-collect` 从 541 缩到 23）；`.agents/docs/tests/*.md` 4 篇与 `frontend/tests/README.md` 的命令样例 |
| **怎么回退** | 单个 commit `git revert`；用例回仓 `git checkout <sha> -- tests frontend/tests`（存档目录不受 git 保护，不作为回退源） |

> **未获批准前，本变更只落 proposal/design/tasks，不动代码与文档。**

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `api-path-convention`：`Requirement: 前端与测试调用面遵循唯一写法` 收敛为只约束前端 API 层，
  移除 `tests/` 与 `tests/api/case/*.yaml` 两个扫描面及其 scenario（delta 见 `specs/api-path-convention/spec.md`）

## Impact

- 业务代码：0 行改动
- 测试设施：`frontend/package.json`、`tests/arch/unit/test_api_path_callers.py`、`tests/AGENTS.md`、根 `AGENTS.md`、1 份 spec delta
- CI：python job 收集量 541 → 23（变快）；frontend job 的 vitest 由「跑 557 条」变为「空跑通过」（**净损失**，见 design D4）
- 覆盖净下降：灰盒 0 条、b2b 0 条、前端单测 0 条；仅剩 23 条零 I/O 契约守护
- 不可自动恢复点：存档在 `temps/`（`.gitignore` 声明），`git mv` 保留跟踪但后人 `git add` 新文件会被忽略；存档不保证可运行（design D3）
