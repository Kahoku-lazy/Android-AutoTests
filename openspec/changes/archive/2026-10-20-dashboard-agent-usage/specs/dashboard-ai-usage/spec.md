## MODIFIED Requirements

### Requirement: 仪表盘提供 AI 用量统计接口

系统 SHALL 在仪表盘统计接口的 `ai_usage` 中提供任务数量、输入 token、输出 token、合计 token、缓存命中 token、缓存命中率、平均每任务 token 与 DeepSeek 费用，且均分「今日 / 累计」。输入、输出、缓存命中与费用 MUST 来自当前用户可见智能体的小时用量合计。今日 MUST 指统计日等于当前日期。任务数量 MUST 按可见任务计数，MUST NOT 改用小时记录的调用次数。DeepSeek 费用 MUST 为这些小时费用之和，精度到小数点后 8 位。MUST NOT 用任务上的 token 列，或按小数点后 4 位重算的费用，作为这组数字。`ai_usage.agents` MUST 为每个可见智能体给出一份整份用量。近 12 日的 Token 曲线与费用曲线 MUST 按同一小时用量、以统计日分桶。

#### Scenario: 统计接口返回 AI 用量

- **WHEN** 用户请求仪表盘统计接口
- **THEN** 响应含 `ai_usage`，其 `task_count`、`input_tokens`、`output_tokens`、`total_tokens`、`cache_hit_tokens`、`cache_hit_rate`、`avg_tokens_per_task`、`deepseek_cost` 各含 `today` 与 `total`，并含 `agents` 数组

#### Scenario: 缓存命中率除零

- **WHEN** 输入 token 总数为 0
- **THEN** 缓存命中率为 0，不报错

#### Scenario: 两个角色的费用并进同一份

- **WHEN** 同一智能体在同一统计日有执行者与验收者两条小时用量
- **THEN** 该日输入、输出、缓存命中与费用等于两条记录之和，且只对应这一份智能体用量

### Requirement: 仪表盘展示 AI 用量区块

系统 SHALL 在仪表盘「AI 用量」区块展示任务数量、累计 Token、缓存命中率、平均每任务 Token、DeepSeek 费用卡片，每张卡片同时显示今日与累计数值。DeepSeek 费用 MUST 显示到小数点后 8 位。该区块内的 KPI 卡 MUST NOT 渲染独立「进入」按钮；有跳转路径时用户仍可通过激活整卡进入智能体页。每个可见智能体 MUST 在这些卡片下方再展示一张卡，标题为助手显示名，内容为缓存命中、输入、输出、总费用四项。

#### Scenario: 区块卡片展示

- **WHEN** 用户打开仪表盘且 AI 用量数据加载完成
- **THEN** 「AI 用量」区块展示上述五张卡片，每卡显示今日与累计两个数值，并在其下为每个可见智能体展示缓存命中、输入、输出、总费用

#### Scenario: AI KPI cards have no enter button

- **WHEN** 用户查看「AI 用量」区块已加载的 KPI 卡
- **THEN** 卡片内不存在「进入」按钮（`.kpi-card__enter`）
- **AND** 卡片仍可激活并导航到既有智能体路径

## ADDED Requirements

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
