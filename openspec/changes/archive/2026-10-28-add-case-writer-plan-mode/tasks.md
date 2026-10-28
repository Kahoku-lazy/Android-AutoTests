## 1. 计划工具装配

- [x] 1.1 新增 `engines/agents/tools/tool_case_plan.py`，提供 `build_case_plan_tools()` 返回 `TaskCreate` / `TaskGet` / `TaskList` / `TaskUpdate` 四个实例；单测断言四个工具名。
- [x] 1.2 `tools_config.py` 增加 `build_case_writer_toolkit()`，用 `Toolkit(tools=build_case_plan_tools())` 装配；保留 `build_case_authoring_toolkit()` 为空包。
- [x] 1.3 `case_roles._role_config` 增加 `plan_mode` 参数；`build_case_writer` 与 `build_case_writer_goal` 传 `True`，规划/验收不传；单测断言 writer 有四个计划工具、verifier/planner 没有。

## 2. 提示词与轮次

- [x] 2.1 `CASE_WRITER_PROMPT` 在五阶段前增加「计划模式」章节：先建 4~5 个阶段任务、阶段进入/完成更新、交付前 `TaskList` 清账、计划不能替代七节文档。
- [x] 2.2 `CASE_WRITER_GOAL_PROMPT` 补充：计划完成后仍必须先 `save_case_module_document`，再交结构化 `report`。
- [x] 2.3 `CASE_WRITER_MAX_ITERS` 从 8 调整为 20；单测断言提示词包含计划工具名与关键约束。

## 3. 验证

- [x] 3.1 运行 `python -m pytest -c tests/pytest.ini tests/graybox/unit/test_case_authoring_roles.py tests/graybox/unit/test_case_authoring_prompts.py tests/graybox/unit/test_case_plan_tools.py`，全部通过。
- [x] 3.2 运行 `python -m ruff check engines/agents` 与 `ruff format --check engines/agents`，通过。
- [x] 3.3 运行 `python -c` 或单测确认 `TaskCreate/TaskUpdate` 能在 `AgentState` 上读写任务；不启动模型调用。
- [x] 3.4 运行 `openspec validate add-case-writer-plan-mode --strict` 并归档。
