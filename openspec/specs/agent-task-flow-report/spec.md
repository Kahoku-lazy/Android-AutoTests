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

系统 SHALL 以每条 `ReplyStartEvent` 或每条 SOP 步骤起点（事件类型名 `SOP_STEP_STARTED`）开始一轮。一轮内 MUST 按事件顺序排列；阶段相对上一块发生变化时才新开一块。块标题 MUST 为「开始」「推理阶段」「执行阶段」「结束」。连续且同类型、同一步骤与尝试次数的增量 MUST 并成一条，并用 `count` 给出次数；`count` MUST 取该段内所有增量事件的 `delta_count` 之和，写库时已经折叠成一行的事件 MUST 直接采用该行的 `delta_count`。`delta_count` 缺省为 1 的旧数据 MUST 表现与逐条增量合并时一致。步骤起点 MUST 落在它所开启的那一轮里，MUST NOT 被并入上一步骤的最后一轮。

#### Scenario: 增量合并后阶段交替

- **WHEN** 一轮中依次出现回复开始、三条工具参数增量、工具参数完成、工具结果完成、回复结束
- **THEN** 该轮的块依次为开始、推理阶段、执行阶段、结束，推理阶段的增量条 `count` 为 3，其后仍保留参数完成

#### Scenario: 步骤起点开启新的一轮

- **WHEN** 上一步骤的最后一轮已结束，随后到达一条 `SOP_STEP_STARTED`
- **THEN** 该步骤起点位于新的一轮内，其 `round_id` 大于上一步骤各轮的 `round_id`

#### Scenario: 写库已折叠的增量直接采用存储条数

- **WHEN** 一条工具参数增量行的 `delta_count` 为 17,447，且同段没有其它未折叠增量行
- **THEN** 报告的该项 `count` 为 17,447，展示时刻为该段第一条增量的时刻

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

### Requirement: 结论与交付挂在对应步骤

步骤展开体内，该次尝试的验收子块 MUST 首先展示结构化输出的说明，作为该次结论；执行子块在工具参数含交付原文时 MUST 首先展示该交付全文。系统 MUST NOT 再把全部判决集中堆在页头下方，也 MUST NOT 从文本日志截取结论或交付。

#### Scenario: 验收说明出现在该步折叠内

- **WHEN** 某次验收的结构化输出说明为「截图显示用户已登录」，且判决为通过
- **THEN** 该步验收子块头部标 `✅`，子块内的结论为该说明全文

#### Scenario: 执行交付出现在该步折叠内

- **WHEN** 执行轮的工具参数含交付原文「已打开首页并停在设备列表」
- **THEN** 该步执行子块内首先展示这段交付全文

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

### Requirement: 报告轮次只下发一份

`data.rounds[]` MUST 带稳定的 `round_id`（从 0 起、同一响应内唯一）。`data.cases[]` MUST 用 `round_ids` 引用轮次，MUST NOT 再内嵌 `rounds` 字段；`round_ids` 中每个值 MUST 能在 `data.rounds` 中找到 `round_id` 相同的项。同一轮次对象在响应里 MUST 只序列化一次。单任务 15 万级事件、156 轮的响应 MUST 小于 5MB（未压缩）。

#### Scenario: 用例只引用不复制轮次

- **WHEN** 请求一个 156 轮、12 个用例的终态任务报告
- **THEN** `data.cases[]` 不含 `rounds` 字段，其 `round_ids` 合计 156 项
- **AND** `data.rounds` 仍是 156 项

#### Scenario: 轮次引用可解析且顺序一致

- **WHEN** 校验任一用例的 `round_ids`
- **THEN** 每个值都能在 `data.rounds[].round_id` 中找到唯一对应项
- **AND** 按 `round_ids` 顺序取出的轮次与该用例实际执行顺序一致

#### Scenario: 响应体积不因用例引用翻倍

- **WHEN** 同一任务分别用改动前与改动后的实现生成报告
- **THEN** 改动后响应小于改动前的 60%，且小于 5MB
- **AND** `task`、`rounds`、`conclusion` 的字段与语义不变

### Requirement: 终态任务报告缓存与条件请求

状态为 `completed`、`failed`、`interrupted`、`cancelled` 或 `stopped` 的任务，其报告 MUST 被缓存，TTL MUST 不小于 10 分钟。缓存键 MUST 包含任务编号与该任务当前最大事件 `seq`；最大 `seq` 增大（重跑、补写事件）后 MUST 重新构建，MUST NOT 继续返回旧报告。非终态任务 MUST NOT 缓存。响应 MUST 带 `ETag`；请求带相同 `If-None-Match` 时 MUST 返回 `304` 且响应体为空。缓存命中时 MUST 在 300ms 内返回（本地开发机口径）。

#### Scenario: 二次打开命中缓存

- **WHEN** 对同一终态任务连续请求两次报告
- **THEN** 第二次在 300ms 内返回，且 `data` 与第一次深度相等

#### Scenario: ETag 命中返回 304

- **WHEN** 客户端带上一次响应里的 `ETag` 再次请求
- **THEN** 返回 304 且没有响应体

#### Scenario: 重跑后不复用旧报告

- **WHEN** 任务被重跑并写入新事件后再请求报告
- **THEN** 响应包含新事件的轮次，MUST NOT 与重跑前缓存逐字段相等

#### Scenario: 运行中任务不写缓存

- **WHEN** 任务处于 `running`，连续请求两次报告，且期间新增了一轮事件
- **THEN** 第二次响应的轮次数比第一次多 1

### Requirement: 步骤起点与运行提醒可读

事件项的展示文本 SHALL 覆盖新增的三类事件：步骤起点 MUST 展示步骤名与该步第几次尝试；运行时注入提醒 MUST 展示提醒全文，MUST NOT 截断；推理轮次用尽 MUST 给出一句可读说明。三类事件的标题 MUST 为可读中文，MUST NOT 直接暴露事件类型名。明细仍 MUST 只去掉回车符与首尾空白，MUST NOT 追加省略号。缺少步骤名或尝试次数时 MUST 只展示已有的部分，MUST NOT 打印 `None`。

#### Scenario: 步骤起点给出步骤与尝试次数

- **WHEN** 一条步骤起点事件的步骤名为「打开设置」、尝试次数为 2
- **THEN** 该事件项的明细为「打开设置 · 第 2 次尝试」，标题为可读中文而非 `SOP_STEP_STARTED`

#### Scenario: 运行提醒全文下发

- **WHEN** 一条运行时注入提醒的正文为 500 字
- **THEN** 该事件项的明细与该正文逐字相同，长度不小于 500，且不以省略号结尾

#### Scenario: 推理轮次用尽有可读说明

- **WHEN** 一条推理轮次用尽事件进入报告
- **THEN** 该事件项有非空的可读明细，且标题为可读中文

### Requirement: 按步骤分组执行与验收

系统 SHALL 在每条用例内按步骤分组展示。每个步骤 MUST 对应一行步骤行，其展开体 MUST 包含该步骤的执行过程与验收过程；执行轮与验收轮 MUST NOT 再作为同级条目平铺。

步骤 MUST 以报告 `cases[].steps` 为轴：序号 MUST 取 `steps[].seq`，动作 MUST 取 `steps[].action`。`steps` 缺失时 MUST 按轮次的 `step_seq` 去重升序生成步骤；`step_seq` 也缺失的存量轮次 MUST 每个轮次各自成为一步，MUST NOT 丢弃任何轮次。

轮次 MUST 按 `step_seq` 归入步骤，并按角色类别分流为执行或验收；MUST NOT 用事件的先后顺序推断角色。同一步骤内，执行过程 MUST 排在验收过程之前。

#### Scenario: 执行与验收收进同一步

- **WHEN** 某步有一次执行轮与一次验收轮
- **THEN** 该用例下只有一行该步骤
- **AND** 展开后依次出现执行过程与验收过程，二者不再作为两条同级标题

#### Scenario: 步骤序号相同的重试归到同一步

- **WHEN** 同一步骤执行了两次（`step_seq` 相同，`attempt` 分别为 1 与 2）
- **THEN** 该用例只出现一行该步骤
- **AND** 展开体内有两次尝试，序号仍为该步骤号

#### Scenario: 存量轮次缺少步骤序号

- **WHEN** 任务的轮次都没有 `step_seq`
- **THEN** 每个轮次各自成为一行，标题取该轮的 `subject`
- **AND** 没有任何轮次被丢弃

#### Scenario: 只有验收轮没有执行轮

- **WHEN** 某步只采集到验收轮
- **THEN** 该步仍然渲染步骤行，展开体内只有验收过程，不出现空白的执行块

### Requirement: 步骤行标题与结果徽标

每个步骤行 MUST 可折叠，步骤行 MUST 是唯一的折叠单位。标题 MUST 以行首数字序号开头，序号 MUST 取该步在用例里的步骤号；同一步骤的多次尝试 MUST 共用同一序号。标题 MUST 只含序号与动作，MUST NOT 出现中文步骤序号（「步骤一」…「步骤十」），MUST NOT 出现模型名，也 MUST NOT 出现角色类别文字。动作文本 MUST 只出现一次，MUST NOT 在执行子块或验收子块里重复。

步骤行 MUST 在右侧给出该步结果徽标，取值 MUST 为 `PASS`、`FAIL`、`未完成`、`未执行` 之一，且 MUST NOT 再用 `✅` / `❌` 表示同一结果。

#### Scenario: 步骤行只写一次动作

- **WHEN** 第一步由 `executor_role` 执行，模型为 `deepseek-flash`，动作为「启动应用」
- **THEN** 该用例只有一行以「1.」开头并含「启动应用」的步骤行
- **AND** 展开后的执行子块与验收子块都不再重复「启动应用」，也不出现 `deepseek-flash` 与「执行模型」

#### Scenario: 结果只由步骤徽标表示

- **WHEN** 某步结果为 PASS
- **THEN** 步骤行右侧只有 PASS 徽标，没有 `✅`
- **AND** 该步验收子块头部有 `✅`

### Requirement: 子块的角色徽章与验收标记

角色名 MUST 出现在步骤展开体内的执行 / 验收子块头部，以徽章形式呈现，并按角色区分配色——执行角色与验收角色 MUST 使用不同底色。角色名为空的存量轮次 MUST NOT 渲染角色徽章，子块其余部分保持完整。

验收子块头部 MUST 用 `✅`（通过）或 `❌`（不通过）标记该次验收判决；尚无判决的验收 MUST NOT 给该标记。

#### Scenario: 验收子块标记失败

- **WHEN** 某次验收判决为不通过
- **THEN** 该验收子块头部以 `❌` 开头，块内结论给出驳回说明

#### Scenario: 两个子块按角色分色

- **WHEN** 同一步骤既有 `executor_role` 子块也有 `verifier_role` 子块
- **THEN** 两个角色名都以徽章出现，且执行与验收徽章底色不同，角色名不再以纯文本出现

#### Scenario: 存量轮次没有角色名

- **WHEN** 轮次的 `role` 为空
- **THEN** 该子块不渲染角色徽章，执行过程与验收过程的内容仍完整展示

### Requirement: 重试按次分块并以标签标次数

同一步骤的每次尝试 MUST 在展开体内单独成块，块头 MUST 是次数标签（如「第1次」「第2次」），MUST NOT 写成「第 N 次尝试」这类句子。多次尝试 MUST 按 `attempt` 升序排列；每次尝试的验收 MUST 与该次执行配对展示，配不上执行的验收 MUST 单独成块并保留。

#### Scenario: 两次尝试各成一块

- **WHEN** 第 2 步第 1 次执行交付后验收驳回，第 2 次执行后验收通过
- **THEN** 该步展开体内出现两个块，块头分别为「第1次」与「第2次」
- **AND** 「第1次」块内是驳回结论，「第2次」块内是通过结论

#### Scenario: 次数不写成句子

- **WHEN** 某步只有一次尝试
- **THEN** 展开体块头是「第1次」标签，展开体内不出现「第 1 次尝试」这类文字描述

### Requirement: 尝试块与过程块可折叠

步骤展开体内，每次尝试 MUST 是可折叠的块；块内的执行过程与验收过程 MUST 各自可折叠，互不影响。

首次展开某步时，其尝试块 MUST 默认展开，执行过程与验收过程 MUST 默认收起。过程块收起时 MUST NOT 渲染阶段时间线、截图与事件明细。

过程块收起时，头部 MUST 继续显示角色徽章与过程名；验收过程还 MUST 显示判决标记与结论摘要，MUST NOT 只剩一行空标题。

收起尝试块时 MUST 同时隐藏其内部的执行与验收过程，同一步的其它尝试 MUST 不受影响。

#### Scenario: 展开步骤只看到块头

- **WHEN** 用户展开某一步
- **THEN** 该步每个尝试只显示一行块头与执行 / 验收两行过程头
- **AND** 页面没有该步的阶段时间线与截图

#### Scenario: 点开过程才出时间线

- **WHEN** 用户点开该步的执行过程
- **THEN** 执行过程出现阶段时间线与明细
- **AND** 验收过程仍保持收起

#### Scenario: 收起尝试块带走两个过程

- **WHEN** 该步有两次尝试，用户收起「第1次」
- **THEN** 「第1次」的执行与验收过程一起隐藏
- **AND** 「第2次」保持原状

#### Scenario: 验收过程收起仍给结论

- **WHEN** 验收过程处于收起状态，判决为通过
- **THEN** 过程头仍有 `✅` 与结论摘要

### Requirement: 步骤默认收起并全量渲染

进入任务详情时 MUST 只展开第一条用例，其步骤 MUST 全部收起，MUST NOT 自动展开任何步骤的展开体。用户展开某步时 MUST 只渲染该步展开体的内容，收起时 MUST NOT 保留已展开的过程。

一条用例的步骤 MUST 全量渲染，MUST NOT 分页、MUST NOT 截断步骤行。页面 MUST NOT 再出现轮次分页控件。

#### Scenario: 首次进入只看到步骤清单

- **WHEN** 打开一个已完成任务的详情页
- **THEN** 第一条用例展开，下面只有该用例的步骤行
- **AND** 没有任何步骤展开体默认打开

#### Scenario: 展开一步不影响其它步

- **WHEN** 用户点开第 2 步
- **THEN** 只有第 2 步的展开体出现，其余步骤仍为收起

#### Scenario: 步骤全量渲染不分页

- **WHEN** 一条用例有 25 个步骤
- **THEN** 25 行步骤全部渲染
- **AND** 页面不出现「上一页 / 下一页」或页码
