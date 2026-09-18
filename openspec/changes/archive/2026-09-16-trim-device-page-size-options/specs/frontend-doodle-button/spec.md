## MODIFIED Requirements

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
