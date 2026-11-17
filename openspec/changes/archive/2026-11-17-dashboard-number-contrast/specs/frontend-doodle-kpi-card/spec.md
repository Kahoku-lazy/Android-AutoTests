## REMOVED Requirements

### Requirement: KPI 主数值取 accent 的 80%→30% 渐变

（被「KPI 主数值取深彩渐变」替换：旧口径两端混纸色，实测对比度只有 1.1~3.0:1，远低于大字号 3:1 门槛。）

## ADDED Requirements

### Requirement: KPI 主数值取深彩渐变

共享统计卡（`kpi` 与 `entry` 两个变体）的主数值 MUST 使用传入 accent 与墨色 `--ink` 混合的同色相渐变：起点 MUST 为 accent 与墨色按 **48%** 混合，终点 MUST 为 accent 与墨色按 **30%** 混合。该渐变 MUST NOT 混入纸色，MUST NOT 出现低于 30% 或高于 48% 的 accent 浓度。

主数值与卡底（`--color-white`）的计算对比度 MUST 不低于 **4.5:1**（大字号门槛 3:1 之上再留余量）。不支持 `background-clip: text` 时，数值 MUST 回落到终点色（`accent 30% + ink`），MUST NOT 回落到透明度或纯墨色。

标题、描述、时间与字段名 MUST NOT 改用 accent 上色；卡片描边与三层硬影 MUST 继续取同一 accent。

#### Scenario: 入口卡数值取深彩渐变

- **WHEN** 仪表盘以 `entry` 变体渲染统计入口卡
- **THEN** 主数值的渐变两端分别为 accent 与墨色 48% / 30% 的混合色
- **AND** 终点色对卡白的对比度不低于 4.5:1
- **AND** 卡片硬偏移阴影仍取同一 accent

#### Scenario: 紧凑卡数值取同一区间

- **WHEN** 页面以默认 `kpi` 变体渲染共享统计卡
- **THEN** 主数值使用与 `entry` 变体相同的 48%→30% 区间
- **AND** 标题与描述保持墨色 / 次要色，不随 accent 改变

#### Scenario: 六支模块色都达标

- **WHEN** 分别用 device / ai / runner / element / case / report 六支彩笔渲染统计卡
- **THEN** 每个数值的终点色对卡白的对比度都在 7:1 以上
- **AND** 同一排卡片仍能靠色相区分，不糊成同一种深灰
