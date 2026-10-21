## MODIFIED Requirements

### Requirement: 可见任务的事件流程

系统 SHALL 通过 `GET /api/tasks/{id}/report/` 返回当前用户可见任务的事件流程，响应 MUST 使用标准信封 `{status, data}`：`data` 含 `task`、`rounds`、`cases`、`conclusion`，业务负载 MUST NOT 自带 `status` 字段。`cases` MUST 按用例列出步骤、用例结果和该用例下的轮次。任务不存在、编号无效或当前用户不可见时 MUST 返回 404，错误体为 `{status: false, message}`。该接口 MUST 只读，MUST NOT 写业务表。该接口 MUST 由 DRF 视图提供，使 `GET` 方法出现在 OpenAPI 基线的 `/api/tasks/{task_id}/report/` 下。

#### Scenario: 返回已完成任务的流程

- **WHEN** 当前用户打开自己可见的任务 115 的流程
- **THEN** 响应 `status` 为真，`data.task` 含标题、状态、设备、用例、助手、起止时间与费用，`data.rounds` 按时间排列，`data.cases` 给出用例与步骤
- **AND** 响应顶层不再出现平铺的 `task` / `rounds` / `cases` 字段

#### Scenario: 他人任务不可见

- **WHEN** 另一个普通用户请求同一任务编号
- **THEN** 响应为 404，响应体为 `{status: false, message}`
