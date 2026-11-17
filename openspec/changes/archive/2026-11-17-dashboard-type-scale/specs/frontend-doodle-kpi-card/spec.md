## REMOVED Requirements

### Requirement: Entry card primary value matches accent shadow

**Reason**: 该要求把主数值的配色写成「可用 accent、也可用满色」的开放口径，同时规定紧凑 `kpi` 变体的主数值 MUST 为墨色 —— 而实现上两个变体都早已改成同色相渐变，规格与代码已经对不上；本次又把渐变区间收紧到 80%→30%，原有描述无法表达。

**Migration**: 由本变更新增的「KPI 主数值取 accent 的 80%→30% 渐变」取代：两个变体统一走同一区间，标题与描述仍不随 accent 变色。

## ADDED Requirements

### Requirement: KPI 主数值取 accent 的 80%→30% 渐变

共享统计卡（`kpi` 与 `entry` 两个变体）的主数值 MUST 使用传入 accent 的同色相渐变：起点 MUST 为 accent 与纸色按 80% 混合，终点 MUST 为 accent 与纸色按 30% 混合。

该渐变 MUST NOT 混入墨色，MUST NOT 使用 100% 满色端，也 MUST NOT 使用低于 30% 的淡化端。

标题、描述、时间与字段名 MUST NOT 改用 accent 上色。

#### Scenario: 入口卡数值取同色相区间渐变

- **WHEN** 仪表盘以 `entry` 变体渲染统计入口卡
- **THEN** 主数值的颜色为该卡 accent 与纸色 80%→30% 的渐变
- **AND** 卡片硬偏移阴影仍取同一 accent

#### Scenario: 紧凑卡数值取同一区间

- **WHEN** 页面以默认 `kpi` 变体渲染共享统计卡
- **THEN** 主数值使用与 `entry` 变体相同的 80%→30% 区间渐变
- **AND** 标题与描述保持墨色 / 次要色，不随 accent 改变

### Requirement: 仪表盘信息层级字号

仪表盘页面 MUST 使用三档字号表达层级：大标题（平台概览 / AI 用量等章节标题）20px；卡片与区块标题 16px；其余文本（描述、字段名、时间、标签）14px。

大标题与数值（如 KPI 的 28px 数字）MUST NOT 因本口径改动。

图表内部绘制文字（ECharts 轴标签与图例）不在本要求范围内。

#### Scenario: 卡片标题与正文分档

- **WHEN** 用户打开仪表盘
- **THEN** 「在线设备」「DEEPSEEK 账单」「用量趋势」等标题为 16px
- **AND** 「核心指标实时更新」「当天用量」等文本为 14px

#### Scenario: 大标题与数值不变

- **WHEN** 用户打开仪表盘
- **THEN** 「平台概览」「AI 用量」仍为 20px
- **AND** KPI 数值仍为 28px
