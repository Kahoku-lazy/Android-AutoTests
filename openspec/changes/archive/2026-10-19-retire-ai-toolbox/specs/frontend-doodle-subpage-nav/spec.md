## REMOVED Requirements

### Requirement: Three navigation templates cover platform depth

**Reason**: 该需求把「侧栏子项」列为 AI 助手的导航模版，而 AI 助手已收为单一入口、不再有子路由；继续保留会让这条导航不变量失真。
**Migration**: 由新增的「Two navigation templates cover platform depth」承接面包屑条与列表行进入两类模版。

## ADDED Requirements

### Requirement: Two navigation templates cover platform depth

系统 MUST 用且只用下列两种模版表达子页导航，不得在页内再叠与侧栏重复的顶栏 Tab：

1. 面包屑条：Hub → 工作台 → 叶子（元素定位、用例管理；本轮不改页面流画布页头结构以外的画布）
2. 列表行进入：报告 run/task/cases 与同类列表进详情，详情正文顶部提供回列表

AI 助手只有一个侧栏入口，不再占用「侧栏子项」模版。

#### Scenario: AI has a single entry

<!-- 场景名沿自变更前：AI 工具箱与侧栏子项均已下线，本场景改为守住「AI 助手只有一个入口」 -->

- **WHEN** 用户进入 AI 助手
- **THEN** 侧栏只有一个「AI 助手」入口，页内没有第二套顶栏 Tab
- **AND** 页头标题固定为平台小助手
- **AND** 侧栏与路由既不出现评测中心，也不出现知识库、AI 工具箱

#### Scenario: AI deep link returns to the single entry

<!-- 场景名沿自变更前：子项已收起，回退目标统一为 AI 助手入口 -->

- **WHEN** 用户打开任务详情或智能体编辑页
- **THEN** `.doc-body` 顶部提供回到 AI 助手入口的可见回退
- **AND** 激活后进入 `/ai-assistant/agents`
- **AND** `.wb-header` 内没有该回退控件

#### Scenario: Report list row enters detail in the same shell

- **WHEN** 用户在报告列表点击一行 run
- **THEN** 在同一主区内打开详情，不新开浏览器标签
- **AND** 详情 `.doc-body` 顶部提供回列表
