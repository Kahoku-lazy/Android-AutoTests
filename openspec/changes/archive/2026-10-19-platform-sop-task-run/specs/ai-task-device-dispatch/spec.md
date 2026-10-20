## MODIFIED Requirements

### Requirement: 同设备串行异设备并行
系统 SHALL 以任务记录上已解析的 `device_serial` 为调度键。当某设备已有状态为 running 的任务时，新提交到该设备的任务 MUST 保持 pending 并按创建时间先进先出等待。当两台任务的设备 serial 不同时，系统 SHALL 允许二者同时为 running。系统 MUST NOT 在同一设备上并行启动两条 running 任务。running 任务进入 completed、failed 或 cancelled 后，系统 MUST 按创建时间拉起该设备上最早的 pending 任务。不同智能体提交到同一设备时 MUST 仍共用这一条队列。

#### Scenario: 同设备第二条任务排队
- **WHEN** 设备 A 上已有一条 running 任务，用户再提交一条指定设备 A 的任务
- **THEN** 新任务状态为 pending，且在先任务进入 completed、failed 或 cancelled 之前不得变为 running

#### Scenario: 异设备可以并行
- **WHEN** 设备 A 上有一条 running 任务，用户提交一条指定设备 B 的任务且 B 上没有 running 任务
- **THEN** 指定设备 B 的任务可以立即变为 running

#### Scenario: 前序结束后拉起排队任务
- **WHEN** 设备 A 上 running 任务进入 completed、failed 或 cancelled，且该设备仍有 pending 任务
- **THEN** 系统按创建时间最早者将该 pending 任务变为 running 并开始执行

#### Scenario: 关闭运行中的任务后拉起下一条
- **WHEN** 用户把设备 A 上的 running 任务关闭为 cancelled，且该设备还有一条更早创建的 pending 任务
- **THEN** 该 pending 任务变为 running 并开始执行
