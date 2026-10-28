## 1. 提示词

- [x] 1.1 `engines/agents/prompts/case_writer_prompt.py`：新增 `CASE_WRITER_PROMPT`，覆盖五阶段 SOP、8 种方法、L1-L4 方法数门槛、P0/P1/P2 校准、13 字段、七节输出结构、增量模式与交付前自检。验证：导入常量且关键条款测试通过。**验证结果**：提示词测试 5 项全绿（`test_case_authoring_prompts.py`）。
- [x] 1.2 `engines/agents/prompts/case_verifier_prompt.py`：新增 `CASE_VERIFIER_PROMPT`，覆盖 A-H 八组验收清单、通过门禁、`[阻断|严重|建议]` 驳回归、禁止放水清单与"只验收设计"边界。验证：导入常量且关键条款测试通过。**验证结果**：同上，A-H、门禁数字与驳回格式均在断言内。

## 2. 装配

- [x] 2.1 `engines/agents/prompt_config.py`：导入并导出 `CASE_WRITER_PROMPT` / `CASE_VERIFIER_PROMPT`，补分配注释。验证：`from engines.agents.prompt_config import ...` 成功，`__all__` 含两项。**验证结果**：`test_prompt_config_exports_case_prompts` 通过。
- [x] 2.2 `engines/agents/tools_config.py`：新增 `build_case_authoring_toolkit()`，返回不含任何工具的 `Toolkit`。验证：构造出的工具包只有 `basic` 组且无工具。**验证结果**：`tool_groups` 为 `['basic']`，`tools == []`（两个角色装配测试）。
- [x] 2.3 `engines/agents/role/case_roles.py`：新增编写/验收角色工厂，`vision=False`、编写与验收模型均为 `deepseek-flash`、轮次 8/4，每次新工具包；迁移 `0062` 同步 Agent-02 的 DB model_name。验证：两个工厂返回的角色名、系统提示词、模型、轮次与工具包符合预期。**验证结果**：`test_build_case_writer_*` / `test_build_case_verifier_*` 通过，两个模型常量分别断言为 `deepseek-flash`。
- [x] 2.4 `engines/agents/workflow/case_authoring_workflow.py`：新增 `CaseAuthoringResult`、`CaseAuthoringWorkflow`、`build_run_input`、`run_case_authoring`，一个 SOP 步骤最多两次尝试。验证：`build_run_input` 含四段输入并对空需求抛 `ValueError`；结果对象 `passed` 取最后一次判决，驳回后仍保留草稿。**验证结果**：5 项输入/结果/草稿断言通过；`CASE_MAX_ATTEMPTS=2`。
- [x] 2.5 `engines/agents/workflow/__init__.py`：导出新增的工作流入口，更新模块说明。验证：`from engines.agents.workflow import run_case_authoring` 成功。**验证结果**：`test_workflow_package_exports_case_authoring_entry` 通过。

## 3. 验证

- [x] 3.1 `tests/graybox/unit/test_case_authoring_prompts.py`：锁两份提示词的关键条款、导出关系与禁止放水边界。验证：`python -m pytest tests/graybox/unit/test_case_authoring_prompts.py -q` 全绿。**验证结果**：5 passed。
- [x] 3.2 `tests/graybox/unit/test_case_authoring_roles.py`：锁角色装配、工具包、输入拼装、草稿保留与结果对象。验证：`python -m pytest tests/graybox/unit/test_case_authoring_roles.py -q` 全绿。**验证结果**：7 passed。
- [x] 3.3 静态检查：改动文件 `ruff format --check` 与 `ruff check`。验证：全部通过。**验证结果**：`engines/` 52 files already formatted；`All checks passed!`。
- [x] 3.4 规格校验：`openspec validate add-appliance-case-authoring --strict`。验证：通过。**验证结果**：`Change 'add-appliance-case-authoring' is valid`。
