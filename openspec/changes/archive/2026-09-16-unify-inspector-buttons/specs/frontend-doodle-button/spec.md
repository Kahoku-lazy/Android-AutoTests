## RENAMED Requirements

- FROM: `### Requirement: Skin scope is limited to the device-management page`
- TO: `### Requirement: Skin scope is a registered carrier-page list`

## MODIFIED Requirements

### Requirement: Skin scope is a registered carrier-page list

硬边按键皮肤 SHALL 由「已登记承载页清单」承载，当前清单为设备管理页（`.device-workbench`）与设备检查器（`.inspector-workbench`）。新增承载页 MUST NOT 改变皮肤几何：唯一几何来源仍为侧栏「退出」按钮（2px 墨色实边、2px 近直角、零模糊偏移阴影 `2px 2px 0 0 var(--ink)`）。共享件 `FilterTabs` / `ErrorState` / `DoodleBtn` 与全局主题（`workbench-theme.css` / `style.css` / `tokens.css`）的默认皮肤 MUST NOT 因承载页增加而改变。系统 MUST NOT 把任一承载页的模块配色写入共享组件或全局主题。

#### Scenario: Other pages keep their previous button appearance

- **WHEN** 打开 `/ai-assistant/agents`、`/cases` 等**未登记**页面
- **THEN** 这些页面的按键几何与配色与变更前一致

#### Scenario: Registered carrier pages share one geometry

- **WHEN** 打开 `/devices` 与 `/inspector`
- **THEN** 两页按键的 `border-width` 为 `2px`、`border-style` 为 `solid`、四角 `border-radius` 均为 `2px`、`box-shadow` 为 `2px 2px 0 0` 加墨色且模糊半径为 `0`

#### Scenario: Shared components are not modified

- **WHEN** 检索本次变更对 `FilterTabs.vue`、`ErrorState.vue`、`DoodleBtn.vue`、`workbench-theme.css`、`style.css` 与 `tokens.css` 的差异
- **THEN** 六者均无改动，承载页的外观差异仅由各自的页面作用域选择器产生

## ADDED Requirements

### Requirement: Device-inspector keys adopt the hard-edge skin

设备检查器页「需要硬边外观」的按键 MUST 采用已登记的硬边几何，并沿用各自既有语义底色；工具条原生 `button` 与弹窗 `el-button` MUST 由该页页面作用域统一覆写。文字色 SHALL 为 `var(--ink)`；沿用深色底色的按键（如墨黑底「获取」）文字 SHALL 使用主题浅色令牌，且文字与底色对比度 MUST 不低于 4.5:1。`text` 型图标按键 MUST NOT 被套上边框、背景与硬阴影。

#### Scenario: Toolbar and dialog keys share one geometry

- **WHEN** 在浏览器测量 `/inspector` 工具条任一按键与「保存到元素定位」弹窗底部任一按键的计算样式
- **THEN** 两者 `border-radius` 四角均为 `2px`、`box-shadow` 均为 `2px 2px 0 0` 加墨色且模糊半径为 `0`
- **AND** hover 时计算 `transform` 呈左上位移 1px，`box-shadow` 偏移增至 `3px 3px`

#### Scenario: Disabled key drops its offset shadow

- **WHEN** 未选择设备或尚无快照，工具条上相应按键处于 disabled
- **THEN** 该按键 `opacity` 为 `0.5` 且 `box-shadow` 为 `none`，与可用态不混淆

#### Scenario: Dark-background key keeps readable text

- **WHEN** 测量「获取」按键的文字色与背景色并计算对比度
- **THEN** 文字色为主题浅色令牌而非 `--ink`，且对比度不低于 `4.5:1`

#### Scenario: Text-type icon key is excluded from the skin

- **WHEN** 测量快照抽屉内 `text` 型 `type="danger"` 删除键
- **THEN** 其计算样式无可见边框、无背景色、无硬阴影，保持无底无边的图标形态
