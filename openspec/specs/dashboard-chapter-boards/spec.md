# dashboard-chapter-boards Specification

## Purpose
定义仪表盘「章节钉板」信息架构：将运营、AI、资产、趋势动态收束为可扫描的四章节容器，以模块色方标、英文 eyebrow 与中文标题表达分区层级；平台运营章节承载设备、智能体、运行中任务、任务数量与工作流五张入口卡，使视觉与 Hand-Drawn Doodle 主题一致。

## Requirements

### Requirement: Dashboard content is organized into four chapter boards
仪表盘主内容区 SHALL 将原有同权多段分区收束为恰好四个章节钉板，顺序为：平台运营、AI 用量、测试资产、趋势与动态。每个章节 SHALL 使用页面级分区容器（`.doc-section` 或其 doodle 章节变体），MUST NOT 用 `AppCard` 充当章节外壳。测试资产章节 MUST 只呈现用例类 KPI，MUST NOT 再呈现元素类 KPI 或元素统计卡（元素定位已退役）。

#### Scenario: Four chapters render in order
- **WHEN** 用户打开仪表盘且统计数据可展示（含全零占位）
- **THEN** 主内容区自上而下出现四个章节，标题文案分别为「平台运营」「AI 用量」「测试资产」「趋势与动态」（或语义等价的产品文案），且不再以独立同权章节分别呈现「测试用例」与「元素定位」

#### Scenario: Cases and elements share one asset chapter
- **WHEN** 用户查看「测试资产」章节
- **THEN** 该章节只呈现用例类 KPI；不出现元素类 KPI、元素统计卡或「Android元素」文案

### Requirement: Chapter headers expose hierarchy with doodle cues
每个章节头 SHALL 同时包含：模块色方标（或等价图标块）、英文 eyebrow、中文标题（可用 marker 高亮），MUST NOT 仅依赖灰色圆角 pill 作为主层级信号。

#### Scenario: Chapter head is scannable
- **WHEN** 用户浏览任一章节头
- **THEN** 可见英文 eyebrow、中文标题与彩色方标；章节容器带虚线描边与硬色偏移阴影（钉板语义）

### Requirement: Existing KPI cards and APIs remain the data surface
章节重组 MUST NOT 把仪表盘改成可写运营台：KPI 入口卡、趋势 `AppCard`、活动时间线仍直映只读 stats/activities 接口。系统 MUST 继续只请求既有仪表盘统计与活动只读接口，MUST NOT 为展示测试资产而新增写操作或在前端推算业务指标。`cases.breakdown` SHALL 按当前用户的用例项目维度返回（每项含项目标识、名称与用例数）；MUST NOT 再要求该字段保持测试类型拆分或与重组前类型键一一对应。`cases.total` SHALL 仍为当前用户文档用例合计。元素类 KPI 的数据源字段随元素定位退役一并移除，统计响应 MUST NOT 再包含元素或元素页面计数。

#### Scenario: Stats endpoints unchanged
- **WHEN** 完成本变更后打开仪表盘
- **THEN** 仍只请求既有仪表盘统计与活动只读接口
- **AND** 测试用例子区的项目卡数值来自该次统计响应中的 `cases.breakdown` 项目项，而不是前端另行请求用例项目列表后再本地拼卡

#### Scenario: Case totals still match project rows
- **WHEN** 统计响应同时给出 `cases.total` 与项目维度 `cases.breakdown`
- **THEN** `cases.total` 等于各项目用例数之和（无项目时为 0）

### Requirement: Chapter headers omit summary chips

仪表盘章节头 MUST NOT 再呈现 chip 摘要行。「平台运营」章节头 MUST NOT 展示设备、智能体、任务、工作流汇总 chip；「AI 用量」章节头 MUST NOT 展示「角色·累计」「角色·今日」或语义等价的分角色 Token 摘要 chip。章节层级 MUST 由模块色方标、英文 eyebrow 与中文标题表达，MUST NOT 依赖灰色圆角 pill。`ai_usage.by_role` 仍可保留在统计接口中，但 MUST NOT 用于章节头 chip。「测试资产」章节头右侧的用例数 chip 不受本条约束。

#### Scenario: 平台运营章节头不再有汇总 chip

- **WHEN** 用户打开仪表盘并查看「平台运营」章节头
- **THEN** 章节头只有模块色方标、英文 eyebrow、中文标题与描述，不存在设备、智能体、任务或工作流数量的 chip

#### Scenario: AI 用量章节头不再有角色 chip

- **WHEN** 用户打开仪表盘并查看「AI 用量」章节头
- **THEN** 页面不存在「角色·累计」「角色·今日」或语义等价的分角色 Token 摘要 chip

#### Scenario: 测试资产用例 chip 保留

- **WHEN** 用户查看「测试资产」章节头右侧
- **THEN** 用例数量 chip 仍然可见

### Requirement: Platform ops chapter includes task count card

仪表盘「平台运营」章节 SHALL 按顺序展示在线设备、活跃智能体、运行中任务、任务数量、工作流五张 KPI 卡。任务数量卡的数据 MUST 取自当前用户可见任务的累计数量，MUST 保留整卡点击进入任务清单页（`/tasks`）。该卡 MUST 同时展示今日任务数作为副标题。这五张卡 MUST NOT 渲染独立「进入」按钮或同类进入控件，跳转 MUST 只能由整卡激活触发。

#### Scenario: 平台运营五卡顺序

- **WHEN** 用户打开仪表盘并查看「平台运营」章节
- **THEN** 章节内按顺序出现「在线设备」「活跃智能体」「运行中任务」「任务数量」「工作流」五张卡，且「任务数量」不再出现在「AI 用量」章节

#### Scenario: 任务数量卡无独立进入按钮

- **WHEN** 用户查看「任务数量」卡
- **THEN** 卡内不存在「进入」按钮，点击整卡仍可进入任务清单页

#### Scenario: 其余四张平台运营卡同样无独立进入按钮

- **WHEN** 用户查看「在线设备」「活跃智能体」「运行中任务」「工作流」四张卡
- **THEN** 四张卡内均不存在「进入」按钮（`.kpi-card__enter`）
- **AND** 点击卡面仍分别进入设备页、智能体页、报告页、工作流页
