# dashboard-agent-tasks Specification

## Purpose

定义仪表盘趋势第一行（柱状图与任务执行结果）必须反映平台小助手任务卡片；任务卡片列表已迁至独立任务清单页，字段与入口由 `ai-task-list` 约定。

## Requirements

### Requirement: Dashboard execution chart uses agent task cards

系统 MUST 用工作流任务（`assistant_sop`）填充仪表盘 `charts.execution`。近 7 个自然日 MUST 以 `created_at` 分桶；成功桶 MUST 计入 `status` 为 `completed` 或 `success` 的任务，失败桶 MUST 计入 `status` 为 `failed` 的任务。中断与取消 MUST NOT 计入成功或失败柱。系统 MUST NOT 把已退役的设备执行或用例编写任务计入该图，MUST NOT 再返回执行引擎下线后的恒零序列作为该图的业务含义。

#### Scenario: Two successful cards appear on create day

- **WHEN** 用户在某日新建两张状态为成功的工作流任务并打开仪表盘
- **THEN** 该日成功柱为 2、失败柱为 0
- **AND** 其它日期无对应任务时为 0

#### Scenario: Retired task kinds stay out of the chart

- **WHEN** 同一日另有一条状态为成功的设备执行或用例编写任务
- **THEN** 该日成功柱不因这条任务增加

### Requirement: Dashboard result panel lists agent task cards

系统 MUST 用同一批工作流任务填充 `execution_summary`（成功数 / 失败数）与 `recent_tasks`（最近任务，含 id、标题、状态、时间）。成功 MUST 含 `completed` 与 `success`，失败 MUST 只含 `failed`。中断与取消 MUST 在最近任务行中显示为中断或取消，MUST NOT 显示为「未执行」。空列表时文案 MUST 引导前往任务清单，MUST NOT 再引导「执行引擎」。有 id 的条目被激活时 MUST 进入任务清单（`/tasks`），MUST NOT 进入已下线的 `/tasks/:id`，MUST NOT 进入报告列表。

#### Scenario: Empty panel copy

- **WHEN** 当前没有工作流任务
- **THEN** 面板显示空态且文案指向任务清单
- **AND** 成功/失败计数均为 0

#### Scenario: Click recent card opens assistant task detail

- **WHEN** 面板列出带 id 的工作流任务且用户激活该行
- **THEN** 路由进入任务清单 `/tasks`
- **AND** 不进入 `/tasks/:id`

#### Scenario: Interrupted card is not shown as idle

- **WHEN** 最近任务中有一条状态为 `interrupted` 或 `cancelled`
- **THEN** 该行分别显示为中断或取消
- **AND** 不显示为「未执行」

### Requirement: 最近任务卡展示用例身份副行

仪表盘最近任务卡 MUST 在任务标题下展示与任务清单同一句用例文案。一条为标题，多条为「第一条标题 · 共 N 条」，里程碑为「里程碑」，没有身份时 MUST NOT 渲染该副行。该副行 MUST NOT 替换任务标题，也 MUST NOT 改变成功数、失败数或图表分桶。激活该行的去向 MUST 保持现状。

#### Scenario: 多选用例在副行给出计数

- **WHEN** 最近任务卡对应一条冻结了三条用例的任务
- **THEN** 标题仍是工作流名
- **AND** 副行显示「第一条标题 · 共 3 条」

#### Scenario: 旧任务不显示空副行

- **WHEN** 最近任务卡对应一条没有用例身份的历史任务
- **THEN** 只显示任务标题
- **AND** 不显示「—」或空副行
