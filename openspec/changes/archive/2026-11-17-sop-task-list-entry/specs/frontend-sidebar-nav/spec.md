## ADDED Requirements

### Requirement: AI任务分组以任务清单开头

侧栏「AI任务」分组 MUST 以「任务清单」为第一项，路径 MUST 为 `/tasks`。该项 MUST 只在 `/tasks` 高亮，MUST NOT 与「AI 助手」同时高亮。本次 MUST NOT 新增第二套任务页面。

#### Scenario: 第一项进入已有任务清单

- **WHEN** 用户点击侧栏「AI任务」分组的「任务清单」
- **THEN** 路由进入已有的 `/tasks`，页头为「任务清单」

#### Scenario: 激活态不串到助手

- **WHEN** 用户位于 `/tasks`
- **THEN** 只有「任务清单」显示激活态，「AI 助手」不显示激活态
