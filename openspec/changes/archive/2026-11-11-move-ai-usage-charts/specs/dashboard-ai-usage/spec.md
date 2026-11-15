## ADDED Requirements

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
