## MODIFIED Requirements

### Requirement: Only completed runs produce report rows

报告行 MUST 来自两条且仅两条来源：

1. **SOP 报告**（`source` 为 `sop`）：终态任务（`completed`/`success`/`failed`）且结果里带报告定位（`report_run` 与 `report_name` 均非空），对应 `logs/agents/backend_bridge/` 下的一份 HTML。
2. **智能体报告**（`source` 为 `agent`）：正常完成的助手对话轮次（助手消息带非空 `report_id`），对应 `logs/agents/assistants/` 下的一份 HTML。

`failed` 既包含验收不通过，也包含运行中异常中断；两者只要结果里带报告定位，MUST 同等入列。

未执行（`pending`）、执行中（`running`）、取消（`cancelled`）与中断（`interrupted`）的任务/轮次 MUST NOT 出现在 `items`。

#### Scenario: 完成的 SOP 任务进入列表

- **WHEN** 一条任务正常跑完（完成或失败），结果里带报告定位
- **THEN** `items` 含一行 `source` 为 `sop` 的报告，携带该定位

#### Scenario: 异常中断的失败任务与验收不通过同等入列

- **WHEN** 一条任务在运行中因模型调用异常中断进入 `failed`，结果里带报告定位
- **THEN** `items` 含一行 `source` 为 `sop` 的报告，与验收不通过产生的报告没有差别对待

#### Scenario: 完成的助手轮次进入列表

- **WHEN** 平台助手某对话栏的一轮正常完成，消息上登记了 `report_id`
- **THEN** `items` 含一行 `source` 为 `agent` 的报告

#### Scenario: 未执行与执行中不进入列表

- **WHEN** 存在 `pending` 或 `running` 的任务，或某对话栏仍有一轮在运行
- **THEN** `items` 不含这些任务/轮次的任何行，`summary` 也不计入它们

#### Scenario: 取消与中断不进入列表

- **WHEN** 一条任务被用户关闭（`cancelled`）或因重启/预算中断（`interrupted`）
- **THEN** `items` 不含该任务的行
