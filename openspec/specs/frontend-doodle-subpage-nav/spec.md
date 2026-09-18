# frontend-doodle-subpage-nav Specification

## Purpose
定义工作台子页在 L2 页头区内的可见回退导航：波浪面包屑与返回芯片至少其一，覆盖面包屑条、侧栏子项、列表行进入三种模版，使人始终能回到上一层而不依赖浏览器后退。

## Requirements

### Requirement: L2 plus pages expose visible back navigation

深度大于单页的工作台页面（Hub 以下工作台 / 叶子、报告详情链、AI 深链）MUST 在 L2 页面 `.doc-body` 顶部提供可见回退：返回芯片、波浪面包屑，或二者并存。系统 SHALL NOT 把浏览器原生 history 当作唯一回退手段。系统 SHALL NOT 把该回退导航渲染在 `.wb-header` 内。单页模块（仪表盘、设备管理、设备检查器）SHALL NOT 为凑齐导航而伪造祖先链。

#### Scenario: Report detail shows list ancestor

- **WHEN** 用户打开某次 run 的报告详情
- **THEN** `.doc-body` 顶部可见回到「测试报告」列表的控件
- **AND** `.wb-header` 内没有该回退控件
- **AND** 激活该控件后路由回到报告列表，不新开浏览器标签

#### Scenario: Element file leaf shows Hub and workbench ancestors

- **WHEN** 用户打开元素定位某项目下的文件页
- **THEN** `.doc-body` 顶部可见可点的祖先（元素定位 Hub、当前项目工作台）与当前文件名
- **AND** 当前项不可再点，祖先可点并进入对应路由
- **AND** `.wb-header` 只显示主标题与副标题（可含品牌图标）

#### Scenario: Case workbench shows Hub ancestor

- **WHEN** 用户打开用例管理某项目工作台
- **THEN** `.doc-body` 顶部可见回到项目列表的控件
- **AND** 激活后路由回到 `/cases`

### Requirement: Three navigation templates cover platform depth

系统 MUST 用且只用下列三种模版表达子页导航，不得在页内再叠与侧栏重复的顶栏 Tab：

1. 面包屑条：Hub → 工作台 → 叶子（元素定位、用例管理；本轮不改页面流画布页头结构以外的画布）
2. 侧栏子项：AI 助手四子路由由侧栏切换，页内不再叠一套同等导航
3. 列表行进入：报告 run/task/cases 与同类列表进详情，详情正文顶部提供回列表

#### Scenario: AI four tabs stay in the sidebar

- **WHEN** 用户在平台小助手、工具箱、知识库、评测中心之间切换
- **THEN** 切换发生在侧栏子项，页内没有第二套与四子项等价的顶栏 Tab
- **AND** 页头标题随路由更换

#### Scenario: AI deep link returns to its sidebar child

- **WHEN** 用户打开任务详情、Skill 查看或智能体编辑页
- **THEN** `.doc-body` 顶部提供回到对应子项的可见回退（任务列表 / 工具箱 / 平台小助手）
- **AND** 激活后进入该子项路由，而不是笼统的 `/ai-assistant`
- **AND** `.wb-header` 内没有该回退控件

#### Scenario: Report list row enters detail in the same shell

- **WHEN** 用户在报告列表点击一行 run
- **THEN** 在同一主区内打开详情，不新开浏览器标签
- **AND** 详情 `.doc-body` 顶部提供回列表

### Requirement: Crumb visuals use registered tokens

祖先链接 MUST 使用登记令牌呈现波浪下划线；当前项 MUST 使用登记的马克笔高亮。颜色、间距、字号 MUST 取自 `tokens.css` 已登记变量（可经 `--comp-*` 组件令牌引用颜色原子）。SHALL NOT 在组件样式中直写十六进制色。

#### Scenario: Current crumb is highlighted without a link

- **WHEN** 面包屑渲染不少于两级
- **THEN** 最后一级不是可激活链接，并带马克笔高亮
- **AND** 更早的每一级可激活

#### Scenario: Styles consume tokens only

- **WHEN** 检查面包屑与返回芯片的样式声明
- **THEN** 色值、字号、间距、阴影均引用令牌
- **AND** 不出现未登记的纯色字面量
