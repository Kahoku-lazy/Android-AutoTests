# task-list-module Specification

## Purpose
把任务域从 AI 助手拆成独立的前后端模块：后端 `task_list` 拥有任务、附件、事件、媒体与小时用量表及 `/api/tasks/*`，前端拥有 `/tasks` 列表与 `/tasks/:id` 详情；AI 助手只保留助手与线路/身份配置。

## Requirements

### Requirement: Task list app owns the task domain

系统 SHALL 提供 Django App `apps.task_list`，拥有 `Task`、`TaskAttachment`、`TaskEvent`、`TaskMedia`、`TaskUsageHourly` 五个模型，分别使用 `task_tasks`、`task_attachments`、`task_events`、`task_media`、`task_usage_hourly` 表。`Task.agent` MUST 为指向 `ai_assistant.AIAgent` 的外键。`apps.ai_assistant` MUST NOT 再定义任务、附件、任务事件、任务媒体或任务用量模型。

数据库迁移 MUST 通过重命名既有 `ai_tasks`、`ai_task_attachments`、`ai_task_events`、`ai_task_media`、`ai_usage_hourly` 完成，MUST NOT 丢失任何行、外键关系或自增序列。迁移 MUST 可回滚到旧表名。

#### Scenario: Existing task rows survive the table rename

- **WHEN** 迁移前数据库中存在任务、附件、事件、媒体与小时用量行
- **THEN** 迁移后这些行分别出现在 `task_tasks`、`task_attachments`、`task_events`、`task_media`、`task_usage_hourly`，行数与关联关系不变

#### Scenario: AI assistant no longer owns task models

- **WHEN** 迁移完成后检查 `apps.ai_assistant` 的模型
- **THEN** 其中不存在任务、附件、任务事件、任务媒体或任务用量模型

### Requirement: Task APIs live under /api/tasks

任务域接口 MUST 注册在 `/api/tasks/` 下：提交、列表、详情、重跑、关闭、删除、清空、详情报告与文件上传。旧 `/api/ai/tasks/*` 与 `/api/ai/agent-tasks/*` MUST 不再注册，直接访问 MUST 返回 404。响应信封 MUST 保持 `{status, data}`。

#### Scenario: New task endpoints respond

- **WHEN** 前端调用 `GET /api/tasks/`、`POST /api/tasks/submit/` 或 `POST /api/tasks/{id}/rerun/`
- **THEN** 请求命中 `task_list` 的视图并返回既有 `{status, data}` 结构

#### Scenario: Old task endpoints are gone

- **WHEN** 客户端访问 `/api/ai/tasks/submit/` 或 `/api/ai/agent-tasks/`
- **THEN** 返回 404，不发生任务创建或列表读取

### Requirement: AI assistant keeps only assistant and route configuration

`apps.ai_assistant` MUST 只保留 `AIAgent`、线路/身份配置页、`/api/ai/agents/*`、内置固定头像与配对引擎配置。它 MUST NOT 再提供任务列表、任务详情、任务创建、调度、重跑、关闭、删除、清空、任务费用或任务用量接口/页面，也 MUST NOT 再提供头像上传接口。

#### Scenario: Assistant page only configures routes

- **WHEN** 用户打开平台小助手页
- **THEN** 页面只展示助手与线路/身份配置，不出现任务列表、任务详情或新建任务入口

### Requirement: Frontend task list module

前端 SHALL 提供 `frontend/src/modules/task-list/`，路由 MUST 包含 `/tasks` 与 `/tasks/:id`，侧栏「AI任务」分组 MUST 提供「任务清单」入口。任务卡、新建任务弹窗、任务详情、日志证据、组合式函数与 API 客户端 MUST 从 `ai-assistant` 模块迁入；`ai-assistant` MUST NOT 再引用任务清单的私有组件或组合式函数。

#### Scenario: Task list module renders list and detail

- **WHEN** 用户访问 `/tasks` 或 `/tasks/:id`
- **THEN** 分别渲染任务清单列表与任务详情，接口请求走 `/api/tasks/*`

#### Scenario: AI assistant has no task imports

- **WHEN** 检查 `frontend/src/modules/ai-assistant/` 的 import
- **THEN** 不存在对 task-list 模块任务组件、组合式函数或任务 API 的引用

### Requirement: 任务详情页按需渲染轮次

任务详情页 MUST 默认只展开第一个用例，其余用例保持折叠；用户展开用例时才渲染其轮次。单个用例内的轮次 MUST 分页展示，每页 20 条，并显示「第 X / Y 页」与上一页 / 下一页控件。用例卡 MUST 带 `content-visibility: auto`，滚动到视口外的用例不参与布局与绘制。前端 MUST 按 `round_ids` 从 `data.rounds` 取轮次，MUST NOT 复制整份轮次对象。打开一个 12 用例、156 轮、8,640 条事件项的任务时，页面 DOM 节点 MUST 少于 3,000。

#### Scenario: 默认只展开第一个用例

- **WHEN** 打开一个含 12 个用例的任务详情
- **THEN** 只有第一个用例的轮次可见，其余 11 个用例为折叠态

#### Scenario: 轮次分页每页 20 条

- **WHEN** 展开一个含 60 轮的用例
- **THEN** 首屏只渲染 20 条轮次，并显示「第 1 / 3 页」
- **AND** 翻到第 2 页后渲染第 21–40 条

#### Scenario: 大任务 DOM 规模受控

- **WHEN** 打开任务 142（12 用例、156 轮、8,640 条事件项）并等待首屏稳定
- **THEN** `document.querySelectorAll('*').length` 小于 3,000

#### Scenario: 轮次顺序与接口一致

- **WHEN** 展开任一用例
- **THEN** 页面上的轮次顺序与该用例 `round_ids` 的顺序一致

### Requirement: 任务列表查询预算与轮询不叠加

`GET /api/tasks/` MUST 只查任务自身列，MUST NOT 通过 `select_related` 读取智能体的大字段；线路名 MUST 由数据库侧从 `route_configs` 中提取。单次列表请求 SQL MUST NOT 超过 5 条，附件 MUST 批量取。前端运行态轮询 MUST 在上一轮未返回时跳过本轮，间隔 MUST NOT 小于 10 秒。

#### Scenario: 列表不再随任务数放大

- **WHEN** 请求 `GET /api/tasks/`，返回 N 条任务
- **THEN** SQL 条数与 N 无关（不超过 5 条）
- **AND** 不出现「每条任务一次附件查询」的 N+1

#### Scenario: 慢请求不叠加

- **WHEN** 上一次任务列表请求尚未返回，轮询到点
- **THEN** 本轮被跳过
- **AND** 上一次返回后按正常节奏继续

#### Scenario: 响应字段不变

- **WHEN** 对比改动前后的任务列表响应
- **THEN** `tasks[]` 的字段与取值口径一致（含 `assistant_name`、`attachment_names`、`deepseek_cost`）

### Requirement: 任务页轮询随路由停止

任务清单页与任务详情页的自动刷新 MUST 跟随「本页是否仍是当前路由」：离开该页面时 MUST 立即停止定时器与后续调度，MUST NOT 在离开后继续发起 `GET /api/tasks/` 或 `GET /api/tasks/{id}/report/`。该判定 MUST NOT 依赖组件卸载——页面可能被 keep-alive 缓存而组件始终未卸载。回到该页面时 MUST 恢复自动刷新，并 MUST 立即静默补拉一次。停止期间 MUST NOT 清空已加载内容、MUST NOT 把页面置为错误态、MUST NOT 重置滚动位置与已展开的用例/步骤。

#### Scenario: 离开任务清单后不再请求列表

- **WHEN** 用户从任务清单切到仪表盘，且清单里仍有运行中任务
- **THEN** 切走后 10 秒内不再出现 `GET /api/tasks/` 请求
- **AND** 清单已加载的数据保持不变

#### Scenario: 离开任务详情后不再请求报告

- **WHEN** 用户在一个运行中任务的详情页停留后切到其它页面
- **THEN** 离开后不再出现该任务的 `GET /api/tasks/{id}/report/` 请求
- **AND** 后端不再因这个已经无人查看的页面继续重建报告

#### Scenario: 回到页面恢复刷新

- **WHEN** 用户从其它页面回到一个仍在运行的任务详情页
- **THEN** 立即发起一次报告请求，随后恢复 3 秒节奏
- **AND** 期间不出现首屏骨架、已展开的用例保持展开

#### Scenario: 缓存页不被离开动作改脏

- **WHEN** 从任务 A 的详情页切到任务 B 的详情页，再回到任务 A
- **THEN** 任务 A 的缓存页在离开期间不发起任何请求、也不进入错误态
- **AND** 回到任务 A 时展示的仍是任务 A 的报告

### Requirement: 任务详情只对本次打开的任务发请求

任务详情页 MUST 只请求本次打开的那条路由所对应的任务。路由离开或切换到其它任务后 MUST NOT 用变化后的路由参数改写本页状态。任务标识缺失或非数字时 MUST NOT 发起报告请求，也 MUST NOT 因此进入错误态。报告请求返回 4xx 时 MUST 立即停止自动刷新并给出可手动重试的入口，MUST NOT 进入退避重试；仅网络错误与 5xx MAY 按既有阶梯退避。

#### Scenario: 离开详情页不发非法标识请求

- **WHEN** 用户离开任务详情页
- **THEN** 不出现 `/api/tasks/NaN/report/` 或 `/api/tasks/undefined/report/` 一类请求
- **AND** 控制台无对应的 404

#### Scenario: 切换到其它任务不串数据

- **WHEN** 从任务 A 的详情页直接打开任务 B 的详情页
- **THEN** 只有 B 页面向 B 发起报告请求，A 的缓存页不请求 B
- **AND** 返回 A 时仍显示 A 的数据

#### Scenario: 任务已删除时立即停止重试

- **WHEN** 自动刷新收到 404（任务已删除或不属于当前用户）
- **THEN** 不再发起第二次报告请求
- **AND** 页面给出手动重试入口

#### Scenario: 网络错误仍按阶梯退避

- **WHEN** 报告请求因断网或 5xx 失败
- **THEN** 仍按 3 秒 → 6 秒 → 12 秒 → 30 秒退避重试，超过上限后停止

### Requirement: 任务清单展示任务统计

任务清单页 SHALL 在任务卡之上展示三个统计指标：**总任务数**、**成功率**、**执行中任务数**。统计 MUST 来自服务端的只读统计接口，MUST NOT 由前端对已加载的任务行自行汇总（列表接口只返回最近 100 条，自行汇总会给出错误总数）。统计接口 MUST 只统计当前用户可见的任务，且 MUST 用一次聚合查询得出，MUST NOT 读取任务明细行。总任务数 MUST 覆盖全部状态的任务，执行中 MUST 只统计状态为 `running` 的任务。

成功率 MUST 定义为「成功任务数 ÷ 已结束任务数」，已结束任务 MUST 为总数减去执行中与待执行。成功任务 MUST 包含状态 `completed` 与 `success`。已结束任务数为 0 时，成功率 MUST 显示为「—」，MUST NOT 显示 0%。

统计信息 MUST 与任务列表同源刷新：列表因删除、清空、重跑或运行态轮询而更新时，统计 MUST 一并更新；MUST NOT 为统计单独新增定时器。

#### Scenario: 统计条给出三项指标

- **WHEN** 用户打开任务清单页，库中有 15 条任务且其中 1 条正在执行
- **THEN** 统计区显示总任务 15、执行中 1
- **AND** 成功率按已结束任务计算

#### Scenario: 成功率按已结束任务计算

- **WHEN** 库中有 9 条成功、1 条失败、2 条执行中的任务
- **THEN** 成功率为 90%
- **AND** 总任务为 12、执行中为 2

#### Scenario: 没有已结束任务时显示「—」

- **WHEN** 库中只有 2 条待执行任务
- **THEN** 成功率显示为「—」
- **AND** MUST NOT 显示 0%

#### Scenario: 只统计当前用户可见的任务

- **WHEN** 库中存在属于其他用户智能体范围的任务
- **THEN** 总数、成功率与执行中都不包含这些任务

#### Scenario: 删除任务后统计同步更新

- **WHEN** 用户在清单页删除一条任务
- **THEN** 总任务数减 1，成功率随之重算
- **AND** MUST NOT 需要手动刷新页面

### Requirement: 任务清单展示任务结果占比

任务清单页 SHALL 展示任务结果占比图，按**成功**、**失败**、**中断**、**取消**四类给出占比。四类 MUST 分别对应状态：成功 `completed`/`success`、失败 `failed`、中断 `interrupted`、取消 `cancelled`；其余状态（待执行、执行中、暂停）MUST NOT 进入占比图的扇区。数量为 0 的类别 MUST NOT 画扇区，但 MUST 仍在图例中列出，以说明该类别当前为空。

占比图的图例 MUST 置于图表上方并横向排列，MUST 只显示颜色与类别名，MUST NOT 显示条数（如「14 条」）或百分比。各类占比 MUST 由图表上的标签显示。库中没有任何任务时，占比图 MUST 显示空态提示，MUST NOT 渲染出一个占满圆环的假扇区。

占比图 MUST 在同一区块内附一张**数量柱状图**：横轴为四类结果，纵轴为条数，每根柱 MUST 标注条数标签；柱色 MUST 与占比图扇区同色。

#### Scenario: 四类占比与数量

- **WHEN** 库中有 7 条成功、2 条失败、1 条中断、0 条取消
- **THEN** 占比图为三个扇区，分别标出 70%、20%、10%
- **AND** 图例横向列出四项（成功 / 失败 / 中断 / 取消），取消仍在列但不画扇区

#### Scenario: 图例不显示条数与百分比

- **WHEN** 用户查看占比图图例
- **THEN** 每一项只有颜色圆点与类别名
- **AND** MUST NOT 出现条数或百分比文字

#### Scenario: 执行中不计入占比

- **WHEN** 库中同时存在执行中与待执行任务
- **THEN** 占比图的四类数量加起来不等于总任务数
- **AND** 图例不出现「执行中」类别

#### Scenario: 数量柱状图与扇区同源

- **WHEN** 库中有 14 条成功、10 条失败、4 条中断、3 条取消
- **THEN** 数量柱状图为 4 根柱，数值分别为 14、10、4、3
- **AND** 柱色与占比图对应扇区一致

#### Scenario: 空库显示空态

- **WHEN** 任务库没有任何任务
- **THEN** 占比图区域显示空态提示
- **AND** MUST NOT 画出扇区

### Requirement: 任务清单按智能体展示任务柱状图

任务清单页 SHALL 为每个**当前用户可见的智能体**各展示一张任务柱状图，与总体数量柱状图并排。每张图 MUST 展示该智能体的成功 / 失败 / 中断 / 取消条数，并 MUST 给出该智能体的总数、执行中条数与成功率。智能体清单 MUST 来自统计接口，MUST NOT 由前端硬编码；新增智能体后图表 MUST 自动多一张，MUST NOT 需要改前端代码。没有任务的智能体 MUST 仍展示一张全 0 的图，MUST NOT 被隐藏。其他用户私有智能体 MUST NOT 出现。

#### Scenario: 每个可见智能体一张图

- **WHEN** 库中只有 Agent-01号 与 Agent-02 两个可见智能体
- **THEN** 区块内出现三张柱状图：总体数量、Agent-01号、Agent-02
- **AND** 每张图标出该智能体自己的四类条数

#### Scenario: 新增智能体自动多一张图

- **WHEN** 平台新增第三个智能体（即使还没有任务）
- **THEN** 板块内自动出现第三张该智能体的柱状图
- **AND** 该图四类条数均为 0，成功率显示「—」

#### Scenario: 他人私有智能体不出现

- **WHEN** 另一个用户拥有一个私有智能体
- **THEN** 当前用户的图表里 MUST NOT 出现该智能体

#### Scenario: 四张图卡片等高

- **WHEN** 宽屏下同时展示占比图与三张柱状图
- **THEN** 四张卡的上下边界 MUST 对齐（同一行等高）
- **AND** 环图与柱图的可绘制高度随之拉伸，MUST NOT 出现某张卡明显更矮

### Requirement: 详情页展示四层耗时

任务详情页 MUST 展示四层耗时：用例标题行给出用例耗时，步骤行给出步骤耗时，执行过程与验收过程的块头分别给出该轮的模型耗时。

用例与步骤的耗时 MUST 出现在结果徽标之前（从左到右：耗时、结果），并 MUST 用青色时间片呈现（2px 描边 + 青色底 + 粗体），MUST NOT 用次要文字色弱化成与说明文字同级。

墙钟耗时 MUST 与模型耗时用不同措辞区分：步骤与用例只给数字（如 `3m12s`），模型耗时 MUST 带「模型」前缀（如 `模型 38s`）。格式 MUST 统一为紧凑写法：不足 1 分钟用 `42s`，不足 1 小时用 `3m12s`，超过 1 小时用 `1h02m`。

轮次尚未结束时 MUST 显示「进行中」，MUST NOT 显示 `0s`。耗时缺失或为 0 时 MUST 不渲染任何耗时文案，MUST NOT 显示占位破折号。

#### Scenario: 步骤行带耗时

- **WHEN** 某步骤的 `duration_ms` 为 192000
- **THEN** 该步骤行的结果徽标旁显示 `3m12s`

#### Scenario: 耗时排在结果徽标之前

- **WHEN** 某用例的 `outcome` 为 PASS 且 `duration_ms` 为 250000
- **THEN** 该用例标题行从左到右先出现 `4m10s`，再出现 `PASS`
- **AND** 两者都是带描边的时间/状态徽标，耗时不着次要文字色

#### Scenario: 执行块头带模型耗时

- **WHEN** 某执行轮 `model_ms` 为 38000
- **THEN** 该块头在角色徽标与模型名之后显示 `模型 38s`

#### Scenario: 运行中显示进行中

- **WHEN** 某轮 `running` 为 true
- **THEN** 该块头显示「进行中」而不是耗时数字

#### Scenario: 缺时间戳不显示耗时

- **WHEN** 某步骤的 `duration_ms` 为 0 或缺失
- **THEN** 该步骤行只显示结果徽标，不出现 `0s` 或破折号

### Requirement: 任务执行状态徽标七态分色且底色渐变

任务清单「执行状态」徽标 MUST 为每个状态提供可区分的色相，覆盖 `pending` / `running` / `paused` / `success` / `failed` / `interrupted` / `cancelled` 七态；SHALL NOT 让任一状态回落到无彩灰底。徽标底色 MUST 是该状态色的**纵向渐变**（上约 20% → 下约 5% 混白），描边 MUST 取该状态色；文字 MUST 用墨色（状态色只承载描边与底色），以保证在浅渐变底上的可读对比度。色相 MUST 全部取自 `tokens.css` 已登记令牌，SHALL NOT 写字面色值。

#### Scenario: 七态各有独立色相

- **WHEN** 任务清单同时渲染待执行、执行中、任务暂停、任务成功、任务失败、已中断、任务取消七种状态
- **THEN** 七枚徽标的底色与描边两两不同
- **AND** 不存在与「默认灰底」完全相同的徽标

#### Scenario: 底色是渐变而非平涂

- **WHEN** 检查任一状态徽标的背景
- **THEN** `background-image` 含 `linear-gradient`
- **AND** 渐变两端分别约为该状态色的 20% 与 5% 与卡片底的混合

#### Scenario: 文字仍可读

- **WHEN** 测量任一状态徽标的文字色与底色
- **THEN** 文字为墨色，不直接使用浅色状态令牌作前景
- **AND** 文字与底色的对比度不低于 4.5:1

### Requirement: 任务清单工具栏布局与工作流下拉筛选

任务清单的工作流筛选 MUST 是下拉控件，选项 MUST 为「全部」加当前存在的每个工作流；选项数据 MUST 复用 `/api/tasks/` 响应里的 `workflows`（该字段由后端 `ai_assistant.api.list_sop_workflows()` 提供，已删除的工作流不出现），前端 SHALL NOT 另拉一份或在前端重算工作流清单。「显示行数」工具条与上方筛选行、与下方表格之间的垂直间距 MUST 明显大于控件自身间隙（不小于 16px）。「上一页 / 下一页」MUST 位于工具条右端；不可点击时 MUST 呈灰底灰边并撤除位移阴影，与可点态可区分。

#### Scenario: 工作流用下拉筛选

- **WHEN** 打开 `/tasks`
- **THEN** 工作流筛选是一个下拉，默认显示「全部」，展开后列出当前每个工作流名
- **AND** 选择一个工作流后表格只剩该工作流的任务

#### Scenario: 工具条上下留白

- **WHEN** 检查「显示行数」工具条
- **THEN** 它与上方筛选行的间距、与下方表格的间距都不小于 16px

#### Scenario: 翻页键靠右且禁用置灰

- **WHEN** 任务只有 1 页
- **THEN** 「上一页 / 下一页」位于工具条右端，且两键均为灰底灰边、无位移阴影
- **AND** 多页时可用键恢复原底色与阴影

### Requirement: 任务清单每页固定 10 行且无行数选择器

任务清单每页 MUST 固定 **10** 行；取值 MUST 来自模块 `constants.ts`（选项集与默认值同源），页面 SHALL NOT 内联行数字面量。工具栏 MUST NOT 渲染「显示行数」标签或行数按钮组。分页文案与翻页键仍 MUST 保留「第 X / Y 页 · 共 N 条」与上一页 / 下一页。

#### Scenario: 每页 10 行

- **WHEN** 打开 `/tasks` 且任务多于 10 条
- **THEN** 表格每页呈现 10 行

#### Scenario: 无行数选择器

- **WHEN** 检查工具栏
- **THEN** 不存在「显示行数」标签与行数按钮
- **AND** 分页选项集仍由模块 `constants.ts` 提供

### Requirement: 任务清单展示用例身份

任务清单 MUST 在工作流列之后展示「用例」列。展示文案 MUST 只由该任务的用例身份算出，MUST NOT 回读用例库，也 MUST NOT 从步骤名或附件正文反推。一条用例 MUST 只显示标题。多条 MUST 显示「第一条标题 · 共 N 条」，悬停 MUST 按选择顺序列出「项目名 / 标题」。来源为里程碑且没有行时 MUST 显示「里程碑」。没有用例身份的任务 MUST 显示「—」。该列 MUST NOT 改变任务标题、执行状态、附件名或分页。

#### Scenario: 一条用例直接显示标题

- **WHEN** 任务的用例身份只有一条，标题为「H6810 定时」
- **THEN** 用例列显示「H6810 定时」
- **AND** 不显示「共 1 条」

#### Scenario: 多条用例显示计数与悬停名单

- **WHEN** 任务按顺序冻结了「定时」「场景」「音乐」三条用例
- **THEN** 用例列显示「定时 · 共 3 条」
- **AND** 悬停按顺序给出三条「项目名 / 标题」

#### Scenario: 上传里程碑与旧任务分开

- **WHEN** 同一页有一条上传里程碑的任务和一条没有用例身份的历史任务
- **THEN** 前者用例列显示「里程碑」
- **AND** 后者用例列显示「—」
