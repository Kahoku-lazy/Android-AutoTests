## Purpose

定义 L1 侧栏在 hand-drawn doodle 主题下的可见视觉行为：对齐 `temps/hand-drawn-doodle-sidebar.html` 的侧栏观感，同时保留现有导航文案、路由与 Lucide SVG 图标。

## ADDED Requirements

### Requirement: Sidebar chrome matches hand-drawn paper shell
系统 SHALL 以暖白纸面作为侧栏底色，并以墨色虚线（非粗实线）作为侧栏与主区的分隔。品牌区与底栏 SHALL 使用同风格虚线分隔。

#### Scenario: Sidebar shows dashed rail and warm paper
- **WHEN** 用户进入带侧栏的工作台页面
- **THEN** 侧栏背景为暖白纸色，右侧为墨色虚线分隔，而非粗实线挡板观感

### Requirement: Nav labels and Lucide icons are preserved
系统 MUST 保留现有侧栏导航中文文案与 Lucide SVG 图标语义（`data-lucide` / 现有 icon 名）。视觉改造 MUST NOT 用字母方块替换业务 SVG。

#### Scenario: Labels and icons unchanged in meaning
- **WHEN** 用户查看侧栏导航项
- **THEN** 各入口中文名称与现网一致，且仍渲染对应 Lucide SVG（可外包描边方盒）

### Requirement: Active and hover use doodle emphasis
系统 SHALL 在导航项 hover 时使用浅黄强调并允许轻微旋转；在 active 时使用黄底、墨色虚线描边，以及偏移色块阴影（阴影色优先模块色令牌）。折叠态 MUST 仍可识别当前项。

#### Scenario: Active item shows yellow plate and offset shadow
- **WHEN** 用户位于某一模块路由
- **THEN** 对应侧栏项呈现黄底 + 虚线描边 + 偏移阴影，且不阻挡点击

#### Scenario: Hover does not break navigation
- **WHEN** 用户悬停非当前导航项并点击
- **THEN** 路由正常跳转，hover 样式不拦截交互

### Requirement: Brand mark follows template geometry with theme colors
品牌区 SHALL 提供方形描边 mark（黄底 + 墨色描边 + 青绿/模块色偏移阴影），文案「AI」「自动化测试平台」MUST 保留可读。

#### Scenario: Brand text remains readable
- **WHEN** 侧栏展开
- **THEN** 用户仍能读到「AI」与「自动化测试平台」（或等价现有品牌文案）

### Requirement: Interaction behavior unchanged
折叠、拖拽调宽、账号切换菜单、退出登录的行为 MUST 保持可用；本变更 MUST NOT 改变路由 path 或鉴权流程。

#### Scenario: Collapse and account menu still work
- **WHEN** 用户折叠侧栏或打开账号菜单并退出
- **THEN** 行为与改前一致（可折叠、可切换/退出），仅外观变化
