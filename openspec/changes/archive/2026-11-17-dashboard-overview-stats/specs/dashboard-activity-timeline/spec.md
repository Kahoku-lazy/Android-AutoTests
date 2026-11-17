## MODIFIED Requirements

### Requirement: Activity feed lists workflow tasks

活动条目 MUST 只由工作流任务（`assistant_sop`）构成，`type` MUST 为 `run`，并按 `time` 倒序排列。系统 MUST NOT 再返回已下线智能体的更新条目，MUST NOT 再查询已删除的测试执行表，MUST NOT 把已退役的设备执行或用例编写任务写入活动流。窗口上限 MUST 为 100 条，分页在该窗口内切片。每条 MUST 含 `type`、`action`、`time`（`YYYY-MM-DD HH:MM`）；`detail` MAY 省略。

#### Scenario: Task card appears as a run activity

- **WHEN** 存在一条工作流任务
- **THEN** 活动数组中出现 `type` 为 `run` 的条目
- **AND** `action` 含该任务标题（无标题则用目标或「未命名任务」）

#### Scenario: Agent update remains an agent activity

- **WHEN** 历史数据中仍有已下线智能体的更新记录
- **THEN** 活动数组中不出现 `type` 为 `agent` 的条目

#### Scenario: Retired task kinds do not appear

- **WHEN** 同时存在工作流任务与已退役的设备执行或用例编写任务
- **THEN** 活动数组只含工作流任务

## RENAMED Requirements

- FROM: `### Requirement: Activity feed merges assistant tasks and agent updates`
- TO: `### Requirement: Activity feed lists workflow tasks`
