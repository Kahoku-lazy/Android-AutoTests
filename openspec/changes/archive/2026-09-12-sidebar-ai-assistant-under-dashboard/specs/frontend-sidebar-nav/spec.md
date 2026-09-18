## Purpose

定义侧栏导航入口的分组顺序与分组标题可见性，使「AI 助手」紧挨仪表盘且不出现重复的「AI助手」分组标题。

## ADDED Requirements

### Requirement: AI assistant sits under dashboard
系统 SHALL 将「AI 助手」导航项（含其可展开子项）放在「仪表盘」正下方。系统 MUST NOT 在二者之间插入其它导航项。

#### Scenario: Order on workbench sidebar
- **WHEN** 用户打开带侧栏的工作台页面且侧栏展开
- **THEN** 导航列表中「仪表盘」的下一项是「AI 助手」

### Requirement: Duplicate AI assistant group label is absent
系统 MUST NOT 渲染独立分组标题「AI助手」。父项文案「AI 助手」MUST 保留。

#### Scenario: No group heading AI助手
- **WHEN** 用户查看展开态侧栏
- **THEN** 不存在仅含「AI助手」文案的分组标题节点，且仍可见可展开的「AI 助手」入口
