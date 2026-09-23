## MODIFIED Requirements

### Requirement: Three navigation templates cover platform depth

系统 MUST 用且只用下列三种模版表达子页导航，不得在页内再叠与侧栏重复的顶栏 Tab：

1. 面包屑条：Hub → 工作台 → 叶子（元素定位、用例管理；本轮不改页面流画布页头结构以外的画布）
2. 侧栏子项：AI 助手三子路由由侧栏切换，页内不再叠一套同等导航
3. 列表行进入：报告 run/task/cases 与同类列表进详情，详情正文顶部提供回列表

#### Scenario: AI three tabs stay in the sidebar

- **WHEN** 用户在平台小助手、工具箱、知识库之间切换
- **THEN** 切换发生在侧栏子项，页内没有第二套与三子项等价的顶栏 Tab
- **AND** 页头标题随路由更换
- **AND** 侧栏与路由均不出现评测中心

#### Scenario: AI deep link returns to its sidebar child

- **WHEN** 用户打开任务详情、Skill 查看或智能体编辑页
- **THEN** `.doc-body` 顶部提供回到对应子项的可见回退（任务列表 / 工具箱 / 平台小助手）
- **AND** 激活后进入该子项路由，而不是笼统的 `/ai-assistant`
- **AND** `.wb-header` 内没有该回退控件

#### Scenario: Report list row enters detail in the same shell

- **WHEN** 用户在报告列表点击一行 run
- **THEN** 在同一主区内打开详情，不新开浏览器标签
- **AND** 详情 `.doc-body` 顶部提供回列表
