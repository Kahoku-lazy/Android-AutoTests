## MODIFIED Requirements

### Requirement: 仪表盘展示 AI 用量区块

系统 SHALL 在仪表盘「AI 用量」区块展示任务数量、累计 Token、缓存命中率、平均每任务 Token、DeepSeek 费用卡片，每张卡片同时显示今日与累计数值。DeepSeek 费用卡片上的累计与今日 MUST 以三位有效数字显示，MUST NOT 使用科学计数法。接口里的费用精度仍为小数点后 8 位。该区块内的 KPI 卡 MUST NOT 渲染独立「进入」按钮；有跳转路径时用户仍可通过激活整卡进入智能体页。每个可见智能体 MUST 在这些卡片下方再展示一张卡，标题为助手显示名，内容为缓存命中、输入、输出、总费用四项。

#### Scenario: 区块卡片展示

- **WHEN** 用户打开仪表盘且 AI 用量数据加载完成
- **THEN** 「AI 用量」区块展示上述五张卡片，每卡显示今日与累计两个数值，并在其下为每个可见智能体展示缓存命中、输入、输出、总费用

#### Scenario: AI KPI cards have no enter button

- **WHEN** 用户查看「AI 用量」区块已加载的 KPI 卡
- **THEN** 卡片内不存在「进入」按钮（`.kpi-card__enter`）
- **AND** 卡片仍可激活并导航到既有智能体路径
