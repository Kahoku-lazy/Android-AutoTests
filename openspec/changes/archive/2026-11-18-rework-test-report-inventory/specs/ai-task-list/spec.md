# Delta: ai-task-list

## MODIFIED Requirements

### Requirement: Sidebar AI task group exposes task list first

侧栏「AI任务」分组 SHALL 按顺序展示「任务清单」「用例管理」「BUG单管理」「测试报告」，路径 MUST 分别为 `/tasks`、`/cases`、`/bugs`、`/reports`。任务清单入口 MUST 只在 `/tasks` 高亮，MUST NOT 与「AI 助手」入口同时高亮。

#### Scenario: AI task group order

- **WHEN** 用户查看侧栏「AI任务」分组
- **THEN** 自上而下依次为「任务清单」「用例管理」「BUG单管理」「测试报告」

#### Scenario: Task list active state

- **WHEN** 用户位于 `/tasks`
- **THEN** 只有「任务清单」显示激活态，「AI 助手」不显示激活态
