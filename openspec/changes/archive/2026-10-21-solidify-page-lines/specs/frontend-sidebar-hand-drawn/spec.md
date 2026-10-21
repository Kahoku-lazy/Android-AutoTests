## MODIFIED Requirements

### Requirement: Sidebar chrome matches hand-drawn paper shell

系统 SHALL 以暖白纸面作为侧栏底色，并以 2.5px 墨色实线作为侧栏与主区的分隔。侧栏线型 SHALL 由 `.sidebar` 作用域内的具名令牌 `--sidebar-line` 决定，其值 SHALL 为 `solid`，MUST NOT 借用共享组件令牌或其它模块令牌来决定自身线型。品牌区与底栏 SHALL 使用同风格实线分隔。

#### Scenario: Sidebar shows dashed rail and warm paper

- **WHEN** 用户进入带侧栏的工作台页面
- **THEN** 侧栏背景为暖白纸色，右侧为墨色实线分隔，而非虚线或粗实线挡板观感
- **AND** 该线型来自 `.sidebar` 作用域内的 `--sidebar-line`

### Requirement: Active and hover use doodle emphasis

系统 SHALL 在导航项 hover 时使用浅黄强调并允许轻微旋转；在 active 时使用黄底、墨色实线描边，以及偏移色块阴影（阴影色优先模块色令牌）。折叠态 MUST 仍可识别当前项。

#### Scenario: Active item shows yellow plate and offset shadow

- **WHEN** 用户位于某一模块路由
- **THEN** 对应侧栏项呈现黄底 + 实线描边 + 偏移阴影，且不阻挡点击

#### Scenario: Hover does not break navigation

- **WHEN** 用户悬停非当前导航项并点击
- **THEN** 路由正常跳转，hover 样式不拦截交互
