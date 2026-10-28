# dashboard-ai-usage Specification

## Purpose

约定仪表盘按今日与累计展示平台全部模型调用的 token 与费用用量（不按智能体可见性过滤）：累计用量、当天用量、缓存命中率、总费用、当天费用，以及每个可见智能体一份缓存命中、输入、输出和总费用；任务数量在平台运营章节展示。

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

系统 SHALL 在仪表盘统计接口的 `ai_usage` 中提供任务数量、输入 token、输出 token、合计 token、缓存命中 token、缓存命中率、平均每任务 token 与 DeepSeek 费用，且均分「今日 / 累计」。输入、输出、缓存命中与费用 MUST 来自平台全部小时用量（`task_usage_hourly` 全表，含 `agent_id = 0` 的行），MUST NOT 按当前用户可见智能体过滤。今日 MUST 指统计日等于当前日期。任务数量 MUST 按可见任务计数，MUST NOT 改用小时记录的调用次数。DeepSeek 费用 MUST 为这些小时费用之和，精度到小数点后 8 位。MUST NOT 用任务上的 token 列，或按小数点后 4 位重算的费用，作为这组数字。`ai_usage.agents` MUST 为每个可见智能体给出一份整份用量。近 7 日的 Token 曲线与费用曲线 MUST 按同一小时用量、以统计日分桶。

#### Scenario: 统计接口返回 AI 用量

- **WHEN** 用户请求仪表盘统计接口
- **THEN** 响应含 `ai_usage`，其 `task_count`、`input_tokens`、`output_tokens`、`total_tokens`、`cache_hit_tokens`、`cache_hit_rate`、`avg_tokens_per_task`、`deepseek_cost` 各含 `today` 与 `total`，并含 `agents` 数组

#### Scenario: 缓存命中率除零

- **WHEN** 输入 token 总数为 0
- **THEN** 缓存命中率为 0，不报错

#### Scenario: 两个角色的费用并进同一份

- **WHEN** 同一智能体在同一统计日有执行者与验收者两条小时用量
- **THEN** 该日输入、输出、缓存命中与费用等于两条记录之和，且只对应这一份智能体用量

#### Scenario: 不可见智能体的用量仍进平台合计

- **WHEN** 平台上存在一条 `agent_id = 0` 或属于查看者不可见智能体的小时用量
- **THEN** `ai_usage` 的 token 与 DeepSeek 费用合计包含该行
- **AND** `ai_usage.agents` 不因此新增该智能体的卡片

### Requirement: 仪表盘展示 AI 用量区块

系统 SHALL 在仪表盘「AI 用量」区块展示累计用量、当天用量、缓存命中率、总费用、当天费用五张卡片，并 MUST 采用左侧两行 KPI、右侧智能体用量的布局。左侧第一行 MUST 依次为累计用量、当天用量、缓存命中率，左侧第二行 MUST 依次为总费用、当天费用。这五张 KPI 卡的副标题 MUST 全部为「DeepSeek」，MUST NOT 出现空副标题或其它文案。累计用量与当天用量 MUST 以 token 合计量为主数值，按百万（M）单位、保留 2 位小数显示，MUST NOT 除以任务数，MUST NOT 使用千（K）单位。缓存命中率 MUST 以百分比、1 位小数显示。总费用与当天费用 MUST 分别取累计与当天的 DeepSeek 费用，按三位有效数字显示，MUST NOT 使用科学计数法，单位 MUST 为元；接口里的费用精度仍为小数点后 8 位。任务数量卡 MUST NOT 再出现在「AI 用量」区块。该区块内的五张 KPI 卡 MUST 为纯展示卡：MUST NOT 渲染独立「进入」按钮，MUST NOT 绑定跳转路径，MUST NOT 具备可点击交互形态（不可点、无 `role="button"`、无 hover 抬升）。每个可见智能体 MUST 在右侧列展示一张卡，标题为助手显示名，内容为缓存命中、输入、输出、总费用四项，MUST NOT 排在 KPI 卡下方。

#### Scenario: 区块卡片展示

- **WHEN** 用户打开仪表盘且 AI 用量数据加载完成
- **THEN** 左侧第一行依次为「累计用量」「当天用量」「缓存命中率」三张副标题为「DeepSeek」的卡片，左侧第二行依次为「总费用」「当天费用」两张副标题为「DeepSeek」的卡片，智能体卡位于右侧列

#### Scenario: 五张 KPI 卡副标题一致

- **WHEN** 用户查看「AI 用量」区块内已加载的五张 KPI 卡
- **THEN** 每张卡都渲染一条副标题，且文案均为「DeepSeek」，不存在缺省文案「核心指标实时更新」

#### Scenario: 当天 Token 用量不取平均

- **WHEN** 当天 token 合计为 12,345,678 且当天任务数为 4
- **THEN** 「当天用量」卡显示 `12.35M`，MUST NOT 显示按任务数平均后的数值，MUST NOT 使用 `K` 单位，且副标题为「DeepSeek」

#### Scenario: 费用按累计与当天拆分

- **WHEN** 累计 DeepSeek 费用为 5.64520228 元、当天费用为 2.66 元
- **THEN** 「总费用」显示 `5.65 元` 且副标题为「DeepSeek」，「当天费用」显示 `2.66 元` 且副标题为「DeepSeek」

#### Scenario: AI KPI cards have no enter button

- **WHEN** 用户查看或点击「AI 用量」区块已加载的五张 KPI 卡
- **THEN** 卡片内不存在「进入」按钮（`.kpi-card__enter`）
- **AND** 卡片不带 `role="button"`，不进入可聚焦态，点击不改变路由

### Requirement: 智能体用量按整份合计

当前用户每个可见智能体 MUST 只有一份用量。同一智能体在不同角色、不同模型上的缓存命中 token、输入 token、输出 token 与总费用 MUST 分别加总。MUST NOT 按角色或模型拆成多张卡。标题 MUST 使用该智能体的助手显示名。总费用 MUST 为小数点后 8 位的十进制字符串，MUST NOT 使用科学计数法。没有小时用量的可见智能体 MUST 仍列出，缓存命中、输入、输出为 0，总费用为 `0.00000000`。

#### Scenario: 执行者与验收者合成一张卡

- **WHEN** 同一智能体既有执行者小时用量又有验收者小时用量
- **THEN** 该智能体只出现一张卡，缓存命中、输入、输出与总费用分别为两组之和

#### Scenario: 助手显示名作为标题

- **WHEN** 智能体配置了助手显示名
- **THEN** 卡片标题为该显示名

#### Scenario: 零用量智能体仍出现

- **WHEN** 可见智能体没有任何小时用量
- **THEN** 卡片仍出现，缓存命中、输入、输出为 0，总费用为 0.00000000

### Requirement: 今日用量按小时返回且不提前出数

系统 SHALL 在统计接口的 `charts.today_usage` 返回当天逐小时的用量，字段为 `tokens`、`cost`（等长 24 项，下标即小时 0–23）与 `current`。`tokens[h]` MUST 为第 h 小时（`[h:00, h+1:00)`）内「输入 token + 输出 token」之和，`cost[h]` MUST 为该小时内 DeepSeek 费用之和（元，8 位小数）；该小时尚未走完或尚未开始时，对应项 MUST 为 `null`，MUST NOT 提前给出该小时的数据，MUST NOT 返回当天累计值。`current` MUST 描述正在进行中的那一小时：`hour` 为当前时刻（0–24，最多 2 位小数）、`tokens` 与 `cost` 为该小时从起点到当前时刻的消耗；当前时刻正好落在整点时 `current` MUST 为 `null`。所有数值 MUST 来自平台全部小时用量表（含 `agent_id = 0` 的行），MUST NOT 按当前用户可见智能体过滤，MUST NOT 取任务表上的 token 列或按任务回写的费用。当天没有用量或小时用量表不可用时，已走完的小时 MUST 为 `0`、未走完与未开始的小时 MUST 为 `null`，且 MUST 不报错。该字段 MUST NOT 包含缓存命中序列。

#### Scenario: 未到达的小时不出数

- **WHEN** 当天 `11:05` 时读取统计接口，且 `[09:00,10:00)` 已消耗 1,239,521 token
- **THEN** `tokens[9]` 为 `1,239,521`，`tokens[11]` 及之后的小时均为 `null`
- **AND** `current.hour` 约为 `11.08`，`current.tokens` 为 `[11:00,11:05)` 的消耗

#### Scenario: 整点后归入已完成小时

- **WHEN** 当天已过 `12:00`，`[11:00,12:00)` 共消耗 40 token
- **THEN** `tokens[11]` 为 `40`，`current` 指向 `12` 点这一小时

#### Scenario: 整点边界无进行中数据

- **WHEN** 当前时刻正好是 `12:00:00`
- **THEN** `current` 为 `null`，`tokens[11]` 已带出完整值

#### Scenario: 当天无用量

- **WHEN** 平台当天没有任何小时用量
- **THEN** 已走完的小时为 `0`，未走完与未开始的小时为 `null`，`current` 的 `tokens` 与 `cost` 为 0，接口仍返回成功
