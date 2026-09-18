# dashboard-agent-tasks Specification

## Purpose

定义仪表盘趋势第一行（柱状图与任务执行结果）必须反映平台小助手任务卡片，以及助手页任务卡仅展示标题与详情入口。

## Requirements

### Requirement: Dashboard execution chart uses agent task cards

系统 MUST 用当前用户可见智能体下的 `AITask` 填充仪表盘 `charts.execution`。近 12 个自然日 MUST 以 `created_at` 分桶；成功桶 MUST 计入 `status` 为 `completed` 或 `success` 的卡片，失败桶 MUST 计入 `status` 为 `failed` 的卡片。MUST NOT 再返回执行引擎下线后的恒零序列作为该图的业务含义。

#### Scenario: Two successful cards appear on create day

- **WHEN** 用户在某日新建两张状态为成功的助手任务卡并打开仪表盘
- **THEN** 该日成功柱为 2、失败柱为 0
- **AND** 其它日期无对应卡片时为 0

### Requirement: Dashboard result panel lists agent task cards

系统 MUST 用同一批 `AITask` 填充 `execution_summary`（成功数 / 失败数）与 `recent_tasks`（最近卡片，含 id、标题、状态、时间）。空列表时文案 MUST 引导前往平台小助手新建任务，MUST NOT 再引导「执行引擎」。有 id 的条目被激活时 MUST 进入该任务详情（`/ai-assistant/tasks/:id`），MUST NOT 进入报告列表。

#### Scenario: Empty panel copy

- **WHEN** 当前用户没有可见助手任务卡
- **THEN** 面板显示空态且文案指向平台小助手
- **AND** 成功/失败计数均为 0

#### Scenario: Click recent card opens assistant task detail

- **WHEN** 面板列出带 id 的助手任务卡且用户激活该行
- **THEN** 路由进入对应助手任务详情页

### Requirement: Assistant task card shows title and details only

平台小助手任务列表中的单张任务卡 MUST 展示标题（无标题则用目标）与「详情」操作。该卡片 MUST NOT 再展示目标全文、设备 serial、创建时间、结果摘要或删除按钮。区块头的筛选、状态分组、新建与调试清空 MAY 保留。

#### Scenario: Compact task card

- **WHEN** 用户打开平台小助手任务卡片区
- **THEN** 每张卡可见标题与「详情」
- **AND** 卡面上无删除、无目标段落、无设备/时间行
