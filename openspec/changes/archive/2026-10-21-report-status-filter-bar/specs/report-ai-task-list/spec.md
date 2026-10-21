## ADDED Requirements

### Requirement: Report workbench filters rows by status

测试报告工作台 SHALL 在「测试报告」分区头提供状态筛选条，包含「全部 / 已完成 / 失败 / 已停止」四项，并在每项上显示当前查询条件下的条数。筛选条 MUST 使用共享 `FilterTabs`，MUST NOT 用内容页签（`AppTabs`）承载状态筛选。

「全部」的计数 SHALL 等于当前查询返回的任务卡总数；「已完成」SHALL 统计 `completed` 与 `success`；「失败」SHALL 只统计 `failed`；「已停止」SHALL 只统计 `stopped`。其它状态（`running` / `pending` / `interrupted` / `error` 等）MUST 只计入「全部」，MUST NOT 新增第五个筛选项。

切换筛选项 SHALL 只改变同一张报告表呈现的行，MUST NOT 为每个状态各渲染一张表格，MUST NOT 产生页签内层纵向滚动。

#### Scenario: Counts follow the current query

- **WHEN** 当前查询返回 12 张任务卡，其中 1 张为 `completed`、11 张为 `failed`
- **THEN** 筛选条依次显示「全部 12」「已完成 1」「失败 11」「已停止 0」

#### Scenario: Switching filters reuses one table

- **WHEN** 用户从「全部」切到「失败」
- **THEN** 页面上只有一张报告表，表内只剩 `failed` 行
- **AND** 纵向滚动仍由页面主体承担，表格容器内没有独立纵向滚动条

#### Scenario: Non-terminal statuses stay in All only

- **WHEN** 当前结果里存在 `running` 或 `pending` 的任务卡
- **THEN** 它们只出现在「全部」的计数与行里，不计入「已完成 / 失败 / 已停止」

#### Scenario: Empty result keeps a stable filter row

- **WHEN** 当前查询没有任何任务卡
- **THEN** 四个筛选项仍然渲染，计数均为 0，报告表显示空态
