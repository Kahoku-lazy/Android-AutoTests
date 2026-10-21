## MODIFIED Requirements

### Requirement: Chapter headers expose hierarchy with doodle cues

每个章节头 SHALL 同时包含：模块色方标（或等价图标块）、英文 eyebrow、中文标题（可用 marker 高亮），MUST NOT 仅依赖灰色圆角 pill 作为主层级信号。

#### Scenario: Chapter head is scannable

- **WHEN** 用户浏览任一章节头
- **THEN** 可见英文 eyebrow、中文标题与彩色方标；章节容器带实线描边与硬色偏移阴影（钉板语义）

## ADDED Requirements

### Requirement: Chapter shells are solid while metric cards stay dashed

仪表盘四个章节板（平台运营 / AI 用量 / 测试资产 / 趋势与动态）的外壳描边 SHALL 为墨色实线，MUST NOT 覆写全局 `.doc-section` 的实线线型；章节头分隔线与子标题分隔线 SHALL 同为实线。

章节外壳内的 KPI 指标卡、智能体用量卡与趋势 `AppCard` SHALL 保留既有手绘虚线卡壳，MUST NOT 因章节外壳改线型而一起变成实线。

#### Scenario: Chapter shells render solid borders

- **WHEN** 用户打开仪表盘并查看四个章节板
- **THEN** 每个章节外壳为墨色实线描边，仍保留模块色硬偏移阴影
- **AND** 章节头与子标题的分隔线为实线

#### Scenario: Metric cards keep their dashed shells

- **WHEN** 用户查看「平台运营」的在线设备、活跃智能体等 KPI 卡，或「AI 用量」的累计用量、当天用量等 KPI 卡
- **THEN** 这些卡片仍呈现虚线描边、近直角与硬偏移色阴影
