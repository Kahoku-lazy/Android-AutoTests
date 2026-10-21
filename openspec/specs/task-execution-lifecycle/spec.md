# task-execution-lifecycle Specification

## Purpose
定义服务停机与重启时任务的生命周期口径：停机先排空正在跑的任务，非正常退出留下的 running 任务以“已中断”留痕，不冒充实测失败，并在任务清单与测试报告中以一致的状态呈现。

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

### Requirement: 中断不计入通过与失败

测试报告的汇总与每日趋势 MUST 只把 `completed`/`success` 计为通过、`failed` 计为失败。`interrupted` MUST 计入总执行次数，MUST NOT 计入通过或失败，也 MUST NOT 进入通过率分母。

#### Scenario: 混合状态下的通过率

- **WHEN** 可见任务包含 1 条 `completed`、1 条 `failed`、1 条 `interrupted`
- **THEN** 汇总的通过为 1、失败为 1、总执行次数为 3、通过率为 50%

### Requirement: 中断状态在界面上可见

任务清单、任务详情与测试报告列表 MUST 把 `interrupted` 显示为“已中断”，并使用与失败不同的标签样式；测试报告的状态筛选 MUST 提供“已中断”分组。

#### Scenario: 报告页显示已中断记录

- **WHEN** 用户打开 `/reports` 且存在 `interrupted` 任务
- **THEN** 该行状态显示“已中断”，且“已中断”筛选分组可筛出该行
