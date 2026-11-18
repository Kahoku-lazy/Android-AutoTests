# Delta: frontend-l3-content-block

## MODIFIED Requirements

### Requirement: Nested composition is bounded
块允许的组合形态为「`.doc-section` 分区内嵌 `AppCard` 数据块」以及「`AppCard` 数据块内嵌 `KpiCard` / 图表 / 表格」；系统 MUST NOT 用 `.doc-section` 包裹单条数据卡，也 MUST NOT 用 `AppCard` 包裹 `.doc-section`。

#### Scenario: Report list composes section then data block
- **WHEN** 检查 `/reports` 的「报告概览」与「测试报告」分区
- **THEN** 每个分区是 `.doc-section`，其内部的指标卡 / 表格卡是 `.ac-card`；不存在 `AppCard` 包 `.doc-section` 的反向嵌套
