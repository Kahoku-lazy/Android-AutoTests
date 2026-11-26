## ADDED Requirements

### Requirement: 失败任务可打开本次运行的报告

任务行状态为 `failed` 且结果里带 `report_run` 与 `report_name` 时，任务清单 MUST 在该行提供「报告」入口，点击 MUST 直接打开本次运行的 HTML 报告，MUST NOT 要求先进入任务详情页。

结果里缺少任一定位时，该行 MUST NOT 显示「报告」入口，MUST NOT 报错，也 MUST NOT 留下点击无反应的空白操作。

#### Scenario: 异常中断的失败任务可打开报告

- **WHEN** 一条任务因运行中异常中断进入 `failed`，结果里带 `report_run` 与 `report_name`
- **THEN** 该行显示「报告」入口，点击打开本次运行的 HTML 报告

#### Scenario: 没有报告的失败任务不显示入口

- **WHEN** 一条任务在起跑前就失败，结果里没有报告定位
- **THEN** 该行不显示「报告」入口
- **AND** 页面其余行与操作保持可用
