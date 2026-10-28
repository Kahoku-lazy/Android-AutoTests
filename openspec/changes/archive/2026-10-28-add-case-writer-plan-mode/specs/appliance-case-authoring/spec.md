## ADDED Requirements

### Requirement: 编写角色用计划模式跟踪五阶段

用例编写角色 SHALL 装配 AgentScope 计划模式工具 `TaskCreate`、`TaskGet`、`TaskList`、`TaskUpdate`，并 MUST 在开始拆解需求前创建计划任务。计划任务 MUST 覆盖至少四个阶段：需求原子拆解、方法匹配与优先级、13 字段用例编写、E2E 与自检；每进入一个阶段 MUST 用 `TaskUpdate` 标记 `in_progress`，完成时 MUST 标记 `completed`。交付七节文档前 MUST 用 `TaskList` 确认没有遗留的 `pending` / `in_progress` 任务。

计划清单只是过程管理，MUST NOT 替代七节文档：最终交付仍 MUST 是完整 Markdown（GoalPipeline 下还必须先保存到模块存储），MUST NOT 用计划摘要、任务列表或“已完成”当作交付正文。

规划角色与验收角色 MUST NOT 装配计划工具；验收角色仍只读文档与模块存储，MUST NOT 修改计划清单。

#### Scenario: 编写角色拿到计划工具

- **WHEN** 创建一个用例编写角色（含 SOP 与 GoalPipeline 两种装配）
- **THEN** 其工具包包含 `TaskCreate`、`TaskGet`、`TaskList`、`TaskUpdate`
- **AND** 规划角色与验收角色的工具包不包含这四个工具

#### Scenario: 编写前先建计划

- **WHEN** 编写角色收到一个模块的需求片段
- **THEN** 在输出需求原子表之前先调用 `TaskCreate` 建立阶段任务
- **AND** 阶段推进时调用 `TaskUpdate` 更新状态
- **AND** 最终交付仍是完整七节 Markdown

#### Scenario: 计划不能当交付

- **WHEN** 编写角色只创建了计划任务、没有产出七节文档
- **THEN** 验收角色按“没有完整用例文档”判不通过
- **AND** 计划清单不得被当作 handover 或模块存储文档

#### Scenario: 验收角色不改计划

- **WHEN** 验收角色判卷
- **THEN** 它没有 `TaskCreate` / `TaskUpdate` 等计划工具
- **AND** 只能读取模块存储文档并给出 `result` / `message`
