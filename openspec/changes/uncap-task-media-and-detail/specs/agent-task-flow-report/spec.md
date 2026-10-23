## ADDED Requirements

### Requirement: 事件明细完整展示

事件项的 `detail` MUST 完整包含该事件的展示文本：文本块全文、工具入参全文、工具结果全文。系统 MUST NOT 按固定字数截断明细，也 MUST NOT 为截断追加省略号。明细只 MUST 去掉回车符并去掉首尾空白。`data.task.result` 不受本要求约束，仍为 240 字摘要。

#### Scenario: 超长工具入参完整下发

- **WHEN** 一条工具调用结束事件的入参有 2,831 字
- **THEN** 该项 `detail` 包含全部入参、长度不小于 2,831，且不以省略号结尾

#### Scenario: 超长文本块完整下发

- **WHEN** 一条文本块完成事件的文本有 3,500 字
- **THEN** 该项 `detail` 等于该文本去掉首尾空白后的内容

#### Scenario: 任务结果仍为摘要

- **WHEN** 任务的 `result` 有 1,000 字
- **THEN** `data.task.result` 仍为 240 字摘要，与事件明细的完整展示互不影响
