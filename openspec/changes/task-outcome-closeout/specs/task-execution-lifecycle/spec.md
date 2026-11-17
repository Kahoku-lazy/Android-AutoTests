## MODIFIED Requirements

### Requirement: 停机先排空再退出

服务停止时，系统 SHALL 先停止派发新任务，再等待当前所有 `running` 任务结束，之后才退出进程。等待上限 MUST 为 180 秒；没有 `running` 任务时 MUST 立即退出；超过上限 MUST 强制退出。强制退出前，系统 MUST 记录当时仍为 `running` 的任务编号。下次收口时，这些编号 MUST 按 `stop_timeout` 记为 `interrupted`，MUST NOT 记为 `failed`，也 MUST NOT 写成「服务重启」。

#### Scenario: 有任务在跑时等待其结束

- **WHEN** 运维执行 `python run.py stop`，此刻存在 `running` 任务
- **THEN** 后端不再派发新的任务，`stop` 持续等待直到 `running` 归零后才停止进程
- **AND** 等待期间任务状态保持 `running`，不会被提前改写

#### Scenario: 无任务时立即停止

- **WHEN** 运维执行 `python run.py stop`，此刻没有 `running` 任务
- **THEN** 后端直接退出，不产生额外等待
- **AND** 不留下停机超时标记

#### Scenario: 超时强制退出

- **WHEN** 等待达到 180 秒仍有 `running` 任务
- **THEN** `stop` 记录这些任务编号并强制结束后端进程
- **AND** 下次收口时这些任务为 `interrupted`，`cause` 为 `stop_timeout`

### Requirement: 重启后 running 记为中断而不再记失败

服务进程清扫心跳已超时的遗留 `running` 任务时，MUST 改为 `interrupted`，MUST NOT 记为 `failed`。没有停机超时标记时，`cause` MUST 为 `process_lost`，结果说明 MUST NOT 固定写成服务重启。恢复 MUST 写入 `finished_at`，MUST 用事件明细回写该任务已产生的费用。心跳仍在更新的 `running` 任务 MUST 保持 `running`。

#### Scenario: 遗留 running 变为已中断

- **WHEN** 服务进程发现数据库中有心跳已超时、状态仍为 `running` 的任务，且该任务不在停机超时名单中
- **THEN** 该任务状态变为 `interrupted`，`finished_at` 非空，`cause` 为 `process_lost`
- **AND** 该任务的 `cost_total` 等于其模型调用事件费用之和

#### Scenario: 心跳未停不被收走

- **WHEN** 新服务进程启动时，某任务为 `running` 且心跳仍在更新
- **THEN** 该任务保持 `running`
- **AND** 结果不被改写成中断说明

#### Scenario: 排队任务仍被拉起

- **WHEN** 某设备存在一条心跳已超时的遗留 `running` 与一条 `pending`
- **THEN** 遗留任务变为 `interrupted` 后，该 `pending` 任务仍可被调度为 `running`

### Requirement: 取消终态不被工作线程覆盖

任务被用户关闭并写入 `cancelled` 之后，工作线程的收尾 MUST NOT 把终态改写为 `completed`、`failed` 或 `interrupted`。终态写入 MUST 以「当前状态仍为 `running`」为条件；条件不满足时，工作线程 MAY 只补充用量与费用字段，MUST NOT 改写状态和结果。取消与正常结束或异常结束同时发生时，`cancelled` MUST 优先。

#### Scenario: 取消后工作线程恰好跑完

- **WHEN** 用户关闭任务后，工作线程在几秒内恰好完成了整轮运行
- **THEN** 任务终态仍为 `cancelled`，结果说明仍为「用户关闭」
- **AND** 不出现 `completed` 与 `cancelled` 两个终态先后写入的情况

#### Scenario: 取消后工作线程异常退出

- **WHEN** 任务被关闭后工作线程以异常结束
- **THEN** 任务终态仍为 `cancelled`，失败原因不写回任务结果
- **AND** 结果中不出现 `failure_kind`
