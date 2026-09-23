## ADDED Requirements

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
