# ai-task-device-dispatch Specification

## Purpose

按已解析的设备 serial 调度平台小助手任务：同一设备上的任务先进先出排队，不同设备上的任务可以同时执行，避免多任务抢同一台设备。

## Requirements

### Requirement: 同设备串行异设备并行
系统 SHALL 以任务记录上已解析的 `device_serial` 为调度键。当某设备已有状态为 running 的任务时，新提交到该设备的任务 MUST 保持 pending 并按创建时间先进先出等待。当两台任务的设备 serial 不同时，系统 SHALL 允许二者同时为 running。系统 MUST NOT 在同一设备上并行启动两条 running 任务。

#### Scenario: 同设备第二条任务排队
- **WHEN** 设备 A 上已有一条 running 任务，用户再提交一条指定设备 A 的任务
- **THEN** 新任务状态为 pending，且在先任务进入 completed 或 failed 之前不得变为 running

#### Scenario: 异设备可以并行
- **WHEN** 设备 A 上有一条 running 任务，用户提交一条指定设备 B 的任务且 B 上没有 running 任务
- **THEN** 指定设备 B 的任务可以立即变为 running

#### Scenario: 前序结束后拉起排队任务
- **WHEN** 设备 A 上 running 任务进入 completed 或 failed，且该设备仍有 pending 任务
- **THEN** 系统按创建时间最早者将该 pending 任务变为 running 并开始执行

### Requirement: 提交时固化设备 serial
系统 SHALL 在创建任务时写入最终调度用的设备 serial。用户留空设备时 MUST 解析当时第一台在线设备并写入；解析失败 MUST 不创建任务。后续调度 MUST 使用落库 serial，MUST NOT 在排队唤醒时再次改写为「当时第一台在线设备」。

#### Scenario: 留空设备写入解析结果
- **WHEN** 用户提交时未选设备且存在在线设备
- **THEN** 任务记录的设备 serial 等于提交时刻解析到的那台设备，调度按该 serial 排队

### Requirement: 进程重启后恢复排队
系统 SHALL 在服务进程启动时把遗留的 running 任务标记为失败，然后按设备尝试启动各设备上最早的 pending 任务。

#### Scenario: 重启后遗留 running 失败并拉起 pending
- **WHEN** 服务重启时某设备存在一条遗留 running 与一条 pending
- **THEN** 遗留 running 落 failed，该 pending 可被调度为 running
