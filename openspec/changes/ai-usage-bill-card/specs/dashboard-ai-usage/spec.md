## MODIFIED Requirements

### Requirement: 仪表盘展示 AI 用量区块

系统 SHALL 在仪表盘「AI 用量」区块左侧展示**一张聚合的「DeepSeek 账单」卡**，右侧为每个可见智能体的用量卡。账单卡 MUST 按以下层级排列：

1. 标题「DeepSeek 账单」；
2. 第一栏：缓存命中率（百分比、1 位小数、作为主指标）；
3. 第二行：当天用量 与 当天费用；
4. 第三行：总用量 与 总费用。

用量 MUST 以 token 合计量按百万（M）单位、保留 2 位小数显示，MUST NOT 除以任务数，MUST NOT 使用千（K）单位。费用 MUST 取累计与当天的 DeepSeek 费用，按三位有效数字显示，MUST NOT 使用科学计数法，单位 MUST 为元；接口里的费用精度仍为小数点后 8 位。系统 MUST NOT 再渲染「累计用量 / 当天用量 / 缓存命中率 / 总费用 / 当天费用」五张独立 KPI 卡。任务数量 MUST NOT 出现在「AI 用量」区块。账单卡与智能体卡 MUST 均为纯展示：MUST NOT 渲染独立「进入」按钮，MUST NOT 绑定跳转路径，MUST NOT 具备可点击交互形态（不可点、无 `role="button"`、无 hover 抬升）。每个可见智能体 MUST 在右侧列展示一张卡，标题为助手显示名，内容为缓存命中、输入、输出、总费用四项，MUST NOT 排在账单卡下方。

#### Scenario: 区块卡片展示

- **WHEN** 用户打开仪表盘且 AI 用量数据加载完成
- **THEN** 左侧只有一张标题为「DeepSeek 账单」的卡，右侧列是智能体用量卡
- **AND** 账单卡自上而下为「缓存命中率」栏、「当天用量 / 当天费用」行、「总用量 / 总费用」行，不再出现独立的五张 KPI 卡

#### Scenario: 五张 KPI 卡副标题一致

- **WHEN** 用户查看「AI 用量」区块左侧已加载的账单卡
- **THEN** 卡片标题固定为「DeepSeek 账单」，副标识固定为「DeepSeek」，不存在空文案或「核心指标实时更新」

#### Scenario: 当天 Token 用量不取平均

- **WHEN** 当天 token 合计为 12,345,678 且当天任务数为 4
- **THEN** 账单卡「当天用量」显示 `12.35M`，MUST NOT 显示按任务数平均后的数值，MUST NOT 使用 `K` 单位

#### Scenario: 费用按累计与当天拆分

- **WHEN** 累计 DeepSeek 费用为 5.64520228 元、当天费用为 2.66 元
- **THEN** 账单卡「总费用」显示 `5.65 元`，「当天费用」显示 `2.66 元`

#### Scenario: AI KPI cards have no enter button

- **WHEN** 用户查看或点击「DeepSeek 账单」卡
- **THEN** 卡片内不存在「进入」按钮（`.kpi-card__enter`）
- **AND** 卡片不带 `role="button"`，不进入可聚焦态，点击不改变路由
