## 1. 模块存储与工具

- [x] 1.1 新增 `tools/tool_case_module_store.py`：`ModuleStore`、保存/读取工具、只读授权。验证：单测。**验证结果**：3 个模块存储/GoalPipeline 单测通过；真实模块写入 20K 字符文档后可被验收角色读取。
- [x] 1.2 `tools_config.build_case_module_store_tools` 按角色装配写/读工具。验证：GoalPipeline 冒烟。**验证结果**：写入/读取工具均进入角色 toolkit，未触发人工授权。

## 2. GoalPipeline 单模块

- [x] 2.1 新增 Goal 版编写/验收提示词与角色：保存全文、report 摘要、读存储判卷、result/message。验证：prompt/角色单测。**验证结果**：prompt 与角色单测通过；真实任务事件流可见 `save_case_module_document`、`read_case_module_document` 与 `result/message` 判决。
- [x] 2.2 新增 `workflow/case_goal_workflow.py`：单轮 GoalPipeline、判决捕获、外层最多 3 轮、截断兜底。验证：单测 + 真实模块。**验证结果**：真实小模块跑完 3 轮，判决捕获 3 条；无文档时按截断处理。
- [x] 2.3 `run_case_authoring_modules` 默认走 GoalPipeline，`CASE_AUTHORING_ENGINE=sop` 可回退。验证：模块流水线单测。**验证结果**：默认 goal 路径进入 GoalPipeline；SOP 回退测试保持通过。

## 3. 验证与归档

- [x] 3.1 相关单测全绿。验证：pytest。**验证结果**：GoalPipeline/模块/提示词/角色/task runner 共 38 passed。
- [x] 3.2 真实 Agent-02 任务跑通 GoalPipeline 路径，事件流可见 save/read/verdict。**验证结果**：任务 166/169 的事件流已出现保存、读取、fail 判决与下一轮读取；两次任务均在第二轮被后端热重载打断（外部进程在改仓库），尚未形成 completed 终态。
- [ ] 3.3 `python run.py check` 与 `openspec validate add-goal-pipeline-module-pool --strict`。**验证结果**：变更校验 valid；门禁 17/22，失败项为 `openapi-schema` / `openapi-coverage`（knowledge-assistant 新接口）与 `prettier` / `prettier-ts`（knowledge-assistant、ai-assistant 既有文件），均不在本变更范围；`ruff format engines/agents` 已全过。
- [x] 3.4 归档变更。
