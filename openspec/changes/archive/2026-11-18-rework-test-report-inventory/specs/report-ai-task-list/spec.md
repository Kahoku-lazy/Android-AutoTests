# Delta: report-ai-task-list

## ADDED Requirements

### Requirement: Report list is sourced from generated reports

`GET /api/reports` MUST 返回标准信封 `{status, data}`，`data` 含 `summary`、`total`、`items`。`items` 的每一行 MUST 对应一份**已生成的 HTML 报告**，按报告生成时间倒序。列表 MUST 只读，MUST NOT 写任何业务表，MUST NOT 扫描磁盘目录来发现报告。可见性 MUST 与任务清单模块一致。扫描与返回上限 MUST 遵守 `platform-load-budget` 的既有约束。

#### Scenario: 列表一行对应一份报告

- **WHEN** 登录用户请求 `GET /api/reports/`
- **THEN** `items` 的每行携带来源标记与查看定位，一行对应一份已生成的报告

#### Scenario: 空结果

- **WHEN** 当前用户没有任何已生成报告
- **THEN** `items` 为空列表，`total` 为 0

### Requirement: Only completed runs produce report rows

报告行 MUST 来自两条且仅两条来源：

1. **SOP 报告**（`source` 为 `sop`）：终态任务（`completed`/`success`/`failed`）且结果里带报告定位（`report_run` 与 `report_name` 均非空），对应 `logs/agents/backend_bridge/` 下的一份 HTML。
2. **智能体报告**（`source` 为 `agent`）：正常完成的助手对话轮次（助手消息带非空 `report_id`），对应 `logs/agents/assistants/` 下的一份 HTML。

未执行（`pending`）、执行中（`running`）、取消（`cancelled`）与中断（`interrupted`）的任务/轮次 MUST NOT 出现在 `items`。

#### Scenario: 完成的 SOP 任务进入列表

- **WHEN** 一条任务正常跑完（完成或失败），结果里带报告定位
- **THEN** `items` 含一行 `source` 为 `sop` 的报告，携带该定位

#### Scenario: 完成的助手轮次进入列表

- **WHEN** 平台助手某对话栏的一轮正常完成，消息上登记了 `report_id`
- **THEN** `items` 含一行 `source` 为 `agent` 的报告

#### Scenario: 未执行与执行中不进入列表

- **WHEN** 存在 `pending` 或 `running` 的任务，或某对话栏仍有一轮在运行
- **THEN** `items` 不含这些任务/轮次的任何行，`summary` 也不计入它们

#### Scenario: 取消与中断不进入列表

- **WHEN** 一条任务被用户关闭（`cancelled`）或因重启/预算中断（`interrupted`）
- **THEN** `items` 不含该任务的行

### Requirement: Report summary counts reports

`summary` MUST 统计**报告数量**：`total_reports`（报告总数）、`sop_reports`（SOP 报告数）、`agent_reports`（智能体报告数），且 `total_reports` MUST 等于 `sop_reports` 与 `agent_reports` 之和。系统 MUST NOT 再返回任务通过率、通过/失败计数或每日趋势负载。

#### Scenario: 混合来源计数

- **WHEN** 当前查询命中 3 份 SOP 报告与 2 份智能体报告
- **THEN** `summary` 为 `total_reports` 5、`sop_reports` 3、`agent_reports` 2

#### Scenario: 空结果计数为零

- **WHEN** 当前用户没有任何已生成报告
- **THEN** `summary` 三项均为 0

### Requirement: SOP report rows carry case identity and task id

`source` 为 `sop` 的行 MUST 携带：`report_run`、`report_name`（查看定位）、`task_id`（关联任务 ID）、`task_title`、`case_label`（用例名称）、设备展示名、任务终态、起止时间与耗时文案。`case_label` MUST 只由任务冻结的用例身份算出，口径与任务清单、BUG 单一致：一条用例显示标题；多条显示「第一条标题 · 共 N 条」；里程碑来源显示「里程碑」；没有用例身份显示空串。系统 MUST NOT 回读用例库，也 MUST NOT 从步骤名或附件正文反推用例名。

#### Scenario: 单用例报告行

- **WHEN** 报告对应任务的冻结身份只含一条用例
- **THEN** 该行 `case_label` 为该用例标题，`task_id` 为任务编号

#### Scenario: 多用例与里程碑

- **WHEN** 冻结身份含多条用例，或来源为里程碑
- **THEN** `case_label` 分别为「第一条标题 · 共 N 条」或「里程碑」

#### Scenario: 无用例身份

- **WHEN** 任务没有冻结用例身份（旧任务或里程碑外无行）
- **THEN** `case_label` 为空串，页面显示「—」，不编造用例名

### Requirement: Agent report rows carry assistant identity

`source` 为 `agent` 的行 MUST 携带：`assistant_id`（助手编号）、`assistant_name`（助手显示名）、`thread_id`、`report_id`（查看定位）、`summary`（该轮一句话结果）与 `created_at`。助手名片已删除时，`assistant_id` MUST 仍显示，`assistant_name` MUST 回落为空串，MUST NOT 因此隐藏该行或报错。

#### Scenario: 智能体报告行带编号与名称

- **WHEN** 某轮报告对应助手名片存在
- **THEN** 该行同时显示助手编号与显示名

#### Scenario: 名片删除后报告仍可查

- **WHEN** 报告对应助手名片已被删除
- **THEN** 该行仍出现在列表，编号照常显示，名称为空

### Requirement: Report workbench filters by source

测试报告工作台 SHALL 提供来源筛选条「全部 / SOP / 智能体」，每项显示当前查询条件下的报告条数，MUST 使用共享 `FilterTabs`。筛选条 SHALL 辅以关键字（匹配用例名称、任务 ID、助手名称或助手编号）与日期区间过滤。切换筛选 MUST 只改变同一张报告表的行，MUST NOT 为每个来源各渲染一张表，MUST NOT 产生页签内层纵向滚动。

#### Scenario: 计数跟随当前查询

- **WHEN** 当前查询命中 5 份报告（3 SOP、2 智能体）
- **THEN** 筛选条依次显示「全部 5」「SOP 3」「智能体 2」

#### Scenario: 切换来源复用同一张表

- **WHEN** 用户从「全部」切到「智能体」
- **THEN** 页面只有一张报告表，表内只剩智能体报告行

#### Scenario: 关键字命中任务 ID

- **WHEN** 用户在关键字框输入某 SOP 报告的任务编号
- **THEN** 列表只剩该任务对应的报告行

### Requirement: Report row opens the generated report

点击报告行（或其「查看报告」操作）MUST 打开该份已生成的 HTML 报告，且 MUST 复用既有读取通道：SOP 报告走 `GET /api/ai/agent-reports/{run}/{name}/`；智能体报告走对话栏日志的一次性 ticket 通道。系统 MUST NOT 为报告台账新增读取端点，MUST NOT 把磁盘绝对路径返回前端，MUST NOT 链到 `/tasks/:id` 或 `/reports/:id`。报告文件已不存在时 MUST 给出可读错误提示，MUST NOT 让页面进入错误态或崩溃。

#### Scenario: 打开 SOP 报告

- **WHEN** 用户点击一行 SOP 报告
- **THEN** 浏览器展示该份 HTML 报告，请求走既有平台报告读取通道

#### Scenario: 打开智能体报告

- **WHEN** 用户点击一行智能体报告
- **THEN** 先换取一次性 ticket，再在浏览器展示该轮 HTML 报告

#### Scenario: 文件缺失可读提示

- **WHEN** 报告行对应的磁盘文件已被删除
- **THEN** 页面提示「报告不存在」，列表与其它行不受影响

### Requirement: Empty copy points to task execution

`items` 为空时，工作台 MUST 提示「报告在执行完成后生成」，并引导用户去任务清单或平台助手发起执行。文案 MUST NOT 引导用户去「执行引擎」跑测试。

#### Scenario: 空表提示

- **WHEN** 报告表没有任何行
- **THEN** 空态说明报告在执行完成后生成，并提到任务清单或平台助手，不提执行引擎

### Requirement: 报告台账接口返回标准信封

`/api/reports/` MUST 返回标准信封 `{status, data}`，业务负载放在 `data` 中且 MUST NOT 自带 `status` 字段，`data` 含 `summary`、`total`、`items`。系统 MUST NOT 提供 `/api/reports/cases/`、`/api/reports/run/{run_id}/`、`/api/reports/{filename}/` 与 `/api/reports/{filename}/content/`；直接访问这些路径 MUST 返回 404。

#### Scenario: 报告列表使用信封

- **WHEN** 登录用户请求 `GET /api/reports/`
- **THEN** 响应为 200 且顶层只有 `status` 与 `data`
- **AND** `data` 含 `summary`、`total`、`items`

#### Scenario: 用例分解与 Run 详情端点不存在

- **WHEN** 请求 `GET /api/reports/cases/` 或 `GET /api/reports/run/{run_id}/`
- **THEN** 响应为 404，MUST NOT 返回信封或任何报告负载

#### Scenario: 旧文件端点已退役

- **WHEN** 请求 `GET /api/reports/{filename}/` 或 `GET /api/reports/{filename}/content/`
- **THEN** 响应为 404，MUST NOT 返回文件内容或附件

### Requirement: 报告工作台单路由约束

测试报告工作台 MUST 只注册列表页 `/reports` 一个路由。系统 MUST NOT 注册 `/reports/:runId`、`/reports/cases/:resultType` 或等价路径；列表行、任务编号与 KPI 卡 MUST NOT 链到这些路径。报告正文 MUST 按「Report row opens the generated report」以既有读取通道打开，MUST NOT 在前端新建报告详情路由。

#### Scenario: 直接访问已删的报告详情路由

- **WHEN** 用户直接打开 `/reports/143`
- **THEN** 前端不渲染报告详情页，落到 404 页

#### Scenario: 用例分解路由不可打开

- **WHEN** 用户直接打开 `/reports/cases/pass`
- **THEN** 前端落到 404 页，MUST NOT 渲染用例分解页

#### Scenario: 列表行打开报告文件而非详情路由

- **WHEN** 用户点击测试报告列表中的一行
- **THEN** 浏览器打开该行对应的 HTML 报告，路由停留在 `/reports`

## REMOVED Requirements

### Requirement: Report list is sourced from assistant tasks

**Reason**: 列表数据源从「可见任务卡（含未执行/执行中）」改为「已生成的报告」，由新需求「Report list is sourced from generated reports」与「Only completed runs produce report rows」承接。
**Migration**: 消费方改读 `data.items`（报告行）与 `data.summary`（报告数量）；任务行展示归任务清单模块。

### Requirement: Task-card success metrics

**Reason**: 统计口径改为报告数量，任务通过率/通过失败计数/每日趋势不再属于测试报告；任务成功率统计归任务清单模块。
**Migration**: 需要任务成功率时读任务清单统计接口；报告页 KPI 改读 `summary.total_reports/sop_reports/agent_reports`。

### Requirement: Report row fields without case columns

**Reason**: 报告行按来源携带业务身份：SOP 行重新引入用例名称（冻结身份口径）与任务 ID，智能体行携带助手编号与名称；旧「禁止用例字段」约束随任务卡语义一并废止。
**Migration**: 见新需求「SOP report rows carry case identity and task id」与「Agent report rows carry assistant identity」。

### Requirement: Report workbench opens the task flow

**Reason**: 任务详情页 `/tasks/:id` 已随 retire-engines-agents 下线；报告行改为直接打开已生成的 HTML 报告。
**Migration**: 见新需求「Report row opens the generated report」。

### Requirement: Empty copy points to AI assistant

**Reason**: 空态文案改为说明「报告在执行完成后生成」并引导任务清单/平台助手，由新需求「Empty copy points to task execution」承接。
**Migration**: 前端空态文案切换到新需求口径。

### Requirement: Report workbench filters rows by status

**Reason**: 报告列表只含已完成的报告，任务状态筛选（已完成/失败/已停止）失去意义；筛选改为来源（全部/SOP/智能体）+ 关键字 + 日期。
**Migration**: 见新需求「Report workbench filters by source」。

### Requirement: 报告接口返回标准信封

**Reason**: 旧 csv/md 文件下载/查看端点随旧执行引擎遗产退役，列表负载结构改为报告台账；信封约束由新需求「报告台账接口返回标准信封」承接。
**Migration**: 列表消费方改读 `data.summary/total/items`；文件查看改走既有平台报告与对话栏日志通道。

### Requirement: 报告工作台不提供报告详情与用例分解路由

**Reason**: 单路由约束保留，但「行点击进 `/tasks/:id`」的场景随任务详情页下线而失效，改为打开报告文件；由新需求「报告工作台单路由约束」承接。
**Migration**: 见新需求「报告工作台单路由约束」与「Report row opens the generated report」。
