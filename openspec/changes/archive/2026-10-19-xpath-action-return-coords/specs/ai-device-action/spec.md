## REMOVED Requirements

### Requirement: xpath 读取文本时列出全部命中

**Reason**: `xpath_action` 不再按 `action` 读文本、检查存在或点击。调用方改为先取文本和坐标，再按坐标点击。
**Migration**: 用 `serial` 与 `xpath` 调用查询。一条命中读顶层 `text`、`x`、`y`；多条命中读 `items` 里的下标。点击和长按改用返回的像素坐标走既有坐标点击工具。

## ADDED Requirements

### Requirement: xpath 查询只返回文本与坐标

`xpath_action` SHALL 只接受设备序列号和 xpath，并 SHALL 以 JSON 文本返回该 xpath 在当前页面上的命中。返回 MUST 含每条命中的元素文本、边框中心的屏幕像素坐标，以及边框字符串。本工具 MUST NOT 点击、长按或改变设备状态，MUST NOT 把结果写成文件。命中顺序 MUST 与页面查找顺序一致。边框无法解析时，该条的 `x` 与 `y` MUST 为 0，`bounds` MUST 仍返回原始字符串。

#### Scenario: 只命中一条时不写下标

- **WHEN** 该 xpath 只命中一个元素，其文本为 `H6110`，边框中心为像素 `(120, 340)`
- **THEN** 返回 `count` 为 1，并含 `text`、`x`、`y`、`bounds`；`x` 为 120，`y` 为 340；返回中没有 `index`，也没有 `items`

#### Scenario: 命中多条时按下标标记

- **WHEN** 同一 xpath 按页面顺序命中三个元素
- **THEN** 返回 `count` 为 3，`items` 含下标 0、1、2；每条都有 `text`、`x`、`y`、`bounds`

#### Scenario: 没有命中

- **WHEN** 该 xpath 没有命中任何元素
- **THEN** 返回 `count` 为 0，`items` 为空列表，且没有顶层 `text`、`x`、`y`

#### Scenario: 查询不产生点击

- **WHEN** 调用 `xpath_action` 并成功返回命中
- **THEN** 设备没有被点击或长按，返回中没有 `action_time`

#### Scenario: 连接失败

- **WHEN** 目标设备无法连接
- **THEN** 返回含 `error` 的 JSON 文本，且不执行点击
