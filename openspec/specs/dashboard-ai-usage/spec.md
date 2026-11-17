# dashboard-ai-usage Specification

## Purpose

约定仪表盘按今日与累计展示平台全部已入账模型的 token 与费用：累计用量、当天用量、缓存命中率、总费用、当天费用。用量趋势按账本日期与小时分桶。任务数量在平台概览章节展示。

## Requirements

### Requirement: 后端持久化 AI 消息 token 用量

系统 SHALL 在 AI 对话流式回复持久化时，记录该条 assistant 消息的输入 token 与输出 token，并记录模型名。

#### Scenario: 对话回复记录 token

- **WHEN** 一次 AI 流式回复完成并落库
- **THEN** 该 assistant 消息的输入 token 与输出 token 字段为该轮回复的累计值，模型名字段非空

#### Scenario: 历史消息无用量

- **WHEN** 修复前已存在的历史消息被读取
- **THEN** 其 token 字段保持 0，不影响统计接口按 0 参与汇总

### Requirement: 后端持久化 AI 消息缓存命中

系统 SHALL 记录该条 assistant 消息的缓存命中 token 数与缓存写入 token 数（模型 API 返回时）。

#### Scenario: 缓存命中落库

- **WHEN** 模型 API 返回缓存命中用量
- **THEN** 该 assistant 消息的缓存命中 token 字段为该轮累计值

### Requirement: 仪表盘提供 AI 用量统计接口

系统 SHALL 在仪表盘统计接口的 `ai_usage` 中提供任务数量、输入 token、输出 token、合计 token、缓存命中 token、缓存命中率、平均每任务 token 与平台费用，且均分「今日 / 累计」。输入、输出、缓存命中与费用 MUST 来自 `ai_usage_records` 全表，MUST NOT 读取 `task_usage_hourly`，MUST NOT 按当前用户可见智能体过滤。今日 MUST 指 `occurred_at` 落在当前日期。任务数量 MUST 按可见任务计数，MUST NOT 改用账本调用次数。平台费用 MUST 为已计价行的人民币费用之和，精度到小数点后 8 位；未计价行 MUST 另以 token 合计返回，MUST NOT 计入费用。MUST NOT 用任务上的 token 列或任务费用列作为这组数字。近 7 日的 Token 曲线与费用曲线 MUST 按同一账本、以 `occurred_at` 的日期分桶。

#### Scenario: 统计接口返回 AI 用量

- **WHEN** 用户请求仪表盘统计接口
- **THEN** 响应含 `ai_usage`，其 token、缓存命中、缓存命中率、平均每任务 token 与平台费用各含 `today` 与 `total`
- **AND** 平台费用来自账本已计价行，不来自小时表

#### Scenario: 缓存命中率除零

- **WHEN** 输入 token 总数为 0
- **THEN** 缓存命中率为 0，不报错

#### Scenario: 两个角色的费用并进同一份

- **WHEN** 同一任务的执行角色与验收角色各产生一笔已计价账本行
- **THEN** 平台费用等于这两笔之和，不按角色拆成两份账单

#### Scenario: 不可见智能体的用量仍进平台合计

- **WHEN** 账本中存在不属于当前查看者可见范围的已计价行
- **THEN** 该行的 token 与费用仍进入平台合计

#### Scenario: 未计价消耗单独可见

- **WHEN** 今日有 token 大于 0 且计价状态为未计价的账本行
- **THEN** 这些 token 出现在未计价合计中
- **AND** 平台费用不包含这些行

### Requirement: 仪表盘展示 AI 用量区块

系统 SHALL 在仪表盘「AI 用量」区块展示累计用量、当天用量、缓存命中率、总费用、当天费用五张卡片。左侧第一行 MUST 依次为累计用量、当天用量、缓存命中率，左侧第二行 MUST 依次为总费用、当天费用。这五张 KPI 卡的副标题 MUST 为「平台」，MUST NOT 写「DeepSeek」。累计用量与当天用量 MUST 以 token 合计量为主数值，按百万（M）单位、保留 2 位小数显示，MUST NOT 除以任务数。缓存命中率 MUST 以百分比、1 位小数显示。总费用与当天费用 MUST 取账本已计价费用，按三位有效数字显示，MUST NOT 使用科学计数法。默认单位为人民币；用户切换到美元后单位 MUST 为美元，数值 MUST 由库存人民币按所显示的汇率换算。该区块内的五张 KPI 卡 MUST 为纯展示卡：MUST NOT 渲染独立「进入」按钮，MUST NOT 绑定跳转路径，MUST NOT 具备可点击交互形态。未计价 token 大于 0 时，区块 MUST 可见地标出该数量，MUST NOT 把对应费用显示成 0 元。

#### Scenario: 区块卡片展示

- **WHEN** 用户打开仪表盘且 AI 用量数据加载完成
- **THEN** 左侧第一行依次为「累计用量」「当天用量」「缓存命中率」，左侧第二行依次为「总费用」「当天费用」
- **AND** 五张卡副标题均为「平台」，费用来自账本

#### Scenario: 五张 KPI 卡副标题一致

- **WHEN** 用户查看「AI 用量」区块内已加载的五张 KPI 卡
- **THEN** 每张卡都渲染一条副标题，且文案均为「平台」

#### Scenario: 当天 Token 用量不取平均

- **WHEN** 当天 token 合计为 12,345,678 且当天任务数为 4
- **THEN** 「当天用量」卡显示 `12.35M`，MUST NOT 显示按任务数平均后的数值

#### Scenario: 费用按累计与当天拆分

- **WHEN** 累计已计价费用为 5.64520228 元、当天费用为 2.66 元
- **THEN** 「总费用」显示 `5.65 元`，「当天费用」显示 `2.66 元`，副标题均为「平台」

#### Scenario: 切换美元只改显示

- **WHEN** 总费用库存为 6.71320000 元，展示汇率为 6.7132，用户切换到美元
- **THEN** 总费用显示为 1 美元量级的换算值，库存仍为 6.71320000 元

#### Scenario: AI KPI cards have no enter button

- **WHEN** 用户查看或点击「AI 用量」区块已加载的五张 KPI 卡
- **THEN** 卡片内不存在「进入」按钮（`.kpi-card__enter`）
- **AND** 卡片不带 `role="button"`，不进入可聚焦态，点击不改变路由

### Requirement: 今日用量按小时返回且不提前出数

系统 SHALL 在统计接口的 `charts.today_usage` 返回当天逐小时的用量，字段为 `tokens`、`cost`（等长 24 项，下标即小时 0–23）与 `current`。`tokens[h]` MUST 为第 h 小时（`[h:00, h+1:00)`）内账本「输入 token + 输出 token」之和，`cost[h]` MUST 为该小时内已计价费用之和（人民币，8 位小数）；该小时尚未走完或尚未开始时，对应项 MUST 为 `null`，MUST NOT 提前给出该小时的数据，MUST NOT 返回当天累计值。`current` MUST 描述正在进行中的那一小时：`hour` 为当前时刻（0–24，最多 2 位小数）、`tokens` 与 `cost` 为该小时从起点到当前时刻的消耗；当前时刻正好落在整点时 `current` MUST 为 `null`。所有数值 MUST 来自 `ai_usage_records`，MUST NOT 读取小时表或任务费用列。当天没有用量时，已走完的小时 MUST 为 `0`、未走完与未开始的小时 MUST 为 `null`，且 MUST 不报错。该字段 MUST NOT 包含缓存命中序列。

#### Scenario: 未到达的小时不出数

- **WHEN** 当天 `11:05` 时读取统计接口，且 `[09:00,10:00)` 的账本已消耗 1,239,521 token
- **THEN** `tokens[9]` 为 `1,239,521`，`tokens[11]` 及之后的小时均为 `null`
- **AND** `current.hour` 约为 `11.08`，`current.tokens` 为 `[11:00,11:05)` 的账本消耗

#### Scenario: 整点后归入已完成小时

- **WHEN** 当天已过 `12:00`，`[11:00,12:00)` 的账本共消耗 40 token
- **THEN** `tokens[11]` 为 `40`，`current` 指向 `12` 点这一小时

#### Scenario: 整点边界无进行中数据

- **WHEN** 当前时刻正好是 `12:00:00`
- **THEN** `current` 为 `null`，`tokens[11]` 已带出完整值

#### Scenario: 当天无用量

- **WHEN** 平台当天没有任何账本行
- **THEN** 已走完的小时为 `0`，未走完与未开始的小时为 `null`，`current` 的 `tokens` 与 `cost` 为 0，接口仍返回成功

### Requirement: AI 用量区块承载用量趋势图

「AI 用量」章节 SHALL 在本章节的用量卡片组下方，以一个「用量趋势」子标题分隔后，承载全部 AI 用量类图表，顺序 MUST 为：每日 Token 用量与每日 DeepSeek 费用（同一行两列）、今日 Token 与费用（整行）、Voice 来源 Token 消耗（整行）。这些图表 MUST NOT 再出现在「趋势与动态」章节。图表的组件、系列、取数口径、纵轴与图例 MUST 与搬移前完全一致，MUST NOT 因换章节而改变数值或单位。「AI 用量」章节 MUST NOT 因新增图表而改变既有用量卡片组的展示与交互。

#### Scenario: 用量趋势图集中在 AI 用量区块

- **WHEN** 用户打开仪表盘并查看「AI 用量」章节
- **THEN** 本章节的用量卡片组下方依次出现「每日 Token 用量 / 每日 DeepSeek 费用」行、「今日 Token 与费用」卡、「Voice 来源 Token 消耗」卡
- **AND** 卡片组与图表之间有「用量趋势」子标题分隔

#### Scenario: 趋势与动态不再含用量图

- **WHEN** 用户查看「趋势与动态」章节
- **THEN** 该章节只有助手任务卡、任务执行结果与最近动态
- **AND** 页面不存在重复的「每日 Token 用量」「每日 DeepSeek 费用」「今日 Token 与费用」「Voice 来源 Token 消耗」卡片

### Requirement: AI 用量区块的数值配色

AI 用量区块里的「平台账单」卡，其主指标（缓存命中率）与四个明细数值（当天用量 / 当天费用 / 总用量 / 总费用）MUST 使用与共享 `KpiCard` 相同的**深彩渐变**：accent（`--part-accent`）与墨色按 48% → 30% 混合，MUST NOT 混入纸色，MUST NOT 使用三段式渐变（末段淡化会让数字读不动）。数值与卡底（`--ink` 4% 混纸色）的计算对比度 MUST 不低于 4.5:1。

单位（`M` / `元` / `%`）MUST 保持墨色并覆盖掉渐变，MUST NOT 跟随数值吃同一套渐变。字段名（缓存命中率 / 当天用量 …）MUST 保持次要色，MUST NOT 用 accent 上色。

#### Scenario: 账单卡数值可读

- **WHEN** 打开仪表盘并查看 AI 用量的「平台账单」卡
- **THEN** `71.7%`、`0.60M`、`0.178 元` 等数值为 accent 与墨色 48%→30% 的渐变
- **AND** 数值对卡底的对比度不低于 4.5:1
- **AND** 单位与字段名仍是墨色 / 次要色，不吃渐变

#### Scenario: 与统计卡同一套配方

- **WHEN** 比较平台概览的统计卡数值与平台账单卡数值
- **THEN** 两者的渐变区间一致（48% → 30%），只是 accent 取各自模块色
