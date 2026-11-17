## REMOVED Requirements

### Requirement: Device-management button groups assign tones by role

**Reason**: 该要求把设备页的按键角色绑在「显示行数」「全部设备·在线·使用中」「表格·卡片」三组分段/切换类控件上。`device-pool-list-controls` 变更删除了卡片视图与行数选择器，并把状态筛选改成下拉控件，这三组控件已不存在，原要求的主干（切换类二态底色）在设备页失去承载对象。

**Migration**: 由「Device-management control bar assigns tones by role」替代：命名动作键（局域网 / 刷新）的底色保持不变；新增的筛选下拉与搜索框采用本页硬边几何但不套用二态底色；分页按键常驻并沿用既有语义底色，置灰态可辨。其它页面的分段控件（如 `AppTabs`）仍按原二态口径执行，不受本变更影响。

## ADDED Requirements

### Requirement: Device-management control bar assigns tones by role

设备管理页（`/devices`）控制区按键 SHALL 按角色分配外观：命名动作键「局域网」底色为 `var(--c-element)`、「刷新」底色为 `var(--c-device)`；筛选下拉与搜索输入 MUST 采用本页已登记的硬边几何（`2px` 墨色实边、四角 `2px`、零模糊偏移阴影 `2px 2px 0 0 var(--ink)`），SHALL NOT 套用分段控件的未选中天蓝 / 选中柠黄二态底色（它们不是切换类控件）。「上一页 / 下一页」MUST 常驻并沿用各自既有语义底色，置灰态 MUST 与可用态可区分（降低透明度并撤除位移阴影）。其余按键（表格操作列、弹窗、空错态重试）SHALL 沿用各自既有语义底色，MUST NOT 被压成同一种底色。设备页 MUST NOT 再出现「显示行数」组或「表格 / 卡片」切换组。

#### Scenario: Named action buttons keep their assigned hues

- **WHEN** 查看设备管理页工具条
- **THEN** 「局域网」底色为薰衣草紫 `var(--c-element)`，「刷新」底色为薄荷绿 `var(--c-device)`

#### Scenario: Filter dropdown and search adopt the hard-edge geometry

- **WHEN** 测量筛选下拉与搜索框的计算样式
- **THEN** 两者 `border-width` 为 `2px`、`border-style` 为 `solid`、四角 `border-radius` 为 `2px`、`box-shadow` 为 `2px 2px 0 0` 加墨色且模糊半径为 `0`
- **AND** 两者的底色不是分段控件的天蓝或柠黄

#### Scenario: Pagination keys stay visible and disabled state is distinct

- **WHEN** 设备只有 1 页
- **THEN** 「上一页」「下一页」仍然渲染，且均不可点击
- **AND** 置灰态的透明度低于可用态，且不绘制位移阴影

#### Scenario: Other keys keep semantic backgrounds

- **WHEN** 查看表格操作列、弹窗与空错态重试按键
- **THEN** 每个按键保留原有语义底色（危险 / 警告 / 主色 / 纸色），不被统一成同一颜色
