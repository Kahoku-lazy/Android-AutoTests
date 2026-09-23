## MODIFIED Requirements

### Requirement: Existing KPI cards and APIs remain the data surface
章节重组 MUST NOT 把仪表盘改成可写运营台：KPI 入口卡、趋势 `AppCard`、活动时间线仍直映只读 stats/activities 接口。系统 MUST 继续只请求既有仪表盘统计与活动只读接口，MUST NOT 为展示测试资产而新增写操作或在前端推算业务指标。`cases.breakdown` SHALL 按当前用户的用例项目维度返回（每项含项目标识、名称与用例数）；MUST NOT 再要求该字段保持测试类型拆分或与重组前类型键一一对应。`cases.total` SHALL 仍为当前用户文档用例合计。元素类 KPI 的数据源字段不受本条变更。

#### Scenario: Stats endpoints unchanged
- **WHEN** 完成本变更后打开仪表盘
- **THEN** 仍只请求既有仪表盘统计与活动只读接口
- **AND** 测试用例子区的项目卡数值来自该次统计响应中的 `cases.breakdown` 项目项，而不是前端另行请求用例项目列表后再本地拼卡

#### Scenario: Case totals still match project rows
- **WHEN** 统计响应同时给出 `cases.total` 与项目维度 `cases.breakdown`
- **THEN** `cases.total` 等于各项目用例数之和（无项目时为 0）
