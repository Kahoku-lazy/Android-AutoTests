## MODIFIED Requirements

### Requirement: Case card enters the matching project workspace

测试用例子区每张项目卡 SHALL 通过**整卡激活**导航到该项目的用例工作台，MUST NOT 在卡内渲染独立「进入」按钮或同类进入控件。MUST NOT 把所有项目卡统一指向无项目上下文的通用 `/cases` 列表（可作为空态入口，不得作为已有项目卡的目标）。

#### Scenario: Clicking a project card opens that project

- **WHEN** 用户点击名称为某已存在项目的用例入口卡
- **THEN** 进入该项目工作台（路径含该项目 id）
- **AND** 卡片内不存在「进入」按钮
