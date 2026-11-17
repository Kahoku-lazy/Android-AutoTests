## MODIFIED Requirements

### Requirement: L2 plus pages expose visible back navigation

深度大于单页的工作台页面（Hub 以下工作台 / 叶子、报告详情链、AI 深链）MUST 在 L2 页面 `.doc-body` 顶部提供可见回退：返回芯片、波浪面包屑，或二者并存。系统 SHALL NOT 把浏览器原生 history 当作唯一回退手段。系统 SHALL NOT 把该回退导航渲染在 `.wb-header` 内。单页模块（仪表盘、设备管理）SHALL NOT 为凑齐导航而伪造祖先链。

#### Scenario: Report detail shows list ancestor

- **WHEN** 用户打开某次 run 的报告详情
- **THEN** `.doc-body` 顶部可见回到「测试报告」列表的控件
- **AND** `.wb-header` 内没有该回退控件
- **AND** 激活该控件后路由回到报告列表，不新开浏览器标签

#### Scenario: Element file leaf shows Hub and workbench ancestors

- **WHEN** 用户打开用例管理某项目下的文件页
- **THEN** `.doc-body` 顶部可见可点的祖先（用例管理 Hub、当前项目工作台）与当前文件名
- **AND** 当前项不可再点，祖先可点并进入对应路由
- **AND** `.wb-header` 只显示主标题与副标题（可含品牌图标）

#### Scenario: Case workbench shows Hub ancestor

- **WHEN** 用户打开用例管理某项目工作台
- **THEN** `.doc-body` 顶部可见回到项目列表的控件
- **AND** 激活后路由回到 `/cases`

### Requirement: Two navigation templates cover platform depth

系统 MUST 用且只用下列两种模版表达子页导航，不得在页内再叠与侧栏重复的顶栏 Tab：

1. 面包屑条：Hub → 工作台 → 叶子（用例管理）
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
