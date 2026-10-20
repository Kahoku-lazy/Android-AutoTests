## MODIFIED Requirements

### Requirement: Skin scope is a registered carrier-page list

硬边按键皮肤 SHALL 由「已登记承载页清单」承载，当前清单为设备管理页（`.device-workbench`）。新增承载页 MUST NOT 改变皮肤几何：唯一几何来源仍为侧栏「退出」按钮（2px 墨色实边、2px 近直角、零模糊偏移阴影 `2px 2px 0 0 var(--ink)`）。共享件 `FilterTabs` / `ErrorState` / `DoodleBtn` 与全局主题（`workbench-theme.css` / `style.css` / `tokens.css`）的默认皮肤 MUST NOT 因承载页增加而改变。系统 MUST NOT 把任一承载页的模块配色写入共享组件或全局主题。

#### Scenario: Other pages keep their previous button appearance

- **WHEN** 打开 `/ai-assistant/agents`、`/cases` 等**未登记**页面
- **THEN** 这些页面的按键几何与配色与变更前一致

#### Scenario: Registered carrier pages share one geometry

- **WHEN** 打开 `/devices`
- **THEN** 该页「需要硬边外观」的按键的 `border-width` 为 `2px`、`border-style` 为 `solid`、四角 `border-radius` 均为 `2px`、`box-shadow` 为 `2px 2px 0 0` 加墨色且模糊半径为 `0`

#### Scenario: Shared components are not modified

- **WHEN** 检索本次变更对 `FilterTabs.vue`、`ErrorState.vue`、`DoodleBtn.vue`、`workbench-theme.css`、`style.css` 与 `tokens.css` 的差异
- **THEN** 六者均无改动，承载页的外观差异仅由各自的页面作用域选择器产生

## REMOVED Requirements

### Requirement: Locator file-view keys adopt the hard-edge skin

**Reason**: 元素定位模块整体退役，其文件详情页（`.locator-workbench.file-view`）已不存在，本要求无承载对象。
**Migration**: 无迁移：该页连同其按键皮肤覆写一起删除；硬边几何只保留设备管理页这一处登记。

### Requirement: Device-inspector keys adopt the hard-edge skin

**Reason**: 设备检查器模块整体退役，检查器页与其工具条、设备选择控件、分组筹码均已删除，本要求无承载对象。
**Migration**: 无迁移：该页连同其按键皮肤与可用性配色覆写一起删除。
