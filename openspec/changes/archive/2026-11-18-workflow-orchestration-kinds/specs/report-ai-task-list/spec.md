## ADDED Requirements

### Requirement: 报告行展示任务种类

`source` 为 `sop` 的报告行 MUST 额外展示该任务冻结的种类。UI 自动化行 MUST 继续展示设备与用例名称。用例编写行没有设备时，设备字段 MUST 为空。需求拆解行 MUST 展示模块数量，设备与用例名称 MUST 为空，并且 MUST NOT 因此从列表中隐藏。筛选来源时，这三种任务报告仍同属 SOP 来源，MUST NOT 另开报告来源。

#### Scenario: 拆解报告不要求设备

- **WHEN** 一份需求拆解报告进入报告清单
- **THEN** 该行显示种类「需求拆解」和模块数量
- **AND** 设备与用例名称显示为「—」

#### Scenario: 三种任务报告共用 SOP 筛选

- **WHEN** 用户把报告来源筛选为「SOP」
- **THEN** UI 自动化、用例编写和需求拆解的报告都出现
- **AND** 智能体报告不出现
