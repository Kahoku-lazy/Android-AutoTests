## ADDED Requirements

### Requirement: 任务执行状态徽标七态分色且底色渐变

任务清单「执行状态」徽标 MUST 为每个状态提供可区分的色相，覆盖 `pending` / `running` / `paused` / `success` / `failed` / `interrupted` / `cancelled` 七态；SHALL NOT 让任一状态回落到无彩灰底。徽标底色 MUST 是该状态色的**纵向渐变**（上约 20% → 下约 5% 混白），描边 MUST 取该状态色；文字 MUST 用墨色（状态色只承载描边与底色），以保证在浅渐变底上的可读对比度。色相 MUST 全部取自 `tokens.css` 已登记令牌，SHALL NOT 写字面色值。

#### Scenario: 七态各有独立色相

- **WHEN** 任务清单同时渲染待执行、执行中、任务暂停、任务成功、任务失败、已中断、任务取消七种状态
- **THEN** 七枚徽标的底色与描边两两不同
- **AND** 不存在与「默认灰底」完全相同的徽标

#### Scenario: 底色是渐变而非平涂

- **WHEN** 检查任一状态徽标的背景
- **THEN** `background-image` 含 `linear-gradient`
- **AND** 渐变两端分别约为该状态色的 20% 与 5% 与卡片底的混合

#### Scenario: 文字仍可读

- **WHEN** 测量任一状态徽标的文字色与底色
- **THEN** 文字为墨色，不直接使用浅色状态令牌作前景
- **AND** 文字与底色的对比度不低于 4.5:1
