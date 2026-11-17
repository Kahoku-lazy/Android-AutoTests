## ADDED Requirements

### Requirement: 控制条的筛选与搜索是输入件皮肤

设备管理页控制条里的状态筛选下拉与名称搜索框 MUST 呈现为输入件，不得套用按键皮肤：MUST NOT 带硬偏移影，字重 MUST 为常规（不是按键的粗字），圆角 MUST 取输入框刻度 `--app-radius-sm`（`4px 8px`）。两件的底色 MUST 为 135° 斜向渐变填充，颜色浓度从 45% 过渡到 20%，色相 MUST 取模块色 `--c-device`（薄荷绿）并通过 `--comp-device-field-fill` 派生，MUST NOT 新增颜色原子或写字面量色值。边框 MUST 保留 `2px` 墨色以与主题输入框一致。hover 时边框 MUST 转为 `--c-dashboard`；focus 时 MUST 额外出现 `3px` 柠黄低浓度扩散环。同一控制条里的「局域网」「刷新」「上一页」「下一页」MUST 继续走按键皮肤（墨边 + 硬偏移影 + 粗字）。

#### Scenario: 两个输入件不再是按键外观

- **WHEN** 打开 `/devices` 并观察控制条
- **THEN** 「全部设备 · N」下拉与搜索框都没有硬偏移影、字重为常规、圆角为 `4px 8px`
- **AND** 两件底色为从左上到右下的薄荷绿渐变，浓度由 45% 递减到 20%

#### Scenario: 输入件与按键一眼可分

- **WHEN** 同一控制条内并排观察「刷新」键与搜索框
- **THEN** 「刷新」键仍是墨边 + `2px` 硬影 + 粗字
- **AND** 搜索框无影、常规字重、带渐变填充

#### Scenario: hover 与 focus 沿用主题输入框语言

- **WHEN** 鼠标移到搜索框上
- **THEN** 边框转为柠黄 `--c-dashboard`，控件不位移、不加影
- **WHEN** 焦点进入搜索框
- **THEN** 除边框转柠黄外，外侧出现 `3px` 柠黄低浓度扩散环
