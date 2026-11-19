## Purpose

让同一工作流可以连续提交多条任务：同一台手机按提交先后排队，不同手机同时执行，空设备不再进入队列。

## ADDED Requirements

### Requirement: 工作流任务按可连接地址排队

系统 SHALL 以提交时固化的可连接地址作为工作流任务的调度键。USB 设备的键 MUST 是硬件序列号，局域网设备的键 MUST 是 `IP:端口`。同一地址已有 running 任务时，新任务 MUST 保持 pending，并按任务编号先后等待。不同地址的任务 MUST 可以同时 running。系统 MUST NOT 在同一地址并行启动两条 running 任务，无论它们来自工作流还是设备执行。

#### Scenario: 同一手机第二条排队

- **WHEN** 地址 A 已有一条 running 任务，用户再向地址 A 提交一条合法工作流任务
- **THEN** 新任务状态为 pending
- **AND** 先提交的任务结束前，新任务不得变为 running

#### Scenario: 不同手机并行

- **WHEN** 地址 A 已有一条 running 任务，用户向没有 running 任务的地址 B 提交一条合法工作流任务
- **THEN** 地址 B 的任务可以立即变为 running

#### Scenario: 前序结束后拉起最早排队任务

- **WHEN** 地址 A 的 running 任务进入成功、失败或取消，且该地址仍有 pending 任务
- **THEN** 系统按任务编号最早者把 pending 任务变为 running 并开始执行

### Requirement: 工作流必须选择设备

系统 SHALL 在创建工作流任务前要求一个非空可连接地址。地址为空时 MUST 拒绝本次提交，MUST NOT 创建任务，也 MUST NOT 启动执行。YAML MUST NOT 被当作设备来源。

#### Scenario: 空设备被拒绝

- **WHEN** 用户提交合法工作流编号和合法里程碑 YAML，但没有设备地址
- **THEN** 系统拒绝提交并说明需要选择设备
- **AND** 不产生新的任务记录

### Requirement: 删除排队任务后继续调度

系统 SHALL 在删除一条带设备地址的 pending 或 running 任务后，再次尝试调度该地址。删除不得让该地址剩余的最早 pending 任务永久停住。没有剩余 pending 任务时，系统 MUST NOT 启动新任务。

#### Scenario: 删除后拉起下一条

- **WHEN** 地址 A 只有一条 pending 任务，用户删除挡住它的同地址任务后该地址不再有 running 任务
- **THEN** 剩余的最早 pending 任务变为 running

#### Scenario: 没有下一条时不启动

- **WHEN** 用户删除地址 A 的最后一条 pending 或 running 任务
- **THEN** 系统不创建或启动新的任务

### Requirement: 停机排空拒绝派发时留下记录

停机排空期间，系统 MUST NOT 启动新的工作流任务。被排空拒绝的派发 MUST 留下可检索的日志，日志 MUST 含任务编号与设备地址。系统 MUST NOT 因此把已创建的 pending 任务改成失败。

#### Scenario: 排空中提交保持待执行

- **WHEN** 停机排空已经开始，用户提交一条带设备的合法工作流任务
- **THEN** 任务保持 pending
- **AND** 日志记录该任务因排空未被派发
