## ADDED Requirements

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

## MODIFIED Requirements

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
