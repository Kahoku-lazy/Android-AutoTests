# task-execution-lifecycle Specification

## Purpose
定义服务停机与重启时任务的生命周期口径：停机先排空正在跑的任务，非正常退出留下的 running 任务以“已中断”留痕，不冒充实测失败，并在任务清单中一致呈现；中断不产生报告，不进报告台账。

## Requirements

### Requirement: 停机先排空再退出

服务停止时，系统 SHALL 先停止派发新任务，再等待当前所有 `running` 任务结束，之后才退出进程。等待上限 MUST 为 180 秒；没有 `running` 任务时 MUST 立即退出；超过上限 MUST 强制退出，并允许下次启动按中断处理。

#### Scenario: 有任务在跑时等待其结束

- **WHEN** 运维执行 `python run.py stop`，此刻存在 `running` 任务
- **THEN** 后端不再派发新的任务，`stop` 持续等待直到 `running` 归零后才停止进程
- **AND** 等待期间任务状态保持 `running`，不会被提前改写

#### Scenario: 无任务时立即停止

- **WHEN** 运维执行 `python run.py stop`，此刻没有 `running` 任务
- **THEN** 后端直接退出，不产生额外等待

#### Scenario: 超时强制退出

- **WHEN** 等待达到 180 秒仍有 `running` 任务
- **THEN** `stop` 强制结束后端进程
- **AND** 下次启动时这些任务按“已中断”处理

### Requirement: 重启后 running 记为中断而不再记失败

服务启动恢复时，遗留的 `running` 任务 MUST 改为 `interrupted` 状态，MUST NOT 记为 `failed`。恢复 MUST 写入中断说明与 `finished_at`，MUST 用事件明细回写该任务已产生的费用。

#### Scenario: 遗留 running 变为已中断

- **WHEN** 服务启动时数据库中仍有状态为 `running` 的任务
- **THEN** 该任务状态变为 `interrupted`，`finished_at` 非空，`result` 说明服务重启导致中断
- **AND** 该任务的 `cost_total` 等于其模型调用事件费用之和

#### Scenario: 排队任务仍被拉起

- **WHEN** 某设备存在一条遗留 `running` 与一条 `pending`
- **THEN** 遗留任务变为 `interrupted` 后，该 `pending` 任务仍可被调度为 `running`

### Requirement: 中断状态在任务清单可见

任务清单 MUST 把 `interrupted` 显示为“已中断”，并使用与失败不同的标签样式。测试报告列表 MUST NOT 展示中断任务：中断不产生报告，报告台账只收录已生成的报告。

#### Scenario: 任务清单显示已中断记录

- **WHEN** 用户打开任务清单且存在 `interrupted` 任务
- **THEN** 该任务状态显示“已中断”，标签样式与失败可区分

#### Scenario: 报告台账不显示中断任务

- **WHEN** 用户打开 `/reports` 且存在 `interrupted` 任务
- **THEN** 报告列表不含该任务的行，也不存在“已中断”筛选分组

### Requirement: 取消终态不被工作线程覆盖

任务被用户关闭并写入 `cancelled` 之后，工作线程的收尾 MUST NOT 把终态改写为 `completed`、`failed` 或 `interrupted`；工作线程 MAY 只补充用量与费用字段。取消与正常结束同时发生时，`cancelled` MUST 优先。

#### Scenario: 取消后工作线程恰好跑完

- **WHEN** 用户关闭任务后，工作线程在几秒内恰好完成了整轮运行
- **THEN** 任务终态仍为 `cancelled`，结果说明仍为“用户关闭”
- **AND** 不出现 `completed` 与 `cancelled` 两个终态先后写入的情况

#### Scenario: 取消后工作线程异常退出

- **WHEN** 任务被关闭后工作线程以异常结束
- **THEN** 任务终态仍为 `cancelled`，失败原因不写回任务结果

### Requirement: 终态与报告产出的边界

一次控制设备任务只要已经进入执行并产生事件记录，其 `failed` 终态（含验收不通过与运行中异常中断）MUST 对应一份可点的 HTML 报告，并在任务结果里留下报告定位。

`interrupted`（含预算超限与重启恢复的中断）与 `cancelled` MUST NOT 产出报告，MUST NOT 在任务结果里留下报告定位。起跑前失败（设备校验、工作流编号缺失、角色装配失败等，尚未产生事件记录）MUST NOT 产出报告，但其失败原因 MUST 写入任务结果供调用方读取。

#### Scenario: 验收不通过产报告

- **WHEN** 任务跑完全部步骤但存在未通过的验收结论，进入 `failed`
- **THEN** 任务结果带报告定位，任务清单可打开本次运行的报告

#### Scenario: 运行中异常中断产报告

- **WHEN** 任务在运行中因模型调用异常中断，进入 `failed`
- **THEN** 任务结果带报告定位，报告可打开且标注运行中断

#### Scenario: 预算中断与重启中断不产报告

- **WHEN** 任务因预算超限或服务重启恢复被标记为 `interrupted`
- **THEN** 任务结果不含报告定位，任务清单不显示「报告」入口

#### Scenario: 起跑前失败无报告但有原因

- **WHEN** 任务因工作流编号缺失在起跑前失败
- **THEN** 任务结果不含报告定位
- **AND** 任务结果含可读的失败原因
