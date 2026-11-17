## MODIFIED Requirements

### Requirement: Dashboard content is organized into three chapter boards

仪表盘主内容区 SHALL 将原有同权多段分区收束为恰好三个章节钉板，顺序为：平台概览、AI 用量、趋势与动态。「平台概览」SHALL 在同一章节内同时承载平台运行指标组（在线设备、平台助手、工作流、运行中任务、任务数量）、仅运营可见的运营配置子区，以及测试用例资产子区（「测试用例」子标题 + 用例项目入口卡）。运行指标组、运营配置子区与用例子区之间 MUST 以子标题分隔，MUST NOT 拆成独立同权章节。每个章节 SHALL 使用页面级分区容器（`.doc-section` 或其 doodle 章节变体），MUST NOT 用 `AppCard` 充当章节外壳。「平台概览」的用例子区 MUST 只呈现用例类 KPI，MUST NOT 再呈现元素类 KPI 或元素统计卡（元素定位已退役）。系统 MUST NOT 再展示「活跃智能体」卡。

#### Scenario: Three chapters render in order

- **WHEN** 用户打开仪表盘且统计数据可展示（含全零占位）
- **THEN** 主内容区自上而下出现三个章节，标题文案分别为「平台概览」「AI 用量」「趋势与动态」
- **AND** 页面不再出现独立的「平台运营」或「测试资产」章节标题

#### Scenario: Overview chapter holds runtime metrics and case assets

- **WHEN** 用户查看「平台概览」章节
- **THEN** 章节内先出现在线设备、平台助手、工作流、运行中任务、任务数量五张运行指标卡
- **AND** 其下出现「测试用例」子标题与用例项目入口卡
- **AND** 不出现「活跃智能体」、元素类 KPI、元素统计卡或「Android元素」文案

### Requirement: Platform ops chapter includes task count card

仪表盘「平台概览」章节的运行指标组 SHALL 按顺序展示在线设备、平台助手、工作流、运行中任务、任务数量五张 KPI 卡。平台助手卡的主数值 MUST 为助手名片总数，工作流卡的主数值 MUST 为工作流总数；两张卡 MUST 整卡进入平台助手页（`/ai-assistant`）。运行中任务卡的主数值 MUST 只计状态为 `running` 的工作流任务，副标题 MUST 固定为「排队 N」，其中 N 为状态为 `pending` 的工作流任务数（含 0）；该卡 MUST 整卡进入任务清单页（`/tasks`）。任务数量卡的主数值 MUST 为工作流任务累计数量，副标题 MUST 为今日新建的工作流任务数，MUST 整卡进入任务清单页。这五张卡 MUST NOT 渲染独立「进入」按钮或同类进入控件，跳转 MUST 只能由整卡激活触发。系统 MUST NOT 把已退役的设备执行或用例编写任务计入运行中、排队或任务数量。

#### Scenario: 平台概览五卡顺序

- **WHEN** 用户打开仪表盘并查看「平台概览」章节的运行指标组
- **THEN** 按顺序出现「在线设备」「平台助手」「工作流」「运行中任务」「任务数量」五张卡
- **AND** 不出现「活跃智能体」，且「任务数量」不再出现在「AI 用量」章节

#### Scenario: 平台助手与工作流分别计数

- **WHEN** 平台上有 3 张助手名片和 2 条工作流
- **THEN** 「平台助手」显示 3，「工作流」显示 2
- **AND** 点击任一张卡进入平台助手页

#### Scenario: 运行中任务只计执行中并显示排队

- **WHEN** 工作流任务中有 1 条 `running`、2 条 `pending`，另有已退役类型的任务也在执行
- **THEN** 「运行中任务」主数值为 1，副标题为「排队 2」
- **AND** 点击整卡进入任务清单页

#### Scenario: 没有排队时仍显示零

- **WHEN** 工作流任务中没有 `pending`
- **THEN** 「运行中任务」副标题仍为「排队 0」

#### Scenario: 任务数量卡无独立进入按钮

- **WHEN** 用户查看「任务数量」卡
- **THEN** 卡内不存在「进入」按钮，点击整卡仍可进入任务清单页
- **AND** 主数值不含已退役任务类型

#### Scenario: 其余四张运行指标卡同样无独立进入按钮

- **WHEN** 用户查看「在线设备」「平台助手」「工作流」「运行中任务」四张卡
- **THEN** 四张卡内均不存在「进入」按钮（`.kpi-card__enter`）
- **AND** 点击卡面分别进入设备页、平台助手页、平台助手页、任务清单页

## ADDED Requirements

### Requirement: Overview inserts an operator-only configuration group

「平台概览」SHALL 在运行指标组与「测试用例」子区之间放置「运营配置」子区。该子区 MUST 只在当前用户为超级管理员或运营时渲染，MUST 以子标题与运行指标组、用例子区分隔。普通用户 MUST NOT 看到该子标题或其中任何卡片。

#### Scenario: 运营在运行指标与用例之间看到运营配置

- **WHEN** 超级管理员或运营打开仪表盘并查看「平台概览」
- **THEN** 「运营配置」子标题出现在五张运行指标卡之后、「测试用例」子标题之前

#### Scenario: 普通用户看不到运营配置子区

- **WHEN** 普通用户打开仪表盘并查看「平台概览」
- **THEN** 不出现「运营配置」子标题
- **AND** 运行指标组之后直接是「测试用例」子区
