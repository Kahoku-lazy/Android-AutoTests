## Purpose

约定任务终态如何收口：失败和中断仍是两个状态，原因写进结果，终态只在任务仍为运行中时才能改写，避免关闭、崩溃和热重载互相覆盖。

## ADDED Requirements

### Requirement: 失败与中断不新增状态

系统 MUST NOT 为任务新增状态值。步骤没通过、模型拒绝、设备命令失败和平台代码错误 MUST 记为 `failed`。进程退出时终态尚未写入、以及运行预算超限，MUST 记为 `interrupted`。用户关闭 MUST 记为 `cancelled`。测试报告的通过率口径 MUST 保持不变：只有 `failed` 计入失败，`interrupted` 只计入总执行次数。

#### Scenario: 模型拒绝仍是失败

- **WHEN** 运行中的任务因模型返回 400 而结束，且终态尚未被其它路径写过
- **THEN** 任务状态为 `failed`
- **AND** 结果中的 `failure_kind` 为 `provider`
- **AND** 该任务计入失败，不计入中断

#### Scenario: 预算超限是中断

- **WHEN** 运行中的任务因模型调用次数或时长超限而停止
- **THEN** 任务状态为 `interrupted`
- **AND** 结果中的 `cause` 为 `budget`
- **AND** 该任务不计入失败

### Requirement: 失败结果保留工作流并写明类别

抛错或步骤没通过时，系统 MUST 把结果写成 JSON，并 MUST 保留提交时已写入的 `workflow_id`。`failure_kind` MUST 只取 `verdict`、`provider`、`device`、`platform` 之一。`reason` MUST 是给人读的短句，MUST NOT 把异常堆栈或网关原始长文作为列表摘要。步骤跑完但一条步骤结论都没有时，MUST 记为 `platform`，不得记为成功。

#### Scenario: 抛错不抹掉工作流编号

- **WHEN** 一条带 `workflow_id` 的运行中任务因平台代码错误结束
- **THEN** 结果仍含原来的 `workflow_id`
- **AND** `failure_kind` 为 `platform`
- **AND** 按该工作流筛选仍能看到这条任务

#### Scenario: 步骤没通过写 verdict

- **WHEN** 任务的步骤都跑完，且至少一步没通过
- **THEN** 状态为 `failed`
- **AND** `failure_kind` 为 `verdict`
- **AND** `reason` 含没通过的步骤名

### Requirement: 中断原因只区分三种

中断结果 MUST 含 `cause`，取值只能是 `stop_timeout`、`process_lost`、`budget`。`python run.py stop` 等待满 180 秒后强制退出的任务 MUST 记为 `stop_timeout`。崩溃、热重载、调试器停掉，以及终态没写上后线程退出，MUST 记为 `process_lost`。系统 MUST NOT 把这些情况一律写成「服务重启」。系统 MUST NOT 为热重载单独新增状态或原因。

#### Scenario: 停机超时

- **WHEN** `python run.py stop` 等满 180 秒后强制退出，且当时某任务仍为 `running`
- **THEN** 下次收口后该任务为 `interrupted`
- **AND** `cause` 为 `stop_timeout`

#### Scenario: 热重载与崩溃同一原因

- **WHEN** 开发热重载或进程崩溃时，某任务仍为 `running` 且终态未写入
- **THEN** 收口后该任务为 `interrupted`
- **AND** `cause` 为 `process_lost`

### Requirement: 终态只在仍为运行中时改写

把任务写成 `completed`、`failed`、`interrupted` 或 `cancelled` 时，系统 MUST 只更新当前状态仍为 `running` 的那一行。若更新不到行，系统 MUST NOT 改已有状态和已有结果，MAY 只补充用量与费用。用户关闭之后工作线程再抛错或再跑完，终态 MUST 仍为 `cancelled`。

#### Scenario: 关闭后异常不改终态

- **WHEN** 用户已把任务写成 `cancelled`，随后工作线程抛出异常
- **THEN** 状态仍为 `cancelled`
- **AND** 结果仍是关闭说明，不出现失败类别

#### Scenario: 重复收口不覆盖

- **WHEN** 同一条任务已经被写成 `interrupted`，清扫再次扫到它
- **THEN** 状态和结果保持第一次写入的值

### Requirement: 心跳未停的任务不被收走

运行中的任务 MUST 周期更新心跳。服务进程的清扫 MUST 只处理状态为 `running` 且心跳已超时的任务。心跳仍在更新时，新启动的进程 MUST NOT 把该任务改成 `interrupted`。清扫 MUST 只在对外服务的进程中运行，管理命令和测试 MUST NOT 触发。收成中断后，系统 MUST 仍按设备拉起最早的 `pending` 任务。

#### Scenario: 旧进程还在跑

- **WHEN** 新服务进程启动时，某任务为 `running` 且心跳仍在更新
- **THEN** 该任务保持 `running`
- **AND** 同设备的 `pending` 任务不被这条仍在跑的任务之外的收口拉起

#### Scenario: 心跳停止后收成中断

- **WHEN** 某任务为 `running`，心跳已超过清扫阈值，且没有停机超时标记
- **THEN** 该任务变为 `interrupted`，`cause` 为 `process_lost`
- **AND** 同设备最早的 `pending` 任务可以被拉起

### Requirement: 列表能读出原因且中断不再轮询

任务列表摘要 MUST 优先展示结果中的 `reason` 或中断说明，MUST NOT 把整段异常原文当作摘要。任务清单在只剩 `interrupted` 任务时 MUST 停止运行态轮询。状态标签 MUST 仍为「任务失败」和「已中断」，不得按 `failure_kind` 或 `cause` 拆出新标签。

#### Scenario: 失败摘要是短句

- **WHEN** 用户打开任务清单，某失败任务的 `failure_kind` 为 `provider`
- **THEN** 该行状态为「任务失败」
- **AND** 摘要是模型拒绝的短句，不是网关返回的整段错误

#### Scenario: 中断后停止轮询

- **WHEN** 任务清单中没有待执行或执行中的任务，只剩已中断任务
- **THEN** 页面不再按运行态间隔继续刷新
