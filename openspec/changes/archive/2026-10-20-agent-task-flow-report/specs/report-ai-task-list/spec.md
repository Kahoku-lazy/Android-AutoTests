## REMOVED Requirements

### Requirement: Report workbench does not navigate away

**Reason**: 列表行改为进入该任务的事件流程报告，不再停在 `/reports`。
**Migration**: 点击一行进入 `/reports/task/:taskId`。任务编号仍不是 `/reports/:id` 的链接，KPI 仍不进入用例分解。

## ADDED Requirements

### Requirement: Report workbench opens the task flow

测试报告列表 MUST 把任务编号显示为纯文本，MUST NOT 链到 `/reports/:id`。KPI 的通过与失败卡片 MUST NOT 进入用例分解。点击列表中的一行 MUST 进入该任务的事件流程页 `/reports/task/:taskId`。

#### Scenario: Clicking a row opens the task flow

- **WHEN** 用户点击测试报告列表中的一行
- **THEN** 浏览器进入 `/reports/task/` 加上该行的任务编号

#### Scenario: Task id is not a run detail link

- **WHEN** 用户查看列表中的任务编号
- **THEN** 该编号不是指向 `/reports/:id` 的链接
