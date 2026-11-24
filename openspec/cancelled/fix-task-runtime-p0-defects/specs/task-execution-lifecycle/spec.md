# task-execution-lifecycle Delta

## MODIFIED Requirements

### Requirement: 重启后 running 记为中断而不再记失败

服务启动恢复时，遗留的 `running` 任务 MUST 改为 `interrupted` 状态，MUST NOT 记为 `failed`。恢复 MUST 写入中断说明与 `finished_at`，MUST 用平台逐次账（usage ledger）中该任务已入账的费用回写任务费用字段；MUST NOT 依赖已退役的任务事件明细作为费用来源。账本暂不可用时 MUST NOT 阻断收口，费用 MAY 暂记 0 并留下可读说明。

#### Scenario: 遗留 running 变为已中断

- **WHEN** 服务启动时数据库中仍有状态为 `running` 的任务
- **THEN** 该任务状态变为 `interrupted`，`finished_at` 非空，`result` 说明服务重启导致中断
- **AND** 该任务的 `cost_total` 等于平台逐次账中该任务已入账费用之和

#### Scenario: 排队任务仍被拉起

- **WHEN** 某设备存在一条遗留 `running` 与一条 `pending`
- **THEN** 遗留任务变为 `interrupted` 后，该 `pending` 任务仍可被调度为 `running`

#### Scenario: 心跳超时收口同样按账本回写费用

- **WHEN** 运行中任务心跳超过阈值被清扫收口为 `interrupted`，且该任务在账本中已有入账记录
- **THEN** 收口后该任务的 `cost_total` 等于账本中该任务已入账费用之和，MUST NOT 被写为 0

## ADDED Requirements

### Requirement: 工作线程心跳容错

工作线程的心跳 MUST 周期性刷新直到任务进入终态或线程退出。单次心跳写入或状态查询失败（含瞬时数据库故障）MUST 记录错误日志并继续调度下一拍，MUST NOT 因单次异常永久停止心跳。进程真正退出时心跳随之消失，遗留任务仍由既有清扫机制按中断收口。

#### Scenario: 瞬时 DB 故障后心跳恢复

- **WHEN** 运行中任务的某一拍心跳因瞬时数据库错误失败，下一拍时数据库已恢复
- **THEN** 心跳继续刷新，任务保持 `running`，MUST NOT 被清扫机制误收为中断

#### Scenario: 任务终态后心跳停止

- **WHEN** 任务已被写为终态（completed / failed / cancelled / interrupted）
- **THEN** 心跳在下一拍检测到终态后停止调度，不再继续写入