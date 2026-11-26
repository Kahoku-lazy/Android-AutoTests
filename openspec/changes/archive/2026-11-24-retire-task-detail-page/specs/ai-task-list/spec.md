## Purpose

任务清单页的卡片契约：卡面展示哪些字段、失败/运行中卡提供哪些操作、是否提供详情入口。

## MODIFIED Requirements

### Requirement: Task list card content and actions

任务清单页的单张任务卡 MUST 展示标题（无标题时用目标）、状态、创建时间、设备、助手名、费用、耗时与附件名。失败任务卡 MUST 提供「重新执行」，运行中任务卡 MUST 提供「关闭」。任务卡 MUST NOT 提供「详情」入口，也 MUST NOT 跳转 `/tasks/:id`——该路由已下线，与 `dashboard-agent-tasks` 的「MUST NOT 进入已下线的 `/tasks/:id`」口径一致。任务卡 MUST NOT 展示目标全文。

#### Scenario: Card fields

- **WHEN** 用户查看任务清单中的一张任务卡
- **THEN** 卡面可见标题、状态、创建时间、设备、助手、费用、耗时与附件名，且不展示目标全文

#### Scenario: Failed and running actions

- **WHEN** 任务卡状态为失败或运行中
- **THEN** 失败卡可见「重新执行」，运行中卡可见「关闭」

#### Scenario: Detail navigation

- **WHEN** 用户查看任务卡并尝试进入详情
- **THEN** 卡面没有「详情」入口，页面不跳转 `/tasks/:id`
- **AND** 任务卡的激活点击只停留在 `/tasks`
