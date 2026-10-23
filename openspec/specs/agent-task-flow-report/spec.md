# agent-task-flow-report Specification

## Purpose

按用例和步骤展示一次可见任务的智能体事件。摘要给出任务状态、测试结果、耗时、助手、设备和费用。每一轮标出模型在做的动作或验收标准，验收结论和执行交付挂在对应步骤上。

## Requirements

### Requirement: 可见任务的事件流程

系统 SHALL 通过 `GET /api/tasks/{id}/report/` 返回当前用户可见任务的事件流程，响应 MUST 使用标准信封 `{status, data}`：`data` 含 `task`、`rounds`、`cases`、`conclusion`，业务负载 MUST NOT 自带 `status` 字段。`cases` MUST 按用例列出步骤、用例结果和该用例下的轮次。任务不存在、编号无效或当前用户不可见时 MUST 返回 404，错误体为 `{status: false, message}`。该接口 MUST 只读，MUST NOT 写业务表。该接口 MUST 由 DRF 视图提供，使 `GET` 方法出现在 OpenAPI 基线的 `/api/tasks/{task_id}/report/` 下。

#### Scenario: 返回已完成任务的流程

- **WHEN** 当前用户打开自己可见的任务 115 的流程
- **THEN** 响应 `status` 为真，`data.task` 含标题、状态、设备、用例、助手、起止时间与费用，`data.rounds` 按时间排列，`data.cases` 给出用例与步骤
- **AND** 响应顶层不再出现平铺的 `task` / `rounds` / `cases` 字段

#### Scenario: 他人任务不可见

- **WHEN** 另一个普通用户请求同一任务编号
- **THEN** 响应为 404，响应体为 `{status: false, message}`

### Requirement: 按回复分轮并按阶段分块

系统 SHALL 以每条 `ReplyStartEvent` 开始一轮。一轮内 MUST 按事件顺序排列；阶段相对上一块发生变化时才新开一块。块标题 MUST 为「开始」「推理阶段」「执行阶段」「结束」。连续且同类型、同一步骤与尝试次数的增量 MUST 并成一条，并用 `count` 给出次数。

#### Scenario: 增量合并后阶段交替

- **WHEN** 一轮中依次出现回复开始、三条工具参数增量、工具参数完成、工具结果完成、回复结束
- **THEN** 该轮的块依次为开始、推理阶段、执行阶段、结束，推理阶段的增量条 `count` 为 3，其后仍保留参数完成

### Requirement: 报告页时间到秒并给出执行耗时

事件流程页的任务起止时间与每条事件时间 MUST 显示为 `YYYY-MM-DD HH:mm:ss`。起止都存在时 MUST 同时给出整次任务的执行耗时。没有事件时 MUST 说明这次任务还没有事件记录。

#### Scenario: 同一分钟内的起止可以区分

- **WHEN** 任务于 `2026-10-20 16:51:01` 开始、`2026-10-20 16:51:35` 结束
- **THEN** 页头显示这两个时刻，并显示执行 34 秒

### Requirement: 报告摘要展示任务结果与环境

系统 SHALL 在报告正文顶部展示任务状态、测试结果、执行耗时与起止时间、执行助手与设备、以及费用。任务状态 MUST 把待执行与暂停显示为待执行，执行中显示为执行中，其余终态显示为已完成。测试结果 MUST 为 PASS 或 FAIL；没有判决且任务未失败时可以为空。费用 MUST 显示到小数点后 8 位。起止时间 MUST 为 `YYYY-MM-DD HH:mm:ss`。

#### Scenario: 失败任务的摘要分开状态与结果

- **WHEN** 任务状态为失败，且最后一次判决不通过
- **THEN** 摘要中任务状态为已完成，测试结果为 FAIL

### Requirement: 按用例列出步骤并给出用例结果

系统 SHALL 按任务配置里的用例顺序展示用例。同一份事件里步骤序号倒退时 MUST 进入下一条用例。每条用例 MUST 给出结果：全部步骤通过为 PASS，任一步不通过为 FAIL，已经开始但未全部通过为未完成，没有轮次为未执行。用例标题 MUST 可折叠。

#### Scenario: 两条用例在步骤序号回到 1 时分开

- **WHEN** 第一条用例的步骤都已通过，随后步骤序号回到 1 且该步不通过
- **THEN** 报告出现两条用例，第一条为 PASS，第二条为 FAIL

### Requirement: 步骤标题标明模型在做什么

每一轮 MUST 可折叠，且默认收起。标题 MUST 含中文步骤序号、执行模型或验收模型、角色名与模型名，以及该步要做的动作或要达成的结果。验收轮在有判决时 MUST 在标题上标 PASS 或 FAIL。

#### Scenario: 执行轮标题带动作

- **WHEN** 第一步由 `executor_role` 执行，动作为「启动应用」
- **THEN** 该轮标题含「步骤一」「执行模型」「executor_role」和「启动应用」

### Requirement: 结论与交付挂在对应步骤

验收轮展开后 MUST 首先展示该轮结构化输出的说明，作为该步结论。执行轮在工具参数含交付原文时，展开后 MUST 首先展示该交付全文。系统 MUST NOT 再把全部判决集中堆在页头下方，也 MUST NOT 从文本日志截取结论或交付。

#### Scenario: 验收说明出现在该步折叠内

- **WHEN** 验收轮的结构化输出说明为「截图显示用户已登录」，且判决为通过
- **THEN** 该轮标题标 PASS，展开后的结论为该说明全文

#### Scenario: 执行交付出现在该步折叠内

- **WHEN** 执行轮的工具参数含交付原文「已打开首页并停在设备列表」
- **THEN** 该轮展开后首先展示这段交付全文

### Requirement: 报告接口只读取渲染所需事件字段

系统 SHALL 在生成 `GET /api/tasks/{id}/report/` 响应时，只从事件表读取渲染所需的列。流式增量事件的载荷（`payload`）MUST NOT 进入报告聚合，也 MUST NOT 出现在响应中；增量 MUST 仅参与合并计数与 `count` 的计算。响应 MUST 继续使用 `{status, data}` 信封，`data` 中 `task`、`rounds`、`cases`、`conclusion` 的字段与语义 MUST 与变更前保持一致。在开发机本地 MySQL、单任务 10 万级事件（其中 9 成以上为流式增量）的条件下，服务端完成该次聚合的耗时 MUST 小于 4 秒（变更前实测 10.2 秒）。

#### Scenario: 大量增量任务的报告四秒内返回

- **WHEN** 单任务有 147,850 条事件，其中 139,948 条为工具参数增量
- **THEN** 接口在 4 秒内返回，且该增量段在 `data.rounds` 中仍是一条，`count` 等于该段内的增量条数

#### Scenario: 增量载荷不进入响应

- **WHEN** 任务里每条流式增量事件的 `payload` 各为 1 MB
- **THEN** 响应体不包含任何增量 `payload` 原文，响应体积不随增量载荷体积增长

#### Scenario: 输出与变更前逐字段一致

- **WHEN** 同一任务分别用变更前与变更后的实现生成报告
- **THEN** `task`、`rounds`、`cases`、`conclusion` 深度相等，时间、费用与判决均一致

### Requirement: 事件明细完整展示

事件项的 `detail` MUST 完整包含该事件的展示文本：文本块全文、工具入参全文、工具结果全文。系统 MUST NOT 按固定字数截断明细，也 MUST NOT 为截断追加省略号。明细只 MUST 去掉回车符并去掉首尾空白。`data.task.result` 不受本要求约束，仍为 240 字摘要。

#### Scenario: 超长工具入参完整下发

- **WHEN** 一条工具调用结束事件的入参有 2,831 字
- **THEN** 该项 `detail` 包含全部入参、长度不小于 2,831，且不以省略号结尾

#### Scenario: 超长文本块完整下发

- **WHEN** 一条文本块完成事件的文本有 3,500 字
- **THEN** 该项 `detail` 等于该文本去掉首尾空白后的内容

#### Scenario: 任务结果仍为摘要

- **WHEN** 任务的 `result` 有 1,000 字
- **THEN** `data.task.result` 仍为 240 字摘要，与事件明细的完整展示互不影响
