# Tasks: repo-wide-python-docstring

> 每批只改模块头 docstring，diff 里出现非 docstring 行即为不合格（见 design D7）。
> 验证命令统一在仓库根执行；检查器命令先 `cd .agents/skills/engines-docstring-check`。

## 0. 前置与口径固化

- [x] 0.1 记录现状基线：`python -m temps.measure_docstring_scope` 输出在册 465 / 达标 91，与 `design.md` Context 表一致（临时脚本用完即删）
- [x] 0.2 Django 排除清单落到检查器常量 `EXCLUDED_FILE_NAMES` / `EXCLUDED_FILE_PATTERNS` / `EXCLUDED_DIR_SEGMENTS`，并用反例验证：`backend/apps/accounts/api.py`（排除）、`backend/apps/case_manager/api_rows.py`（排除）、`backend/apps/device_pool/pool.py`（纳入）、`engines/ae_harness/agents/models.py`（纳入，Django 名只在 backend/ 下生效）

## 1. 规范正文

- [x] 1.1 新增 `.agents/rules/python-docstring-style.md`：4 字段模板 + 字段取值 + 纳入/排除两栏表 + tests 口径 + 检查命令；验证：与检查器常量逐项对照无差异（`selftest` 的范围判定表覆盖 4 条边界）
- [x] 1.2 改写 `.agents/rules/engines-code-style.md` §1/§2 为指针，§6 标题范围从 `engines/agents/**` 改为 `engines/ae_harness/tools/**`，§8 加修订说明；验证：该文件内不再定义模板正文
- [x] 1.3 根 `AGENTS.md`「文档与工具说明」加一行指路到新规范；验证：路径存在且一行
- [x] 1.4 `engines/AGENTS.md` 的「AI 阅读与检查流程」补一段：全仓注释正文位置 + 工具函数条款保留；验证：链接可达

## 2. 检查器与门禁

- [x] 2.1 `scripts/docstrings.py` 增加 `in_scope()` / `exclusion_reason()`，`_module_rules` 改判 `in_scope`；验证：`check --path backend/apps/accounts/api.py` 只提示跳过、不报 `module-fields`
- [x] 2.2 `--all` 改为扫全仓在册文件，`--repo` 保留为兼容空开关，新增 `--summary`；验证：`check --all --summary` 打印 `files_in_scope / files_excluded / 按规则计数`
- [x] 2.3 更新 `.agents/skills/engines-docstring-check/SKILL.md`：范围、排除清单、新命令、工具函数条款；验证：文档内命令逐条可执行（`--all --summary`、`--path utils`、`read --changed`）
- [x] 2.4 `python -m scripts.selftest`：补充「非 engines 路径同样触发 module-fields」「Django 固定文件不触发」「engines 的 models.py 不受 Django 名排除」「空壳 `__init__` 豁免」等合成用例；验证：22/22 通过
- [x] 2.5 `utils/check_gates.py` 增加非阻塞门禁 `python-module-docstring`（`check --all --summary`）；验证：`python -m utils.check_gates --only python-module-docstring` 退出码 0、输出计数

## 3. 试点批（批次 1）

- [x] 3.1 `utils/**` 26 个文件模块头改写（含 `utils/linting/**`、`utils/service_ctl/**`）；验证：`check --path utils` 0 error
- [x] 3.2 根 `run.py`、`run_daphne.py` 模块头改写（`manage.py` 按 D1 排除）；验证：`check --path run.py` / `--path run_daphne.py` 均 0 error
- [x] 3.3 `engines/ae_harness/tools/case_library/__init__.py`、`engines/ae_harness/tools/document/__init__.py` 补齐 4 字段；验证：`check --path engines` 0 error（91 个全扫、0 排除）
- [x] 3.4 回归：`python -m pytest -c tests/pytest.ini tests/arch/unit -q` 中与本变更相关的用例通过（4 个失败 + 9 个 PermissionError 已在 HEAD 干净工作树复现，属既有环境/存量问题，见收口说明）；`python -m utils.check_gates --only linting,boundary,engines-agents-style,python-module-docstring` 两个阻塞项 PASS

## 4. tests 批（批次 2）

> 范围变化（2026-11-24 12:06，`97de4e96`）：测试口径收敛为「灰盒 + b2b + `arch/unit` 契约守护」，
> `tests/**/unit/` 的 118 个单元用例迁至 `temps/tests-unit-archive/`。因此本批从 255 个文件缩到 **118 个**；
> 归档用例在 `temps/` 内，按 D3 的排除清单**不纳入**本规范（临时目录随时整体删除）。

- [x] 4.1 按二级目录切子批（ai_assistant / arch / auth / ops_console / serial_log / device / knowledge_search / task / case / e2e / 其余小目录），每子批 ≤30 文件
- [x] 4.2 每个测试文件：`模块功能`=守什么行为（沿用作者原句）、`Python 调试`=`python -m pytest -c tests/pytest.ini <文件>`、`测试`=`1. 覆盖 <被测模块>`（走 HTTP 的用例按 `tests/<模块>` → 应用映射兜底）
- [x] 4.3 全部完成后 `check --path tests` 0 error（118 个在册、0 排除）；`pytest --collect-only -q tests` 541 collected；`pytest tests/arch/unit` 4 failed（与 HEAD 干净树同 4 条，属既有问题）

## 5. backend 批（批次 3）

- [x] 5.1 `backend/**` 非固定结构 91 个按 app 切子批（ai_assistant / bug_manager / dashboard / device_pool / knowledge_search / report_generator / serial_log / task_list / usage_ledger / config / gateway / models / shared）——实际待迁移 58 个，其余 33 个是空壳 `__init__.py`（豁免）
- [x] 5.2 每子批验证：`check --path backend --summary` = 91 在册 / 232 排除（Django 脚手架）/ 0 error
- [x] 5.3 全部完成后 `check --all --summary` = 328 在册 / 0 error / 0 files_with_issues

## 6. 收口

- [x] 6.1 **工具函数注释保真校验**：`check --path engines/ae_harness/tools` 11 个文件、`tool-docstring` / `tool-summary` / `tool-args` 全 0；本轮只补了 `save_authored_case` 缺失的 `Args:`（4 个参数各一行），未删改任何工具说明
- [x] 6.2 `npx openspec validate repo-wide-python-docstring --strict` 通过
- [x] 6.3 全仓 `check --all --summary` 0 error；相关门禁全 PASS：`django-check` / `ruff-format` / `ruff-lint` / `makemigrations-check` / `pytest-collect` / `boundary` / `linting` / `engines-agents-style` / `python-module-docstring`（阻塞项 7/7、告警项 2/2）；前端门禁不在本单范围（未跑）
- [x] 6.4 临时脚本与中间产物已删除（`temps/` 下本轮新建的 `measure/pilot/inventory/apply/verify` 脚本与 txt 全部清掉；`git status` 不再有本轮临时文件）
- [ ] 6.5 PR 说明附：每批 `git diff --stat`、检查器计数前后对比、排除清单最终版；并声明工作区原有的 8 个在途改动不在本单范围
