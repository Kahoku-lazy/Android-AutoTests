# ai-assistant 模块 AGENTS.md

> **AGENTS 层级**：二级约束 —— 根 `AGENTS.md` 与上级 `frontend/AGENTS.md` 优先于本文件（本文件只写增量）。

> 全局边界 / 模板样式 / 协议要点 / 关单清单 → `../../AGENTS.md`；本文只写本模块增量，冲突以全局为准。

## UI 布局

- 入口 `/ai-assistant`（redirect 到 `/ai-assistant/agents`，`index.vue`）；侧栏「AI 助手」是**单一入口**，没有子项、页内也没有第二套 Tab。评测中心、知识库、AI 工具箱均已下线。
- `agents` 视图 = **小助手看板**：`AgentRouteCard` × 1（`device_control`）直接置于页面背景，不再使用 `.doc-section` 白底外框，也没有「平台小助手 / Assistant / N 个助手」区块标题行；卡片约 312px 宽、头像约 120px，右侧三行依次为名称/职责/配置，窄屏降档收缩。身份卡 = **左正方形头像**（边长 = 右侧三行自然总高）+ **右三行**（名称 / `职责：UI自动化` / 「配置」，仅超管）+ 无底部整行操作区。无独立功能标题带，**无连通状态徽标与校验按钮**（校验功能已下线）。每条线路独立 `route_configs.{route}.name/avatar`。任务卡片列表不在此页。
- **任务清单页** `/tasks`（`TaskListPage.vue`，侧栏「AI任务 / 任务清单」）承载 `TaskBoard` → `FilterTabs` + 「新建任务」+ 调试「清空」（`POST /ai/agent-tasks/clear`）+ 按状态 `el-collapse` 分组 + 卡片字段：标题 / 状态 / 创建时间 / 设备 / **助手名**（`assistant_name`，实时取当前线路 `route_configs.device_control.name`，改名后列表刷新即同步，不固化在任务行）/ **费用**（列表行 `deepseek_cost`，与详情同一计价）/ **耗时**（`started_at`→`finished_at`，缺一则为 —）/ 「详情」。**失败卡**额外「重新执行」→ `POST /ai/agent-tasks/{id}/rerun`（克隆新建 pending，原失败记录不动）。「详情」跳转 `/reports/task/:taskId`（事件流程报告），不再进入 `/ai-assistant/tasks/:taskId`。运行中按步写入 `result`；详情未终态时轮询。
  新建任务弹窗 = 任务标题 / 智能体（单选、必选；未选时提交置灰）/ 配置 YAML（单选）/ 设备（必选）/ 测试指定用例（前端用 `js-yaml` 解析 YAML 的 `title`，空=全部）。提交字段只有 `title / agent_id / device_serial / case_title / config`，不再提交任务目标与文档；`case_title` 由后端落库并传给 `run_platform_sop`。
- **任务详情页** `/ai-assistant/tasks/:taskId`（`TaskDetailPage`）：左「步骤清单」右「步骤详情」，每步按尝试卡片（`TaskAttemptCard`）展示执行结果与验证截图。**执行结果段内还有「日志检查」区块**（`StepLogCheck`，数据来自过程记录的 `executor_log_check`）：逐条列出本步**每一次副作用点击**的**点击前时间点**与**点击后截图路径**（路径以文本给出、有图可点开，未截图时标 `STEP_LOG_CHECK_NO_SHOT_TEXT`「该次点击后未截图」，不得借用验收截图）；该步被规划模型标记为需日志核对（`log_check`）时，块内嵌入与验收**同源**的 5 秒窗口证据（复用 `StepLogEvidence`，不另写一套等级/合并文案）。无点击且无日志时不渲染该块（`hasLogCheck`），存量任务无该键时如实不显示、不报错。**每张尝试卡片内还有「设备日志证据」区块**（`StepLogEvidence`，数据来自过程记录的 `log_evidence`，随任务详情接口原样下发，无需额外接口）：**摘要常显**（等级标签 + 条数 + 关键词 + 命中的功能点，例：`强证据 1 条 · switch_off · 关闭设备成功（#1 设备开关）`；`periodic` 必须显示为「疑似周期」并说明它不能单独作为通过依据）+ **详情折叠**四段（命中详情 / 动作前日志 / 超窗日志 / 窗口原始日志）。等级与结论的中文口径集中在 `helpers/log-evidence.ts`，组件只渲染；窗口日志**只消费服务端下发顺序、前端不排序不合并**（存量任务为旧顺序，如实呈现）；无证据时只显示一行说明（`NO_EVIDENCE_TEXT`），不得留空或报错；两个区块都只读，不提供任何写操作。
- **配置页** `/ai-assistant/agent/:id`（`AgentDetail`）：只保留**基本信息**——名称 / 头像 / 标签 / 描述，加两栏只读的**职责（UI自动化）**与**工作流（ui_auto_workflow）**（当前写死，不落库）。模型 / 线路 / 循环次数 / 模型校验区块已删除；保存时名称与头像仍会写入 `route_configs.device_control`，卡片与任务列表随之同步；模型配置改由后台维护。
- **AI 工具箱（装配台）已整体下线**：`/ai-assistant/toolbox`、Skill 查看页、平台工具调试页、`api/toolbox.ts` 与其组合式/纯函数全部删除；平台业务工具与自定义 Skill 不再有平台侧开关，SOP 的工具集由引擎代码固定装配（见 `sop-task-run`）。

## 组件设计


## API 接口


## 快速验证清单
