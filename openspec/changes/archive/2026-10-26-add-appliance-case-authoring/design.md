# 设计：家电测试用例编写与验收角色

## Context

见 `proposal.md`。当前 `engines/agents` 已有角色基类与配置（`role/base.py`、`role/config.py`）、提示词目录（`prompts/` + `prompt_config.py` 分配）、SOP 执行者/验收者范式（`workflow/ui_auto_workflow.py`）。SOP 的交付契约是 `_Handover`（一个 `handover` 文本字段），判决契约是 `_Verdict`（`passed` + `message`），最多尝试次数由 `SOPStep.max_attempts` 控制。技能正文在 `engines/agents/skills/common/appliance-test-cases/`。

## Goals / Non-Goals

**Goals**

- 两个角色可独立装配、可成对运行，提示词把技能方法论固化成模型可执行的硬约束。
- 编写角色一次交付完整用例文档；验收角色给出可执行、可回灌的驳回意见。
- 与现有 executor / verifier 链路零耦合。

**Non-Goals**

- 不接后端接口、前端页面、数据库与任务编排。
- 不执行用例、不生成测试报告、不做设备截图或设备日志验收。
- 不替代技能原文，不引入新的用例存储格式。

## Decisions

### D1 提示词自包含，不挂技能加载工具

把五阶段 SOP、8 种方法、复杂度/方法数门槛、13 字段、量化要求直接写进系统提示词，而不是让模型先调用 skill viewer 读技能。理由：流程固定、一次调用完成，避免"模型没读技能就开写"的不确定性。代价是提示词与技能可能漂移，用模块 docstring 声明"技能是维护基准"，并用单元测试锁住关键条款。

### D2 两个角色都不挂工具

需求正文、项目代号、版本号、已有用例索引都由调用方放进开场输入；编写角色只输出文档，验收角色只判卷。理由：文件读取/写入工具会让角色行为依赖宿主环境，且当前 `engines/agents/tools` 没有文件工具；先做纯文本角色，后面要接文件再单独加工具。工具包用 `build_toolkit([])` 构造空 `basic` 组，框架会在结构化输出时自动注入 `GenerateStructuredOutput`。

### D3 复用 SOP 执行者/验收者范式

一个 `SOPStep`：编写角色为 executor，验收角色为 verifier，`max_attempts=2`。驳回时 SOP 清空 submission，把 `message` 原样回灌，编写角色在同一步重写。理由：项目已有该范式，重试与状态语义不需要新造；`CaseAuthoringWorkflow` 只负责装配、事件透传和结果读取。

### D4 两个角色都用 deepseek-flash

用例编写与验收都走 `FLASH`：003 这类大需求单轮生成慢、成本高，统一 Flash 降低等待与费用；二者都不需要图片输入。模型名集中为 `CASE_WRITER_MODEL` / `CASE_VERIFIER_MODEL` 两个常量，后续要换模型只改一处。Agent-02 的 DB `model_name` 由迁移 `0062` 同步为 `deepseek-flash`。

### D5 长文档放 handover

SOP 只接受文本交付，编写角色必须把七节文档全文写进 `handover`，禁止"摘要 + 文件名"。代价是输出 token 较大；通过 `max_iters` 设小（编写 8、验收 4）避免无谓循环。

### D6 角色模块独立

新增 `role/case_roles.py`，不改 `role/agents.py`。现有 executor / verifier 是设备执行链路，工具、提示词、模型预算都不同；分模块避免改一处牵连设备链路。

## Risks / Trade-offs

- [长文档走结构化输出可能触顶] → 提示词要求按模块分节、单表 13 列，禁止重复贴需求原文；后续如仍超限，可拆成"原子表"与"用例表"两个 SOP 步骤。
- [统一用 FLASH，长文档推理可能不如 PRO 稳] → 验收提示词要求逐条核对并按阻断/严重分级；如误判率偏高，把 `CASE_WRITER_MODEL` 换回 `PRO`，只改常量。
- [提示词与技能漂移] → 模块 docstring 写明技能是维护基准；单测锁五阶段、13 字段、方法数门槛、门禁数字等关键条款。
- [需求正文超长触发上下文压缩] → 两个角色无工具、`max_iters` 小，压缩触发面小；调用方负责按模块切分需求。

## Migration Plan

纯新增：部署后不影响既有任务与设备执行链路。回滚时删除新增的提示词、角色、工作流与测试文件，并从 `prompt_config.py` / `tools_config.py` / `workflow/__init__.py` 移除对应导出即可。

## Open Questions

无。
