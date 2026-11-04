## ADDED Requirements

### Requirement: 步骤行给出模型、工具与空档耗时

报告的每条用例里，`cases[].steps[]` SHALL 同时给出该步的三个耗时字段：`duration_ms`（步骤墙钟，语义不变）、`model_ms`（该步全部模型调用耗时之和）、`tool_ms`（该步全部工具返回耗时之和）与 `idle_ms`（`duration_ms - model_ms - tool_ms`）。`idle_ms` MUST NOT 为负数，差额为负时 MUST 取 0。存量任务没有工具类事件时 `tool_ms` 与 `idle_ms` MUST 为 0，MUST NOT 因此报错或省略 `duration_ms`。

页面 MUST 在步骤行展示「模型」「工具」「空档」三项耗时，取值口径与接口字段一致；某项为 0 时 MUST NOT 渲染该项的 `0s` 徽标。三项之和 MUST 等于步骤墙钟（允许 1 秒内的取整误差）。

#### Scenario: 三个耗时字段同时下发

- **WHEN** 某步墙钟 126 秒，其中模型调用合计 51 秒、工具返回合计 42.5 秒
- **THEN** 该步的 `duration_ms`、`model_ms`、`tool_ms` 分别取这三个值，`idle_ms` 为 32.5 秒

#### Scenario: 差额不为负

- **WHEN** 某步事件时间戳存在重叠，导致模型与工具耗时之和大于步骤墙钟
- **THEN** `idle_ms` 为 0，MUST NOT 返回负数

#### Scenario: 存量任务没有工具事件

- **WHEN** 某步只有模型调用事件、没有任何工具返回事件
- **THEN** `tool_ms` 与 `idle_ms` 为 0，`duration_ms` 与 `model_ms` 照常下发

#### Scenario: 页面同时展示三项

- **WHEN** 打开某步耗时非零的任务详情
- **THEN** 该步行同时出现「模型」「工具」「空档」三项耗时，且都不为零

#### Scenario: 零值不显示

- **WHEN** 某步没有工具事件
- **THEN** 该步行只出现「模型」耗时，没有「工具」「空档」的 0s 徽标
