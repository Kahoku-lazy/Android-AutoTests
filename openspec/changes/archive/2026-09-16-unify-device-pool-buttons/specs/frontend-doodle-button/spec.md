## Purpose

定义 Doodle Craft「硬边按键皮肤」：一组按键在需要统一外观时共用的几何（墨色实边、近直角、零模糊偏移硬阴影与 hover 上移），以及页面内按键按角色分配底色的规则和皮肤的作用域约束，使同一页面内不再并存多套圆角/边框/阴影。

## ADDED Requirements

### Requirement: Hard-edge button skin has a single geometry source

系统 SHALL 以「硬边按键皮肤」作为需要该外观的页面按键的唯一几何：2px 墨色实边、2px 近直角、零模糊偏移阴影 `2px 2px 0 0 var(--ink)`，hover 与键盘聚焦时左上位移 1px 且阴影增至 `3px 3px 0 0 var(--ink)`。该几何 SHALL 与侧栏「退出」按钮（`frontend/sidebar-doodle`）一致，MUST NOT 自创第二套硬边几何或再次引入模糊阴影。

#### Scenario: Skin geometry matches the sidebar logout control

- **WHEN** 在浏览器测量设备管理页任一按键的计算样式
- **THEN** `border-width` 为 `2px`、`border-style` 为 `solid`、`border-color` 为 `--ink` 的计算值、`border-radius` 四角均为 `2px`
- **AND** `box-shadow` 为 `2px 2px 0 0` 加墨色，且模糊半径为 `0`

#### Scenario: Hover lifts the button and deepens the shadow

- **WHEN** 指针悬停或键盘聚焦任一按键
- **THEN** 计算 `transform` 呈左上位移 1px，`box-shadow` 偏移增至 `3px 3px 0 0`

### Requirement: Interactive text stays readable on every assigned tone

按键文字色 SHALL 为 `var(--ink)`；每个已分配底色上的文字与其底色计算对比度 MUST 不低于 **4.5:1**。系统 MUST NOT 采用会跌破该阈值的组合（例如柠黄底配白字）。当按键沿用深色底色时（例如 Element Plus 实心 `type="danger"` 的 `--el-color-danger`），文字色 SHALL 改用主题已有的浅色令牌而非墨色。

#### Scenario: Contrast holds on all four assigned tones

- **WHEN** 测量「未选中天蓝」「选中柠黄」「局域网紫」「刷新绿」四类按键的文字色与底色并计算对比度
- **THEN** 四组对比度均不低于 `4.5:1`

#### Scenario: Solid danger keeps light text on its dark background

- **WHEN** 测量弹窗内实心 `type="danger"` 按钮（未点名按键，沿用 `--el-color-danger` 深红底）
- **THEN** 其文字色为浅色令牌而非 `--ink`
- **AND** 文字与底色对比度不低于 `4.5:1`

### Requirement: Device-management button groups assign tones by role

设备管理页（`/devices`）按键底色 SHALL 按角色分配：切换/分段类控件（显示行数、全部设备·在线·使用中、表格·卡片）未选中为 `var(--c-workflow)`、选中为 `var(--c-dashboard)`；「局域网」为 `var(--c-element)`；「刷新」为 `var(--c-device)`。其余按键（分页、表格操作列、卡片操作、弹窗、空错态重试）SHALL 沿用各自既有语义底色，MUST NOT 被压成同一种底色。切换类选中态 SHALL 与既有分段控件（`AppTabs` / `el-radio-button`）同口径。

#### Scenario: Toggle groups show blue when unselected and yellow when selected

- **WHEN** 在设备管理页切换「表格 / 卡片」、「显示行数」或任一筛选 Tab
- **THEN** 未选中项底色为天蓝 `var(--c-workflow)`，选中项底色为柠黄 `var(--c-dashboard)`
- **AND** 选中态底色与 `AppTabs` 选中态同值

#### Scenario: Named action buttons keep their assigned hues

- **WHEN** 查看设备管理页工具条
- **THEN** 「局域网」底色为薰衣草紫 `var(--c-element)`，「刷新」底色为薄荷绿 `var(--c-device)`

#### Scenario: Unnamed buttons keep semantic backgrounds

- **WHEN** 查看分页、表格操作列、卡片操作与弹窗按键
- **THEN** 每个按键保留原有语义底色（危险 / 警告 / 主色 / 卡片纸色），不被统一成同一颜色

### Requirement: Skin scope is limited to the device-management page

该皮肤 SHALL 由设备管理页作用域（`.device-workbench`）承载。共享件 `FilterTabs` / `ErrorState` 与 `.wb-btn` 的默认皮肤，以及其它页面的按键外观，MUST NOT 因此改变；系统 MUST NOT 把设备管理页的配色写入共享组件或全局主题。

#### Scenario: Other pages keep their previous button appearance

- **WHEN** 打开 `/inspector`、`/ai-assistant/agents`、`/cases` 等使用共享 `FilterTabs` / `ErrorState` / `.wb-btn` 的页面
- **THEN** 这些页面的按键几何与配色与变更前一致

#### Scenario: Shared components are not modified

- **WHEN** 检索本次变更对 `FilterTabs.vue`、`ErrorState.vue`、`workbench-theme.css` 与 `style.css` 的差异
- **THEN** 四者均无改动，设备管理页的外观差异仅由页面作用域选择器产生
