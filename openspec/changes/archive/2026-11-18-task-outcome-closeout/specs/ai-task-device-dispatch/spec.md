## MODIFIED Requirements

### Requirement: 重启后遗留任务记为中断并恢复排队

系统 SHALL 只把心跳已超时的遗留 `running` 任务标记为 `interrupted`，MUST NOT 标记为 `failed`，也 MUST NOT 收走心跳仍在更新的 `running` 任务。没有停机超时标记时，结果 MUST 说明进程退出导致终态未写回，MUST NOT 固定写成服务重启。恢复 MUST 写入 `finished_at`，MUST 用该任务的模型调用事件合计回写 `cost_total`，然后按设备尝试启动各设备上最早的 `pending` 任务。

#### Scenario: 重启后遗留 running 变为已中断并拉起 pending

- **WHEN** 服务进程发现某设备有一条心跳已超时的遗留 `running` 与一条 `pending`
- **THEN** 遗留 `running` 落 `interrupted`，`cause` 为 `process_lost`
- **AND** 该 `pending` 可被调度为 `running`

#### Scenario: 旧进程仍在心跳

- **WHEN** 新服务进程启动时，某设备的 `running` 任务心跳仍在更新，且同设备还有 `pending`
- **THEN** 该 `running` 任务保持 `running`
- **AND** 该 `pending` 任务在这条任务结束前不得被拉起
