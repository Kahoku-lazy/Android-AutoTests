## 1. 用例角色装配移出 workflow

- [x] 1.1 新增 `engines/agents/case_roles.py`：`build_case_authoring_roles(store, *, requirement_text="")` 返回已挂产物工具的 `(writer, verifier)`；编写角色可写、验收角色只读。验证：单测断言两边工具集非空、验收角色不带写入工具。**验证结果**：通过 —— `test_paired_assembly_attaches_artifact_tools` 断言编写侧含 `save_state_machine` / `append_scenarios` / `append_cases`，验收侧含 `read_artifact` / `check_artifact_facts`，且两侧无写入工具交集。
- [x] 1.2 `engines/agents/workflow/case_goal_workflow.py`：改用上述函数，删除 `build_case_writer` / `build_case_verifier` / `build_case_artifact_tools` 三处 import 与四行装配。验证：该文件源码检索这三个名字为 0 命中；`python -m pytest -c tests/pytest.ini tests/graybox/unit/test_case_goal_workflow.py -q` 全绿。**验证结果**：通过 —— 文件内三名字 0 命中（仅 docstring 更新后也不含）；`test_case_goal_workflow.py` 8 passed，`test_case_artifact.py` 16 passed。
- [x] 1.3 新增契约断言：`workflow/` 下任何模块都不得直接调用角色装配入口。验证：新测试文件按 AST 扫描 `engines/agents/workflow/*.py`，命中即失败。**验证结果**：通过 —— `test_workflow_boundary.py` 2 passed；口径为「排除 lambda 内的延迟调用」（设备侧的 `lambda: IncompleteHandoverGuard(build_executor())` 属于转交工厂，允许），函数体里直接 `build_case_writer()` 才判违规。

## 2. 模块「模块功能」修正

- [x] 2.1 逐个改成一句话职责（17 个）：`workflow/case_file.py`、`workflow/platform_run.py`、`workflow/handover_guard.py`、`event_sink.py`、`messaging/messages.py`、`middleware/model_retry.py`、`middleware/rag_context.py`、`middleware/tracing.py`、`rag/config.py`、`rag/chunker.py`、`rag/indexer.py`、`rag/service.py`、`rag/store.py`、`realtime_vocie/config.py`、`realtime_vocie/events.py`、`realtime_vocie/session.py`、`tools/tool_img_b64.py`。验证：`python -m scripts.docstrings check --path engines/agents --include-existing` 的 `module-summary` 归零。**验证结果**：通过 —— 全包 error 由 100 降到 83，`module-summary=0`（其余 83 条是逐函数缺 `Args:` / `Returns:` 等段，见未完成项说明）。

## 3. 文档对齐

- [x] 3.1 根 `AGENTS.md`：技能 → `config/data/skills/`；提示词 → `config/data/prompts/` + `role_sys_prompts.py`；去掉不存在的 `mcp_config/`。**验证结果**：通过 —— 三处均已改；技能一行同时注明「资产已就位，装配入口尚未接上」。
- [x] 3.2 `engines/agents/AGENTS.md`：删除 `mcp_config/` 行，新增 `case_roles.py` 行。验证：检索两处文档中不再出现 `prompt_config.py`、`engines/agents/skills`、`mcp_config/`。**验证结果**：通过 —— 两文件检索均 0 命中。

## 4. 门禁

- [x] 4.1 `python run.py check`；`ruff check` / `ruff format --check engines/` 通过。**验证结果**：部分通过 —— 阻塞项 22/23，唯一失败是 `vue-file-size`：`frontend/src/modules/task-list/components/TaskBoard.vue` 被**未提交的用户改动**改到 503 行（本次未触碰任何前端文件；改前该门禁为 23/23）。`ruff check` 与 `ruff format --check engines/`（120 个文件）通过；`engines-docstring-check` 改动文件 0 error；`engines-agents-style` 仍是既有 22 条。
- [x] 4.2 `openspec validate tighten-agents-review-findings --strict` 通过。**验证结果**：通过（`skip_specs` 生效，零 delta 被接受）。

## 未完成项（另行处理）

- 全包仍有 **83 条** 文档段缺失：`doc-returns=59`、`doc-args=17`、`doc-raises=3`、`doc-summary=3`、`def-docstring=1`（另有 `class-attributes=8` warn）。这些要逐函数读实现补「返回什么 / 参数含义 / 抛什么」，机械补「返回结果」属于假合规，故不在本次（纯注释准确性修正）范围内一并处理。
