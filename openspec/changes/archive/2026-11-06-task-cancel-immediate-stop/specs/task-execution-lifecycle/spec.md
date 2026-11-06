## ADDED Requirements

### Requirement: 取消终态不被工作线程覆盖

任务被用户关闭并写入 `cancelled` 之后，工作线程的收尾 MUST NOT 把终态改写为 `completed`、`failed` 或 `interrupted`；工作线程 MAY 只补充用量与费用字段。取消与正常结束同时发生时，`cancelled` MUST 优先。

#### Scenario: 取消后工作线程恰好跑完

- **WHEN** 用户关闭任务后，工作线程在几秒内恰好完成了整轮运行
- **THEN** 任务终态仍为 `cancelled`，结果说明仍为“用户关闭”
- **AND** 不出现 `completed` 与 `cancelled` 两个终态先后写入的情况

#### Scenario: 取消后工作线程异常退出

- **WHEN** 任务被关闭后工作线程以异常结束
- **THEN** 任务终态仍为 `cancelled`，失败原因不写回任务结果
