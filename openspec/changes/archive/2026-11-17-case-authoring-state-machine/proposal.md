# 用例编写改为「状态机 → 业务流场景 → 边界/场景用例」三段式

## Why

现有用例编写流水线产出的是「七节 Markdown + 13 字段用例表」，它面向人工评审：产物里没有设备执行工作流需要的页面锚点与日志证据字段，两份工作流无法闭环；同时为了绕开「一次生成整篇长文档」的输出上限，堆了模块规划、截断递归二分、第六节统计回写、全文重发重写等五套兜底，两个角色、两套引擎、两套近乎重复的提示词。把产物换成「状态机 → 场景 → 用例」三段结构化数据、交付改成增量工具、编排收敛到一条 GoalPipeline，可以同时解掉复杂度与不可执行两个问题。

## What Changes

- **BREAKING** 编写产物改为三段式结构化数据：需求状态机（states / transitions）→ 业务流场景（状态机路径）→ 边界与场景法用例；Markdown 文档与 Mermaid 状态图由平台**渲染生成**，不再由模型一次性写出。
- **BREAKING** 验收口径收窄为两条：用例数据是否与需求一致、是否存在自推测或捏造。删除旧门禁全部条目（七节结构、13 字段完整性、方法数下限、P0 占比、E2E 条数、原子覆盖率、模糊词、第六节统计回写）。
- **BREAKING** 编排收敛为单一目标流水线（GoalPipeline）：执行者=用例编写、验证者=用例验收；删除 SOP 双轨与 `CASE_AUTHORING_ENGINE` 开关，删除模块规划角色，角色数 5 → 2。
- **BREAKING** 取消需求模块切分与输出截断拆分：编写角色通过增量工具（保存状态机 / 追加场景 / 追加用例）分次交付，单次输出天然有界。
- 新增确定性事实预检：每个状态、迁移、场景、用例的 `source` 必须是需求原文的子串；用例引用的状态与场景必须已声明；用例中的数值必须能在其 `source` 里找到。预检结果作为工具交给验收角色，并写入任务结果。
- 任务结果结构变化：移除 `modules` 与 `truncated`，新增 `artifact`（三段产物）、`facts`（预检结论）与渲染后的 `document`。

## 关联文档

- 无独立 PRD 编号：本变更重写的是用例编写方法与产物契约，依据为既有规格 `appliance-case-authoring`、`appliance-case-authoring-task` 与本次讨论。
- 现状问题清单：`dev_docs/DEV_TEST/UI自动化 问题记录.md`（「用例与锚点」一节记录设计产物与执行输入不闭环）。
- 外部依据：AgentScope 2.0.11 目标流水线（GoalPipeline，执行者/验证者 + 结构化输出 + 驳回重做）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `appliance-case-authoring`: 编写产物契约（七节/13 字段 → 三段式结构化）、验收口径（八组清单 → 事实两条）、编排（双轨 + 规划角色 → 单一 GoalPipeline）、模块切分与截断机制（删除）
- `appliance-case-authoring-task`: 任务执行编排（两角色、无规划）、`Task.result` 结构（modules/truncated → artifact/facts）、用例入库来源（Markdown 解析 → 结构化产物）

## Impact

- **engines**：`workflow/case_authoring_workflow.py`（删除 SOP 分支后大幅收缩）、`workflow/case_goal_workflow.py`（改为单流水线，保留 GoalPipeline）、`workflow/case_module_plan.py`（删除规划与切分）、`workflow/case_document_check.py`（换成事实预检）、`tools/tool_case_module_store.py`（换成产物增量存储）、`tools_config.py`、`agent_builders.py`、`config/data/agent_config.yaml`（角色 5 → 2）、`prompts/CASE_WRITER_PROMPT.md` 与 `CASE_VERIFIER_PROMPT.md`（重写，Goal 变体删除）
- **backend**：`task_list/task_runner.py`（结果映射与入库来源）、`task_list/task_reports.py`（用例编写报告字段）、`case_manager/api_import.py`（落库字段）
- **前端**：用例编写任务的结论区（三段计数与判决）；不改设备任务页面
- **测试**：`tests/graybox/unit/test_case_authoring_modules.py`、`test_case_authoring_roles.py`、`test_case_authoring_prompts.py`、`test_case_goal_workflow.py`、`test_case_document_check.py`、`test_case_authoring_task_runner.py` 需重写；新增事实预检与产物存储测试
- **兼容**：用例库中已有的 44 条用例与历史任务结果按 legacy 保留，不做数据迁移；新任务一律按新结构产出
- **非目标**：不生成设备执行用的结构化用例 YAML，不改设备执行工作流（另立变更）
