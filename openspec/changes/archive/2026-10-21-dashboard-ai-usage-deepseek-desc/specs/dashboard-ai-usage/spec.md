## MODIFIED Requirements

### Requirement: 仪表盘展示 AI 用量区块

系统 SHALL 在仪表盘「AI 用量」区块展示累计用量、当天用量、缓存命中率、总费用、当天费用五张卡片，并 MUST 采用左侧两行 KPI、右侧智能体用量的布局。左侧第一行 MUST 依次为累计用量、当天用量、缓存命中率，左侧第二行 MUST 依次为总费用、当天费用。这五张 KPI 卡的副标题 MUST 全部为「DeepSeek」，MUST NOT 出现空副标题或其它文案。累计用量与当天用量 MUST 以 token 合计量为主数值，按百万（M）单位、保留 2 位小数显示，MUST NOT 除以任务数，MUST NOT 使用千（K）单位。缓存命中率 MUST 以百分比、1 位小数显示。总费用与当天费用 MUST 分别取累计与当天的 DeepSeek 费用，按三位有效数字显示，MUST NOT 使用科学计数法，单位 MUST 为元；接口里的费用精度仍为小数点后 8 位。任务数量卡 MUST NOT 再出现在「AI 用量」区块。该区块内的 KPI 卡 MUST NOT 渲染独立「进入」按钮；有跳转路径时用户仍可通过激活整卡进入智能体页。每个可见智能体 MUST 在右侧列展示一张卡，标题为助手显示名，内容为缓存命中、输入、输出、总费用四项，MUST NOT 排在 KPI 卡下方。

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

- **WHEN** 用户查看「AI 用量」区块已加载的 KPI 卡
- **THEN** 卡片内不存在「进入」按钮（`.kpi-card__enter`）
- **AND** 卡片仍可激活并导航到既有智能体路径
