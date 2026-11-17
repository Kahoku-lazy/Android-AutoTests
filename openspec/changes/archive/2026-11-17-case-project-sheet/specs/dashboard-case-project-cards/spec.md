## MODIFIED Requirements

### Requirement: Case KPI cards are one per case-manager project

仪表盘「平台概览」章节「测试用例」子区的用例项目卡 SHALL 为当前用户可见的每一个用例项目渲染一张 KPI 入口卡。卡片标题 SHALL 为项目名称，主数值 SHALL 为该项目对应用例表的行数（含 0）。自动化项目计自动化表，功能项目计功能表。系统 MUST NOT 再以 Android用例、Web用例、API用例、功能业务（或语义等价的固定类型标签）作为该子区的入口卡。

#### Scenario: Projects render as case cards

- **WHEN** 当前用户拥有至少一个用例项目，且仪表盘统计已成功返回
- **THEN** 「平台概览」章节内「测试用例」子区出现与项目数量相同的入口卡
- **AND** 每张卡的标题为对应项目名称，主数值为该项目用例数
- **AND** 页面上不可见文案「Android用例」「Web用例」「功能业务」作为该子区入口卡标题

#### Scenario: Zero-case project still has a card

- **WHEN** 用户刚创建了一个尚无用例的项目，并再次打开或刷新仪表盘
- **THEN** 「测试用例」子区出现以该项目名称命名的入口卡，主数值为 0

### Requirement: Case card enters the matching project workspace

测试用例子区每张项目卡 SHALL 通过**整卡激活**导航到该项目的用例表，路径含该项目 id。MUST NOT 在卡内渲染独立「进入」按钮或同类进入控件。MUST NOT 把所有项目卡统一指向无项目上下文的通用 `/cases` 列表（可作为空态入口，不得作为已有项目卡的目标）。MUST NOT 再导航到文件详情或目录工作台。

#### Scenario: Clicking a project card opens that project

- **WHEN** 用户点击名称为某已存在项目的用例入口卡
- **THEN** 进入该项目的用例表（路径含该项目 id，且不是文件详情路径）
- **AND** 卡片内不存在「进入」按钮
