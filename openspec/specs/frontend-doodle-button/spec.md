# frontend-doodle-button Specification

## Purpose
定义 Doodle Craft「硬边按键皮肤」：一组按键在需要统一外观时共用的几何（墨色实边、近直角、零模糊偏移硬阴影与 hover 上移），以及页面内按键按角色分配底色的规则和皮肤的作用域约束，使同一页面内不再并存多套圆角/边框/阴影。

## Requirements

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

设备管理页（`/devices`）按键底色 SHALL 按角色分配：切换/分段类控件（显示行数、全部设备·在线·使用中、表格·卡片）未选中为 `var(--c-workflow)`、选中为 `var(--c-dashboard)`；「局域网」为 `var(--c-element)`；「刷新」为 `var(--c-device)`。其余按键（分页、表格操作列、卡片操作、弹窗、空错态重试）SHALL 沿用各自既有语义底色，MUST NOT 被压成同一种底色。切换类选中态 SHALL 与既有分段控件（`AppTabs` / `el-radio-button`）同口径。「显示行数」组 SHALL 只有单一选项（`5`），因而只呈现选中态；其未选中态规则 MAY 保留以备选项增加，MUST NOT 仅因当前不可达而被判为未实现。

#### Scenario: Toggle groups show blue when unselected and yellow when selected

- **WHEN** 在设备管理页切换「表格 / 卡片」或任一筛选 Tab
- **THEN** 未选中项底色为天蓝 `var(--c-workflow)`，选中项底色为柠黄 `var(--c-dashboard)`
- **AND** 选中态底色与 `AppTabs` 选中态同值

#### Scenario: Page-size group has a single option and renders the selected state

- **WHEN** 查看设备管理页「显示行数」组
- **THEN** 该组只渲染一个选项「5」，且其底色为选中态柠黄 `var(--c-dashboard)`
- **AND** 不渲染选项「10」

#### Scenario: Named action buttons keep their assigned hues

- **WHEN** 查看设备管理页工具条
- **THEN** 「局域网」底色为薰衣草紫 `var(--c-element)`，「刷新」底色为薄荷绿 `var(--c-device)`

#### Scenario: Unnamed buttons keep semantic backgrounds

- **WHEN** 查看分页、表格操作列、卡片操作与弹窗按键
- **THEN** 每个按键保留原有语义底色（危险 / 警告 / 主色 / 卡片纸色），不被统一成同一颜色

### Requirement: Skin scope is a registered carrier-page list

硬边按键皮肤 SHALL 由「已登记承载页清单」承载，当前清单为设备管理页（`.device-workbench`）、设备检查器（`.inspector-workbench`）与元素定位文件详情页（`.locator-workbench.file-view`）。新增承载页 MUST NOT 改变皮肤几何：唯一几何来源仍为侧栏「退出」按钮（2px 墨色实边、2px 近直角、零模糊偏移阴影 `2px 2px 0 0 var(--ink)`）。共享件 `FilterTabs` / `ErrorState` / `DoodleBtn` 与全局主题（`workbench-theme.css` / `style.css` / `tokens.css`）的默认皮肤 MUST NOT 因承载页增加而改变。系统 MUST NOT 把任一承载页的模块配色写入共享组件或全局主题。

#### Scenario: Other pages keep their previous button appearance

- **WHEN** 打开 `/ai-assistant/agents`、`/cases` 等**未登记**页面
- **THEN** 这些页面的按键几何与配色与变更前一致

#### Scenario: Registered carrier pages share one geometry

- **WHEN** 打开 `/devices`、`/inspector` 与元素定位文件详情页
- **THEN** 三页「需要硬边外观」的按键的 `border-width` 为 `2px`、`border-style` 为 `solid`、四角 `border-radius` 均为 `2px`、`box-shadow` 为 `2px 2px 0 0` 加墨色且模糊半径为 `0`

#### Scenario: Shared components are not modified

- **WHEN** 检索本次变更对 `FilterTabs.vue`、`ErrorState.vue`、`DoodleBtn.vue`、`workbench-theme.css`、`style.css` 与 `tokens.css` 的差异
- **THEN** 六者均无改动，承载页的外观差异仅由各自的页面作用域选择器产生

### Requirement: Locator file-view keys adopt the hard-edge skin

元素定位文件详情页（`.locator-workbench.file-view`）上「需要硬边外观」的按键 MUST 采用已登记的硬边几何。至少「删除」MUST 由该页页面作用域覆写，不得保留 Element Plus 默认圆角与无硬阴影的 `plain` 危险外观。删除键底色 SHALL 取已登记危险红令牌，文字色 SHALL 为浅色令牌（非 `--ink`），对比度 MUST 不低于 4.5:1。面包屑「返回目录」芯片 MAY 继续使用共享 `WorkbenchCrumbs` 既有硬边回退，MUST NOT 再造第二套返回键。共享件 `FilterTabs` / `ErrorState` / `DoodleBtn` 与全局主题 MUST NOT 因本页加入承载清单而被改写。

#### Scenario: Delete key shares logout geometry

- **WHEN** 在浏览器测量 `/elements` 文件详情页的「删除」按键与侧栏「退出」按键的计算样式
- **THEN** 两者 `border-width` 均为 `2px`、`border-style` 为 `solid`、四角 `border-radius` 均为 `2px`、`box-shadow` 均为 `2px 2px 0 0` 加墨色且模糊半径为 `0`
- **AND** 悬停「删除」时计算 `transform` 呈左上位移 1px，`box-shadow` 偏移增至 `3px 3px 0 0`

#### Scenario: Delete remains a dangerous action with readable text

- **WHEN** 测量该「删除」按键的底色与文字色
- **THEN** 底色为已登记危险红令牌、文字为浅色令牌
- **AND** 对比度不低于 `4.5:1`
- **AND** 点击仍先确认再删除（确认流程不变）

### Requirement: Device-inspector keys adopt the hard-edge skin

设备检查器页「需要硬边外观」的按键 MUST 采用已登记的硬边几何；工具条原生 `button`、设备选择触发键与弹窗 `el-button` MUST 由该页页面作用域统一覆写。**工具条按键**的底色 SHALL 按可用性分配：可用为天蓝 `var(--c-workflow)`，不可用为灰 `var(--color-ink-79)`；**设备选择触发键不适用这套可用性配色**——它始终可用、MUST NOT 呈灰键，其外观（白底、无阴影、保留墨线边框）由 `device-inspector-page` 的「分组选择控件与设备选择控件」定义，本 capability 只约束它的硬边几何与「由页面作用域覆写」两项。分组筹码属**切换类控件**，SHALL 按平台既有切换口径配色：未选中为天蓝 `var(--c-workflow)`、选中为柠黄 `var(--c-dashboard)`。上述底色上的文字色 SHALL 为 `var(--ink)`，且文字与底色对比度 MUST 不低于 4.5:1。不可用按键 MUST NOT 以原生 `disabled` 静默拦截点击，MUST NOT 以整体 `opacity` 表达不可用：不可用态由灰底 + 点击提示「按键不可用，请先选择设备」承担。`text` 型图标按键 MUST NOT 被套上边框、背景与硬阴影。

#### Scenario: Toolbar and dialog keys share one geometry

- **WHEN** 在浏览器测量 `/inspector` 工具条任一按键与「保存到元素定位」弹窗底部任一按键的计算样式
- **THEN** 两者 `border-radius` 四角均为 `2px`、`box-shadow` 均为 `2px 2px 0 0` 加墨色且模糊半径为 `0`
- **AND** hover 时计算 `transform` 呈左上位移 1px，`box-shadow` 偏移增至 `3px 3px`

#### Scenario: Available key is sky blue with readable text

- **WHEN** 已选定可用设备且已载入快照，测量「获取」「历史快照」「保存到元素定位」的底色与文字色
- **THEN** 底色为 `var(--c-workflow)`、文字色为 `var(--ink)`，且三者对比度均不低于 `4.5:1`

#### Scenario: Disabled key drops its offset shadow

- **WHEN** 未选择设备或尚无快照，工具条上相应按键处于不可用态
- **THEN** 该按键底色为灰 `var(--color-ink-79)` 且 `box-shadow` 为 `none`（撤掉位移阴影），与可用态的蓝底 + 硬阴影不混淆
- **AND** 其 `opacity` 为 `1`：不可用态由灰底承担，不再用整体降透明度表达；点击该按键提示「按键不可用，请先选择设备」

#### Scenario: Select trigger is not part of the availability tone

- **WHEN** 未选择设备时测量设备选择触发键的底色与 `box-shadow`
- **THEN** 其底色为白（纸色）、`box-shadow` 为 `none`，既有别于可用态的天蓝底，也不等于不可用态的灰底
- **AND** 该外观只在 `device-inspector-page` 的「分组选择控件与设备选择控件」中被定义，本 capability 不重复定义其底色

#### Scenario: Dark-background key keeps readable text

<!-- 场景名沿自变更前：本页原墨黑底「获取」已改为天蓝底，本 Scenario 改为守住「文字与底色对比度」这一不变量 -->

- **WHEN** 测量 `/inspector` 页任一按键的文字色与底色并计算对比度
- **THEN** 该页按键底色只有浅色系（天蓝 `--c-workflow` / 柠黄 `--c-dashboard` / 灰 `--color-ink-79` / 纸色），文字色为 `var(--ink)`，全部对比度不低于 `4.5:1`
- **AND** 若该页此后引入深色底按键，其文字色 MUST 改用主题浅色令牌而非 `--ink`，且对比度仍不低于 `4.5:1`

#### Scenario: Text-type icon key is excluded from the skin

- **WHEN** 测量快照抽屉内 `text` 型 `type="danger"` 删除键
- **THEN** 其计算样式无可见边框、无背景色、无硬阴影，保持无底无边的图标形态

#### Scenario: Partition chips follow the toggle tone convention

- **WHEN** 测量 `/inspector` 页面分区筹码的底色
- **THEN** 未选中项为天蓝 `var(--c-workflow)`、选中项为柠黄 `var(--c-dashboard)`，与 `AppTabs` / `el-radio-button` 的选中态同值
- **AND** 筹码沿用硬边几何（`border-radius` 四角 `2px`、零模糊硬阴影）

### Requirement: Snapshot drawer clear key adopts the danger hard-edge skin

历史快照抽屉的「一键清空」是**带文字标签的动作键**，MUST 采用已登记的硬边按键皮肤几何（与侧栏「退出」键同源：2px 墨色实边、2px 近直角、零模糊偏移阴影 `2px 2px 0 0` 加墨色，hover 与键盘聚焦时左上位移 1px 且阴影增至 `3px 3px 0 0`），MUST NOT 保持 Element Plus text 型「无边框、无底色、无硬阴影」的文字键外观。其底色 SHALL 取已登记的**深**危险红令牌（Element Plus 实心 `danger` 的底色，即 `--color-red-46`；更浅的 `--app-marker-red` 与浅色文字只有 2.92:1，MUST NOT 用于本条），文字色 SHALL 为浅色令牌（非墨色），两者对比度 MUST 不低于 `4.5:1`。该键不可用时（本人尚无历史快照）SHALL 呈本页统一的灰键：底色为灰令牌、位移阴影撤除、`opacity` 保持 `1`；不可用期间点击 MUST NOT 弹出确认框、MUST NOT 发起清空请求。皮肤 MUST 由设备检查器页页面作用域承担，MUST NOT 改动共享件与全局主题。

#### Scenario: Clear key shares the logout geometry

- **WHEN** 在浏览器测量快照抽屉内「一键清空」按键与侧栏「退出」按键的计算样式（该键可用时）
- **THEN** 两者 `border-width` 均为 `2px`、`border-style` 均为 `solid`、`border-color` 均为墨色、四角 `border-radius` 均为 `2px`
- **AND** `box-shadow` 均为 `2px 2px 0 0` 加墨色且模糊半径为 `0`

#### Scenario: Clear key carries the danger tone with readable text

- **WHEN** 测量该键的底色与文字色
- **THEN** 底色为已登记**深**危险红令牌（不透明、非灰、非 `--app-marker-red`）、文字为浅色令牌（非墨色）
- **AND** 两者对比度不低于 `4.5:1`（实测约 `5.97:1`）

#### Scenario: Unavailable clear key drops to the page gray key

- **WHEN** 本人尚无历史快照，抽屉内的「一键清空」处于不可用态
- **THEN** 其底色为灰令牌、`box-shadow` 为 `none`、`opacity` 为 `1`，与可用态的红底 + 硬阴影可区分
- **AND** 点击它不弹出确认框、不发起清空请求、不改变列表

#### Scenario: Row delete icon key stays bare

- **WHEN** 测量同一抽屉内每行的 text 型 `type="danger"` 删除图标键
- **THEN** 其计算样式仍无可见边框、无背景色、无硬阴影，保持无底无边的图标形态
- **AND** 本需求不改变它的形状与点击行为（点击仍先确认再删除）
