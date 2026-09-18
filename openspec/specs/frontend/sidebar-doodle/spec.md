# frontend/sidebar-doodle Specification

## Purpose
定义工作台侧栏导航图标色块与退出按钮的 doodle 视觉行为，使模块可辨识、危险操作醒目，且颜色全部来自设计令牌。

## Requirements

### Requirement: Nav icon uses module color fill

侧栏每个导航项的图标方盒 MUST 以该路由已绑定的模块色填充，并保留墨色粗边。Lucide 描边 MUST 使用 `--ink`，以保证在浅色模块底上可读。Active 与 hover 状态 MUST NOT 把图标方盒改回白底。

#### Scenario: Default item shows module-colored icon box

- **WHEN** 用户展开侧栏并查看任一已映射模块色的导航项
- **THEN** 该项图标方盒底色为对应模块色，边框为墨色，内部图标为墨色描边

#### Scenario: Active item keeps colored icon box

- **WHEN** 当前路由对应的导航项处于 active
- **THEN** 该项图标方盒仍为模块色底，不得回退为白底

### Requirement: Logout control uses marker red

展开态「退出」按钮 MUST 呈现马克笔红实心底、墨色边框与扁平偏移阴影，文字为浅色以保证对比。折叠态退出图标控件 MUST 使用同一红色语义，不得保留白底。

#### Scenario: Expanded logout looks like doodle primary danger

- **WHEN** 侧栏展开并显示账号区「退出」
- **THEN** 按钮为红色实心底、墨边、扁平阴影，文案「退出」为浅色

#### Scenario: Collapsed logout matches red semantic

- **WHEN** 侧栏折叠并显示退出图标按钮
- **THEN** 该按钮底色为同一马克笔红，边框为墨色
