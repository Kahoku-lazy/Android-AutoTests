## MODIFIED Requirements

### Requirement: Dashboard content is organized into four chapter boards
仪表盘主内容区 SHALL 将原有同权多段分区收束为恰好四个章节钉板，顺序为：平台运营、AI 用量、测试资产、趋势与动态。每个章节 SHALL 使用页面级分区容器（`.doc-section` 或其 doodle 章节变体），MUST NOT 用 `AppCard` 充当章节外壳。测试资产章节 MUST 只呈现用例类 KPI，MUST NOT 再呈现元素类 KPI 或元素统计卡（元素定位已退役）。

#### Scenario: Four chapters render in order
- **WHEN** 用户打开仪表盘且统计数据可展示（含全零占位）
- **THEN** 主内容区自上而下出现四个章节，标题文案分别为「平台运营」「AI 用量」「测试资产」「趋势与动态」（或语义等价的产品文案），且不再以独立同权章节分别呈现「测试用例」与「元素定位」

#### Scenario: Cases and elements share one asset chapter
- **WHEN** 用户查看「测试资产」章节
- **THEN** 该章节只呈现用例类 KPI；不出现元素类 KPI、元素统计卡或「Android元素」文案

### Requirement: Existing KPI cards and APIs remain the data surface
章节重组 MUST NOT 把仪表盘改成可写运营台：KPI 入口卡、趋势 `AppCard`、活动时间线仍直映只读 stats/activities 接口。系统 MUST 继续只请求既有仪表盘统计与活动只读接口，MUST NOT 为展示测试资产而新增写操作或在前端推算业务指标。`cases.breakdown` SHALL 按当前用户的用例项目维度返回（每项含项目标识、名称与用例数）；MUST NOT 再要求该字段保持测试类型拆分或与重组前类型键一一对应。`cases.total` SHALL 仍为当前用户文档用例合计。元素类 KPI 的数据源字段随元素定位退役一并移除，统计响应 MUST NOT 再包含元素或元素页面计数。

#### Scenario: Stats endpoints unchanged
- **WHEN** 完成本变更后打开仪表盘
- **THEN** 仍只请求既有仪表盘统计与活动只读接口
- **AND** 测试用例子区的项目卡数值来自该次统计响应中的 `cases.breakdown` 项目项，而不是前端另行请求用例项目列表后再本地拼卡

#### Scenario: Case totals still match project rows
- **WHEN** 统计响应同时给出 `cases.total` 与项目维度 `cases.breakdown`
- **THEN** `cases.total` 等于各项目用例数之和（无项目时为 0）
