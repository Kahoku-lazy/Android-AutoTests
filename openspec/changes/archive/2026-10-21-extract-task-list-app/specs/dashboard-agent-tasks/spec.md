## MODIFIED Requirements

### Requirement: Dashboard result panel lists agent task cards

系统 MUST 用同一批 `Task` 填充 `execution_summary`（成功数 / 失败数）与 `recent_tasks`（最近卡片，含 id、标题、状态、时间）。空列表时文案 MUST 引导前往任务清单新建任务，MUST NOT 再引导「执行引擎」。有 id 的条目被激活时 MUST 进入该任务详情（`/tasks/:id`），MUST NOT 进入报告列表。

#### Scenario: Empty panel copy

- **WHEN** 当前用户没有可见助手任务卡
- **THEN** 面板显示空态且文案指向任务清单
- **AND** 成功/失败计数均为 0

#### Scenario: Click recent card opens assistant task detail

- **WHEN** 面板列出带 id 的助手任务卡且用户激活该行
- **THEN** 路由进入对应任务清单详情页 `/tasks/:id`
