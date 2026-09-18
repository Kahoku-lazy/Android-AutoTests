## MODIFIED Requirements

### Requirement: Device-inspector keys adopt the hard-edge skin

设备检查器页「需要硬边外观」的按键 MUST 采用已登记的硬边几何；工具条原生 `button` 与弹窗 `el-button` MUST 由该页页面作用域统一覆写。按键底色 SHALL 按可用性分配：可用按键为天蓝 `var(--c-workflow)`，不可用按键为灰 `var(--color-ink-79)`；两种底色上的文字色 SHALL 为 `var(--ink)`，且文字与底色对比度 MUST 不低于 4.5:1。不可用按键 MUST NOT 以原生 `disabled` 静默拦截点击，MUST NOT 以整体 `opacity` 表达不可用：不可用态由灰底 + 点击提示「按键不可用，请先选择设备」承担。`text` 型图标按键 MUST NOT 被套上边框、背景与硬阴影。

#### Scenario: Toolbar and dialog keys share one geometry

- **WHEN** 在浏览器测量 `/inspector` 工具条任一按键与「保存到元素定位」弹窗底部任一按键的计算样式
- **THEN** 两者 `border-radius` 四角均为 `2px`、`box-shadow` 均为 `2px 2px 0 0` 加墨色且模糊半径为 `0`
- **AND** hover 时计算 `transform` 呈左上位移 1px，`box-shadow` 偏移增至 `3px 3px`

#### Scenario: Available key is sky blue with readable text

- **WHEN** 已选定可用设备且已载入快照，测量「获取」「历史快照」「已保存页面」「保存到元素定位」的底色与文字色
- **THEN** 底色为 `var(--c-workflow)`、文字色为 `var(--ink)`，且四者对比度均不低于 `4.5:1`

#### Scenario: Disabled key drops its offset shadow

- **WHEN** 未选择设备或尚无快照，工具条上相应按键处于不可用态
- **THEN** 该按键底色为灰 `var(--color-ink-79)` 且 `box-shadow` 为 `none`（撤掉位移阴影），与可用态的蓝底 + 硬阴影不混淆
- **AND** 其 `opacity` 为 `1`：不可用态由灰底承担，不再用整体降透明度表达；点击该按键提示「按键不可用，请先选择设备」

#### Scenario: Dark-background key keeps readable text

<!-- 场景名沿自变更前：本页原墨黑底「获取」已改为天蓝底，本 Scenario 改为守住「文字与底色对比度」这一不变量 -->

- **WHEN** 测量 `/inspector` 页任一按键的文字色与底色并计算对比度
- **THEN** 该页按键底色只有浅色系（天蓝 `--c-workflow` / 灰 `--color-ink-79` / 纸色），文字色为 `var(--ink)`，全部对比度不低于 `4.5:1`
- **AND** 若该页此后引入深色底按键，其文字色 MUST 改用主题浅色令牌而非 `--ink`，且对比度仍不低于 `4.5:1`

#### Scenario: Text-type icon key is excluded from the skin

- **WHEN** 测量快照抽屉内 `text` 型 `type="danger"` 删除键
- **THEN** 其计算样式无可见边框、无背景色、无硬阴影，保持无底无边的图标形态
