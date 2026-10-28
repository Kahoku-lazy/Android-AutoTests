# 用 GoalPipeline 模块池替换单模块 SOP

## Why

单模块「编写 + 验收」现在用 SOP 的 handover 交付全文。大 PRD 的模块文档动辄 20~40K token，handover 会把全文重新输出一遍，既顶到单次输出上限，也让验收只能看作者自述。SOP 的 `max_attempts` 还把「模型没有给出合法结构化输出」和「内容被驳回」混在同一个预算里，空交付会白白吃掉一次尝试。

GoalPipeline 的执行者/验证者协议更贴合这个循环：执行者交 `report`，验证者按 `result`/`message` 判；`max_retries` 与 `max_iters` 分开；验证者每轮可重置上下文。

## What Changes

- 新增 `ModuleStore` 与 `save_case_module_document` / `read_case_module_document` 工具：编写角色把完整七节文档写进任务级存储，最终 `report` 只写摘要；验收角色从存储读实际文档，不采信 `report`。
- 单模块改用 `GoalPipeline`：`max_iters=1`（单轮只判一次，外层最多 3 轮），`max_retries=3`（结构化输出失败不计入真实驳回），`verifier_reset_context=True`。
- 外层重跑：失败后把上一版文档 + 验收意见拼进下一轮输入，最多 3 轮；文档缺失/过短按截断处理，继续走模块拆分。
- 保留 SOP 作为回退：`CASE_AUTHORING_ENGINE=sop` 时走原 `CaseAuthoringWorkflow`，默认 `goal`。
- 工具放在 `tools/tool_case_module_store.py`，由 `tools_config.build_case_module_store_tools` 装配。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `appliance-case-authoring`：单模块执行从 SOP 改为 GoalPipeline + ModuleStore；新增模块文档存储要求。

## Impact

- 引擎：新增 `tools/tool_case_module_store.py`、`workflow/case_goal_workflow.py`、Goal 版提示词与角色；`tools_config` 增加模块存储工具装配。
- 任务层无接口变化；`CASE_AUTHORING_ENGINE` 可回退到 SOP。
- 测试：模块存储、GoalPipeline 结果映射、提示词与角色。
- 无数据库迁移。
