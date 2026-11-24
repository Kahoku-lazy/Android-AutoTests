# dashboard-chapter-boards Delta

## MODIFIED Requirements

### Requirement: Chapter shells are solid while metric cards stay dashed

仪表盘三个章节板（平台概览 / AI 用量 / 趋势与动态）的外壳描边 SHALL 为墨色实线，MUST NOT 覆写全局 `.doc-section` 的实线线型；章节头分隔线与子标题分隔线 SHALL 同为实线。

章节外壳内的 KPI 指标卡与趋势 `AppCard` SHALL 保留既有手绘虚线卡壳，MUST NOT 因章节外壳改线型而一起变成实线。（智能体用量卡已随智能体账单退役移除，不再属于本 requirement 的覆盖对象。）

#### Scenario: Chapter shells render solid borders

- **WHEN** 用户打开仪表盘并查看三个章节板
- **THEN** 每个章节外壳为墨色实线描边，仍保留模块色硬偏移阴影
- **AND** 章节头与子标题的分隔线为实线

#### Scenario: Metric cards keep their dashed shells

- **WHEN** 用户查看「平台概览」的在线设备、平台助手等运行指标卡与用例项目卡，或「AI 用量」的账单卡
- **THEN** 这些卡片仍呈现虚线描边、近直角与硬偏移色阴影