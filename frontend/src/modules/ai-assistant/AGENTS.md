# ai-assistant 模块 AGENTS.md

> **AGENTS 层级**：二级约束 —— 根 `AGENTS.md` 与上级 `frontend/AGENTS.md` 优先于本文件（本文件只写增量）。

> 全局边界 / 模板样式 / 协议要点 / 关单清单 → `../../AGENTS.md`；本文只写本模块增量，冲突以全局为准。

## UI 布局

- 入口 `/ai-assistant/agents`（`index.vue`）；`viewMode` 由路由驱动（`agents` / `toolbox`），两子项共用 `index.vue`。评测中心与知识库已下线。
- `agents` 视图 = 纵向两个区块：
  1. **小助手看板** `.duty-section` → `AgentRouteCard` × 1（`device_control`）：身份卡 = **左正方形头像**（边长 = 右三行自然总高）+ **右三行**（名称 / `职责：UI自动化` / 助手状态）+ **底栏**「校验」「配置」（仅超管）。无独立功能标题带。每条线路独立 `route_configs.{route}.name/avatar`；第三行连通徽标**仅三种业务态**：
     - `ready` → 「已连通，可执行任务」
     - `unusable` → 「秘钥已连接，但无法使用」
     - `offline` → 「连接失败，小助手断线」
     探测进行中显示「校验中…」（过程态，非业务态）。**禁止**「未检测 / 已连通 / 已断开」。
     校验写入 `route_configs.{route}.health.status` + `results`（手动立即落库；`GET /ai/agents/health` 每 30 分钟复检；缺 `status` 的旧缓存视为过期并实探）。进页即探测，完成后徽标必为三态之一。
     探测语义：先证密钥可达（list），再对三角色发极短 chat；仅 chat 成功才算可用于执行；`is_connected`/`connected` 仅 `ready` 为 true。
  2. **任务卡片列表** `TaskBoard` → `FilterTabs` + 「新建任务」+ 调试「清空」（`POST /ai/agent-tasks/clear`）+ 按状态 `el-collapse` 分组 + 卡片字段：标题 / 状态 / 创建时间 / 设备 / **助手名**（`assistant_name`，实时取当前线路 `route_configs.device_control.name`，改名后列表刷新即同步，不固化在任务行）/ **费用**（列表行 `deepseek_cost`，与详情同一计价）/ **耗时**（`started_at`→`finished_at`，缺一则为 —）/ 「详情」。**失败卡**额外「重新执行」→ `POST /ai/agent-tasks/{id}/rerun`（克隆新建 pending，原失败记录不动）。「详情」跳转 `/ai-assistant/tasks/:taskId`。运行中按步写入 `result`；详情未终态时轮询。
- **任务详情页** `/ai-assistant/tasks/:taskId`（`TaskDetailPage`）：左「步骤清单」右「步骤详情」，每步按尝试卡片（`TaskAttemptCard`）展示执行结果与验证截图。**执行结果段内还有「日志检查」区块**（`StepLogCheck`，数据来自过程记录的 `executor_log_check`）：逐条列出本步**每一次副作用点击**的**点击前时间点**与**点击后截图路径**（路径以文本给出、有图可点开，未截图时标 `STEP_LOG_CHECK_NO_SHOT_TEXT`「该次点击后未截图」，不得借用验收截图）；该步被规划模型标记为需日志核对（`log_check`）时，块内嵌入与验收**同源**的 5 秒窗口证据（复用 `StepLogEvidence`，不另写一套等级/合并文案）。无点击且无日志时不渲染该块（`hasLogCheck`），存量任务无该键时如实不显示、不报错。**每张尝试卡片内还有「设备日志证据」区块**（`StepLogEvidence`，数据来自过程记录的 `log_evidence`，随任务详情接口原样下发，无需额外接口）：**摘要常显**（等级标签 + 条数 + 关键词 + 命中的功能点，例：`强证据 1 条 · switch_off · 关闭设备成功（#1 设备开关）`；`periodic` 必须显示为「疑似周期」并说明它不能单独作为通过依据）+ **详情折叠**四段（命中详情 / 动作前日志 / 超窗日志 / 窗口原始日志）。等级与结论的中文口径集中在 `helpers/log-evidence.ts`，组件只渲染；窗口日志**只消费服务端下发顺序、前端不排序不合并**（存量任务为旧顺序，如实呈现）；无证据时只显示一行说明（`NO_EVIDENCE_TEXT`），不得留空或报错；两个区块都只读，不提供任何写操作。
- `toolbox` 视图 = **装配台**（`ToolboxPanel`）：上区「助手此刻可用」生效芯片（总闸 AND 目录启用）；下区左**五源**（平台业务 / 自定义 Skill / 无线端口 / **模型调试** / **日志关键词**）+ 右目录。业务与 Skill 源行有「交给助手」总闸；其余三个来源**无总闸**（`gateKey` 为空），各自在来源定义里带 `meta` 副标题（**无总闸来源必须带 `meta`**，否则会掉进「n/m 生效」计数分支且分母借用 Skill 目录数——已由 `toolbox-assembly-port-source.spec.ts` 的公共断言守住），且都不进生效芯片、统计与「未装配」提示。系统提示词（规划 / 执行 / 验收）是**引擎常量**（`engines/ai/agents/config.py`）：前端不展示、不可编辑，装配台没有该来源，模型调试页也不展示其正文。自定义 Skill 目录 = `engines/ai/skills`（本地仓库 + 上传）。点击 Skill 卡片进入 `/ai-assistant/toolbox/skills/:name`（左目录 / 右内容，Markdown 渲染）。平台业务每张工具卡（含已停用）有「调试」→ `/ai-assistant/toolbox/tools/:toolName`（入参表单 + 真实调用；只读登录可执行，写工具仅超管且二次确认；`GET/POST /api/ai/platform-tools/{name}*`，禁止走 `/api/ai/tools/` 内部网关）。**入参表单的参数标签统一为「中文名（english_name）」+ 必填/可选 + 类型**：中文名与中文说明由服务端 schema 下发（`label` / `hint`，中文名在后端集中维护，前端不得硬编码中文映射，未登记时回退英文名），说明以悬浮提示呈现、不铺在表单里；标签拼接的唯一实现在 `helpers/tool-debug-label.ts`。**设备管理下真正操作手机的工具（list_apps / input_text / tap_screen / swipe_screen / press_key / current_app / click_ratio / drag_ratio / xpath_action）的 `serial` 是候选下拉**：候选 = 对请求者可见 + 在线 + 未被占用，随 schema 的 `options` 下发（无候选时给提示但仍可手输）；acquire_device / release_device 是设备池占用记账、不提供候选。业务模块默认折叠。左侧工具来源含**「无线端口」**（`WifiPortPanel`，无总闸、不交给助手）：五列表格（端口 / SKU名称 / 波特率 / 监听开关 / 日志查看，前三列只读，值来自平台配置登记）+ 监听开关（仅超管可改，关闭前二次确认并提示 AI 验收降级）+ 只读日志抽屉（当前文件尾部行、手动/自动刷新，同毫秒合并、最新在上；前端不排序）。左侧工具来源还含**「日志关键词」**（`LogKeywordPanel`，无总闸、不交给助手、**只读**）：用共享 `AppTable` 以**表格**展示对照表，恰为三列 `关键词 / 功能模块 / 功能点（#编号 + 名称）`，**一行一个「关键词 × 功能点」**（一个关键词对应多个功能点就是多行；现场 67 个关键词 → 约 70 行）；表格上方带搜索（同时作用于关键词 / 模块名 / 功能点名），计数恒报**全量**（`{关键词数} 个关键词 · {功能点数} 个功能点 · {行数} 行`）、搜索时也不缩水；数据来自 `GET /api/ai/log-keywords/`（`origin` 标明取自**运行中的采集索引**还是关键词表文件，并给出文件与更新时间），行与搜索的唯一实现在 `helpers/log-keyword-rows.ts`（**行序与表内逐行一致**，前端不重排不合并；搜索过滤是纯函数、不请求后端）；页面如实标注「改关键词表后需重启平台才用于判定」，且除搜索框与页头「刷新」外**没有任何新增 / 编辑 / 删除 / 上传 / 保存入口**（改表仍走文件）。

## 组件设计


## API 接口


## 快速验证清单
