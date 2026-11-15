## MODIFIED Requirements

### Requirement: Case KPI cards are one per case-manager project

仪表盘「平台概览」章节「测试用例」子区的用例项目卡 SHALL 为当前用户可见的每一个用例项目渲染一张 KPI 入口卡。卡片标题 SHALL 为项目名称，主数值 SHALL 为该项目下文档用例条数（含 0）。系统 MUST NOT 再以 Android用例、Web用例、API用例、功能业务（或语义等价的固定类型标签）作为该子区的入口卡。

#### Scenario: Projects render as case cards

- **WHEN** 当前用户拥有至少一个用例项目，且仪表盘统计已成功返回
- **THEN** 「平台概览」章节内「测试用例」子区出现与项目数量相同的入口卡
- **AND** 每张卡的标题为对应项目名称，主数值为该项目用例数
- **AND** 页面上不可见文案「Android用例」「Web用例」「功能业务」作为该子区入口卡标题

#### Scenario: Zero-case project still has a card

- **WHEN** 用户刚创建了一个尚无用例的项目，并再次打开或刷新仪表盘
- **THEN** 「测试用例」子区出现以该项目名称命名的入口卡，主数值为 0
