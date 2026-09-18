## Purpose

定义仪表盘「章节钉板」信息架构：将运营、AI、资产、趋势动态收束为可扫描的四章节容器，并用 chip 摘要替代裸灰字标签，使分区层级与 Hand-Drawn Doodle 主题一致。

## ADDED Requirements

### Requirement: Dashboard content is organized into four chapter boards
仪表盘主内容区 SHALL 将原有同权多段分区收束为恰好四个章节钉板，顺序为：平台运营、AI 用量、测试资产、趋势与动态。每个章节 SHALL 使用页面级分区容器（`.doc-section` 或其 doodle 章节变体），MUST NOT 用 `AppCard` 充当章节外壳。

#### Scenario: Four chapters render in order
- **WHEN** 用户打开仪表盘且统计数据可展示（含全零占位）
- **THEN** 主内容区自上而下出现四个章节，标题文案分别为「平台运营」「AI 用量」「测试资产」「趋势与动态」（或语义等价的产品文案），且不再以独立同权章节分别呈现「测试用例」与「元素定位」

#### Scenario: Cases and elements share one asset chapter
- **WHEN** 用户查看「测试资产」章节
- **THEN** 用例类 KPI 与元素类 KPI 同属该章节；用例与元素以子分区或双栏形式区分，而不是两个顶层章节

### Requirement: Chapter headers expose hierarchy with doodle cues
每个章节头 SHALL 同时包含：模块色方标（或等价图标块）、英文 eyebrow、中文标题（可用 marker 高亮），MUST NOT 仅依赖灰色圆角 pill 作为主层级信号。

#### Scenario: Chapter head is scannable
- **WHEN** 用户浏览任一章节头
- **THEN** 可见英文 eyebrow、中文标题与彩色方标；章节容器带虚线描边与硬色偏移阴影（钉板语义）

### Requirement: Section summaries use chips instead of raw gray meta lines
章节级汇总信息（设备/任务总数、Token/费用、角色拆解等）SHALL 以 chip（近直角墨边标签）呈现。AI 用量的分角色 Token 摘要 MUST NOT 再以多行未样式化灰字堆叠。

#### Scenario: AI role breakdown renders as chips
- **WHEN** 后端返回分角色 Token 汇总且前端已格式化为可读字符串
- **THEN** 「累计 / 今日」角色摘要以 chip 形式出现在 AI 用量章节头或紧邻摘要区，页面上不出现「分角色 Token（累计）：…」这类多行裸灰字标签

### Requirement: Existing KPI cards and APIs remain the data surface
章节重组 MUST NOT 改变仪表盘只读聚合语义：KPI 入口卡、趋势 `AppCard`、活动时间线仍直映现有 stats/activities 接口字段；MUST NOT 新增写操作或前端推算业务指标。

#### Scenario: Stats endpoints unchanged
- **WHEN** 完成本变更后打开仪表盘
- **THEN** 仍只请求既有仪表盘统计与活动只读接口；各 KPI 数值与重组前同一数据源字段一致（展示分组可变，字段映射不变）
