## ADDED Requirements

### Requirement: xpath 读取文本时列出全部命中

当 `xpath_action` 的动作为读取文本时，系统 SHALL 返回该 xpath 命中的全部元素。每条命中 MUST 带有与点击、长按相同的下标、元素文本，以及屏幕像素范围。返回中的 `text` SHALL 为入参 `index` 所指向那一条的文本；`index` 超出命中范围或没有任何命中时，`text` MUST 为空字符串。`count` MUST 等于命中条数。存在检查、点击与长按的行为 MUST NOT 因本要求而改变。

#### Scenario: 多个相同文本都带下标和范围

- **WHEN** 页面上有两个文本都是 `ON` 的元素命中同一 xpath，并以 `index` 为 0 读取文本
- **THEN** 返回的 `count` 为 2，`text` 为 `ON`，`items` 含下标 0 与 1，且每条都有该元素的像素范围

#### Scenario: 指定下标决定 text

- **WHEN** 同一 xpath 命中至少两条，并以 `index` 为 1 读取文本
- **THEN** `text` 为下标 1 那一条的文本，`items` 仍列出全部命中及其下标

#### Scenario: 没有命中

- **WHEN** 该 xpath 没有命中任何元素
- **THEN** 返回 `count` 为 0，`text` 为空字符串，`items` 为空列表
