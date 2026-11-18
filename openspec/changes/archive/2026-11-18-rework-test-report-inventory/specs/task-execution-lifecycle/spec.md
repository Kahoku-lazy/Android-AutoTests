# Delta: task-execution-lifecycle

## ADDED Requirements

### Requirement: 中断状态在任务清单可见

任务清单 MUST 把 `interrupted` 显示为“已中断”，并使用与失败不同的标签样式。测试报告列表 MUST NOT 展示中断任务：中断不产生报告，报告台账只收录已生成的报告。

#### Scenario: 任务清单显示已中断记录

- **WHEN** 用户打开任务清单且存在 `interrupted` 任务
- **THEN** 该任务状态显示“已中断”，标签样式与失败可区分

#### Scenario: 报告台账不显示中断任务

- **WHEN** 用户打开 `/reports` 且存在 `interrupted` 任务
- **THEN** 报告列表不含该任务的行，也不存在“已中断”筛选分组

## REMOVED Requirements

### Requirement: 中断不计入通过与失败

**Reason**: 测试报告不再统计任务通过/失败与每日趋势，改为统计报告数量；中断任务不产生报告、天然不进入台账，原通过率分母口径失去载体。
**Migration**: 任务成功率口径见 `task-list-module` 的任务清单统计需求；报告数量口径见 `report-ai-task-list` 的「Report summary counts reports」。

### Requirement: 中断状态在界面上可见

**Reason**: 原需求覆盖「任务清单、任务详情与测试报告列表」三处：任务详情已随 retire-engines-agents 下线，测试报告改为报告台账后不再展示中断任务；任务清单的中断展示由新需求「中断状态在任务清单可见」承接。
**Migration**: 见新需求「中断状态在任务清单可见」；报告台账口径见 `report-ai-task-list` 的「Only completed runs produce report rows」。
