# PRD-08 — AI 助手 (AI Assistant)

> 关联模块：`apps/ai_assistant/` · 前端：`frontend/src/modules/ai-assistant/`
> 关联全局：`[需求大纲.md](./需求大纲.md)` §5.8
> 关联上游：`[PRD-02-设备管理](./PRD-02-设备管理.md)` · `[PRD-03-设备检查器](./PRD-03-设备检查器.md)` · `[PRD-04-元素定位](./PRD-04-元素定位.md)` · `[PRD-05-用例管理](./PRD-05-用例管理.md)` · `[PRD-06-执行引擎](./PRD-06-执行引擎.md)` · `[PRD-09-工作流工作台](./PRD-09-工作流工作台.md)`（经 26 个平台 Tool 调用各模块）
> 版本：v6.16 · 状态：评审中 · 日期：2026-08-28

**修订记录**

- v6.16（2026-08-28）：**两条线路 + 任务发布 + 移除主对话**——智能体改为「控制设备 / 平台任务」两条能力线路（`route_configs`：每线路 planner/executor 模型配置）；新增任务发布（`POST /ai/tasks/submit` + `GET /ai/agent-tasks`）；移除 SSE 流式对话与前端聊天窗口。详细契约以 ARCH-08 v3.4 与 openspec change `refactor-ai-two-routes-task-publishing` 为准；正文 §1/§2/§5 中「智能对话中枢 / 流式对话」相关表述为待全文同步的旧表述。



## 1. 功能定位

AI 助手是平台的**智能对话中枢**，用户通过创建任务卡片来驱动AI助手完成任务。

**核心职责**：

- **平台小助手**：见 [PRD-08-AI助手-01-平台小助手](./PRD-08-AI助手-01-平台小助手.md)（智能体看板 + 任务下发）。

- **知识库管理**：ChromaDB 向量库状态、文档列表、重建索引；**知识库开关 + 文档引用范围在知识库页统一配置**
- **评测中心**：自然语言用例生成与执行
- **AI 工具箱**：集中管理共享 skill / MCP / 扩展；**统一配置能力开关（业务/内置/MCP/Skill）与工作区 Skills**；并**展开展示 + 全局启用/停用平台业务工具与 MCP/Skill**（按模块分组、逐个说明功能；MCP/Skill 直接启用/停用，无「导入到智能体」）
---

## 2. 业务功能

### 2.1 平台小助手（F-01-01）

> 已拆分至独立 PRD：[PRD-08-AI助手-01-平台小助手](./PRD-08-AI助手-01-平台小助手.md)（功能简介 / UI布局 / 详细功能）



### 2.3 API Key 安全（F-01-03）

API Key 全程加密存储（Fernet），列表 / 详情只返回脱敏值，完整 Key 仅一次性查看。


| 规则    | 行为                                                                 |
| ----- | ------------------------------------------------------------------ |
| 写入    | 明文 Key 经 `encrypt_key()` 加密后落库，DB 值不以 `sk-` 开头                     |
| 展示    | 列表不返回 Key；详情返回 `mask_key()` 脱敏值（前 3 + `***` + 后 4）                 |
| 一次性查看 | `POST /agents/{id}/reveal-key` 仅首次返回明文，之后返回脱敏值 + `revealed: false` |
| 更新    | 前端回传 `***` 掩码视为未变更，跳过更新保留原值；Key 变更后 `key_revealed` 复位              |


**验收标准**：

- `GET /ai/agents` 响应无 `api_key` 字段
- `GET /ai/agents/{id}` 的 `api_key` 为脱敏值
- reveal-key 首次返回明文，二次返回脱敏；Key 变更后可再次查看一次
- 解密失败返回空字符串而非崩溃，不 fallback 原文



### 2.4 模型连接测试与检测（F-01-04）

- **连接测试**（`POST /agents/{id}/test`）：调 `/models` 或 `/chat/completions` 验证连通性，回写 `is_connected` + `available_models` + `last_checked_at`
- **模型检测**（`POST /models/detect`）：用 provider + api_key + base_url 拉取可用模型列表，供配置页合并去重

**边界状态**：


| 场景         | 行为                                         |
| ---------- | ------------------------------------------ |
| API Key 无效 | `connected: false`，message 返回 HTTP 状态与错误摘要 |
| 网络不可达      | `connected: false`，message 返回连接错误          |


**验收标准**：

- 连接成功返回 `connected: true` + 模型列表；失败返回 `connected: false` + message
- 检测到的模型与内置模型合并去重，当前选中模型始终在列表中



### 2.5 能力开关（F-01-05）

平台唯一智能体通过四组能力开关决定可用的工具集，构建时由 `agent_factory` 按开关组装 Toolkit。**开关配置已从智能体配置页下沉**：业务/内置/MCP/Skill 开关在「AI 工具箱」页配置，知识库开关在「知识库」页配置（经 `platform-config` 读写），智能体配置页只保留模型/提示词/参数。


| 开关字段                                          | 默认         | 启用后注入的工具                                                                                |
| --------------------------------------------- | ---------- | --------------------------------------------------------------------------------------- |
| `enable_workspace_tools`                      | false      | 6 个 AgentScope 内置文件工具（Bash / Edit / Glob / Grep / Read / Write），受 `skills_config` 逐工具开关 |
| `enable_business_tools`                       | false      | 平台业务工具（见 §4.1），具体启用哪些由 AI 工具箱全局开关（`ai_platform_tools`）决定（§2.12）                         |
| `enable_mcp_tools`                            | false      | 共享工具箱中已启用的 MCP 客户端（`AISharedTool(item_type=mcp, enabled=True)`，直接启用/停用无导入）              |
| `enable_skills`                               | false      | 共享工具箱中已启用的 skill 目录（`AISharedTool(item_type=skill, enabled=True)`，直接启用/停用无导入）           |
| `enable_knowledge_base` + `knowledge_sources` | false / {} | 知识库文档过滤：`doc:相对路径` 按文件引用；`dir:相对目录` 按目录动态引用（检索时展开为目录下当前全部文件）                            |


平台唯一智能体默认**纯对话模型**（全部开关 false，无默认系统提示词）。

**验收标准**：

- 未启用 business_tools 时，`/api/tools/agent-config` 返回 `enabled_tools: []`
- 启用 workspace_tools 但 `skills_config` 关闭 Bash 时，构建出的 Toolkit 不含 Bash
- `knowledge_sources` 只导入的文档 / 目录参与 `search_knowledge_base` 检索；目录引用（`dir:`）动态展开，新增 / 删除文件自动生效
- 开关 / 文档范围经 `platform-config` 读写，与智能体配置页解耦（保存智能体不覆盖这些字段）



### 2.6 SSE 流式对话（F-02-01）

对话页发起 `POST /conversations/{id}/chat/stream`，AgentScope 在 Django 进程内运行，`reply_stream` 事件经 SSE 逐 token 流式返回。单请求完成「构建 Agent → 恢复上下文 → 流式回复 → 持久化」。

**流式生命期**：构建 Agent（进程内）→ 保存用户消息 → 恢复历史上下文 → `reply_stream` 消费事件 → SSE 推送 → 终端事件时后端持久化 assistant 消息。

**模型状态**（`MODEL_STATUS_MAP`）：思考中 / 调用模型 / 调用工具 / 输出中 / 已完成。

**组件**：`ChatView.vue` + `useSSE` + `api/sse.ts`（`streamChat` 用原生 fetch 读 ReadableStream，401 自动刷新重试一次）。

**边界状态**：


| 场景          | 行为                                            |
| ----------- | --------------------------------------------- |
| 消息为空且无附件    | 400「消息不能为空」                                   |
| 无权限访问对话     | 403                                           |
| 对话不存在       | 404                                           |
| 2 分钟无事件     | SSE 发送心跳注释 `: heartbeat`                      |
| 客户端断开 / 换对话 | 取消旧 agent Task（`CancelledError`），保留已生成内容，后台续跑 |
| 模型服务不可用     | 顶部降级横幅「AI 模型服务暂不可用…」                          |
| 同一对话重复请求    | 取消上一 stale Task，保留最新                          |


**验收标准**：

- 回复逐 token 渲染，非整段一次性
- 切换 / 关闭对话后已生成内容不丢失，历史消息从后端加载
- 401 时自动刷新 token 并重试一次
- 终端事件（REPLY_END / ExceedMaxIters）后端持久化 assistant 消息



### 2.7 消息渲染（F-02-02）

每条消息经 `MessageBubble` 渲染，按内容块类型区分：


| 内容块  | 渲染                      | 说明                                |
| ---- | ----------------------- | --------------------------------- |
| 文本   | Markdown + Mermaid 图表   | `useMarkdown` 渲染                  |
| 思考块  | `ThinkingBlock`（默认折叠）   | ReAct 推理过程，多轮可折叠                  |
| 工具调用 | `ToolCallCard`（折叠 / 展开） | 工具名 + 参数 + 结果                     |
| 提示块  | `HintCard`              | SOP 阶段卡片 / 任务卡片（内嵌进度）/ PRD 用例预览卡片 |
| 数据块  | 图片气泡                    | 用户上传图片                            |


**任务卡片**（内嵌于对话流）：`run_test` / `get_run_status` / `stop_run` 工具调用时，`ChatView` 解析输出维护内嵌进度卡片（PENDING → RUNNING → COMPLETED / FAILED / STOPPED）。

**组件**：`MessageBubble.vue` + `ThinkingBlock` / `ToolCallCard` / `HintCard` + `useMarkdown` / `useMessageStore`。

**HintCard 提示变体**（`hint.type` 区分，见 `HintCard.vue`）：


| type               | 渲染                  | 说明                                                              |
| ------------------ | ------------------- | --------------------------------------------------------------- |
| `sop_card`         | SOP 工作流卡片           | 阶段徽标 Phase1~4（`phase-1`~`phase-4`）、需求、用例设计列表、下一步提示              |
| `task_card`        | 任务卡片                | 状态徽标（PENDING/RUNNING/COMPLETED/FAILED/STOPPED）、run_id、标题、设备、用例数 |
| `prd_case_preview` | PRD 用例预览卡片          | 生成用例总数 / P0 必测 / P1 应测统计 + 「导入到用例库」按钮                           |
| 其他 / 字符串           | 通用提示块（`hint-block`） | 兜底渲染                                                            |


**验收标准**：

- Markdown 与 Mermaid 正常渲染；思考块默认折叠可展开
- 工具调用卡片折叠 / 展开切换正常，含参数与结果
- 任务卡片随工具调用更新进度与终态



### 2.8 HITL 工具确认（F-02-03）

Agent 执行写操作工具前，若需要用户确认，流中返回 `RequireUserConfirmEvent`，前端弹出确认对话框；用户 ALLOW / DENY / 全部允许 / 全部拒绝后，结果经 `POST /conversations/{id}/confirm-result` 回传正在运行的 Agent。

**实现**：进程内会话注册表接收确认结果并回传给运行中的 Agent（实现结构见 ARCH-08 §3.3）。

**组件**：`ConfirmDialog.vue` + `useToolConfirm`。

**边界状态**：


| 场景                | 行为                            |
| ----------------- | ----------------------------- |
| 确认超时（2 分钟）        | 记录 warning，终止本轮回复             |
| 无活跃 agent session | 400「No active agent session…」 |
| 确认队列已满            | 409「Agent is busy」            |


**验收标准**：

- 确认弹窗展示工具名与参数，支持单个 / 全部允许 / 拒绝
- ALLOW 后 Agent 继续执行，DENY 后跳过该工具
- 确认结果经 `AIExecutionLog` 记录审计



### 2.9 文件 / 图片上传（F-02-04）

对话输入栏支持上传文档与图片：


| 类型  | 支持格式                                                                                                 | 大小上限 | 处理                          |
| --- | ---------------------------------------------------------------------------------------------------- | ---- | --------------------------- |
| 文档  | txt / log / md / markdown / json / xml / csv / py / js / html / css / yaml / yml / docx / xlsx / pdf | 20MB | 解析为文本注入消息（超 5 万字符截断）        |
| 图片  | png / jpg / jpeg / webp / gif                                                                        | 5MB  | base64 编码，随消息以 DataBlock 发送 |


**组件**：`ChatInput.vue` + `api/agents.ts`（`uploadFile`）。头像上传走 `upload-avatar`（data URI 存 DB）。

**边界状态**：


| 场景                     | 行为                          |
| ---------------------- | --------------------------- |
| 不支持的文件类型               | 400「Unsupported file type」  |
| 文件超限                   | 400「File too large」         |
| docx / xlsx / pdf 解析失败 | 返回 `parse_error`，前端展示解析失败标记 |


**验收标准**：

- 文本 / 文档上传后解析内容注入消息，图片以 DataBlock 随消息发送
- 一次仅支持 1 张图片（多图 400）
- 上传文件在解析后即时清理临时文件



### 2.10 知识库管理（F-03-01）

「知识库」Tab 展示 ChromaDB 向量库状态（文档数 / 库大小 / 上次索引 / 状态）与可索引文档列表，支持重建索引。

**文档来源**：`rag_service.py` 动态扫描 `dev_docs/` 下所有 Markdown + 生成的步骤类型参考。

**目录树查阅（v6.2）**：文档列表按 `dev_docs/` 下的本地目录层级排列——目录作为折叠标题（如 `02-PRD需求`），文件收纳其中；嵌套目录逐层折叠。非 `dev_docs` 来源（步骤类型参考等）归入「其他/参考」兜底组。

**目录引用（v6.2）**：智能体引用知识库时可选**整个目录**（`dir:相对目录` 键）或**单个文件**（`doc:相对路径` 键），两者可混选。目录引用为**动态语义**：检索时后端展开为目录下当前全部文件，目录内新增 / 删除文件自动生效，无需重新勾选。

**组件**：`KnowledgeBase.vue` + `KnowledgeImportDialog.vue` + `helpers/kb-tree.ts` + `api/toolbox.ts`（`getKnowledgeStatus` / `getKnowledgeDocuments` / `reindexKnowledge`）。

**边界状态**：


| 场景           | 行为                   |
| ------------ | -------------------- |
| 索引重建进行中      | 409「索引重建已在进行中」       |
| ChromaDB 不可用 | 状态返回 doc_count 0，不崩溃 |
| 知识库为空        | 检索跳过，返回空列表           |
| 目录键对应目录已删除   | 展开为空，检索跳过该键          |
| 历史 `doc:` 键  | 完全兼容（剥前缀比对 source）   |


**验收标准**：

- 状态卡展示文档数 / 库大小 / 上次索引时间
- 文档列表仅返回元数据（不含正文），供智能体配置页勾选
- 重建索引异步执行，状态页可查询进度
- 知识库 Tab 文档按本地目录折叠树展示，目录标题与 `dev_docs/` 实际目录一致
- 导入弹窗支持目录级与文件级混选；已导入列表能区分展示目录引用与文件引用
- `dir:` 目录引用在检索时动态展开，目录内文件增删后检索结果随之变化



### 2.11 评测中心（F-04-01）

「评测中心」Tab 提供自然语言用例生成与执行：输入自然语言描述 → 选择目标设备 → 生成用例或直接执行。调用 `evaluator-api.ts` 封装 API（评估器模块 `ev_` 前缀）。

**组件**：`EvaluatorTab.vue`。

**验收标准**：

- 自然语言描述可生成用例或触发执行
- 执行轮询间隔 2s（`EVALUATOR_POLL_MS`）



### 2.12 AI 工具箱（F-05-01）

「AI 工具箱」Tab 是平台**工具与能力开关的统一配置入口**：能力开关（业务/内置/MCP/Skill）、平台业务工具启停、工作区 Skills、共享 skill / MCP / 扩展的启停。

**集中管理规则（硬约束）**：

- 平台只用唯一智能体：MCP / Skill 在工具箱**直接启用/停用**，`agent_factory` 直接读 `AISharedTool(enabled=True)`，无 per-agent 副本与「导入」
- 工具箱是 skill 上传 / MCP 配置的**唯一入口**
- 能力开关（`enable_business_tools` / `enable_workspace_tools` / `enable_mcp_tools` / `enable_skills`）与工作区 Skills（`skills_config`）经 `platform-config` 读写，仅超管可改


| 项类型       | 说明                                                     |
| --------- | ------------------------------------------------------ |
| skill     | 上传 skill 文件夹，存 `data/shared_skills/{id}/`；启用 = 直接加载该目录 |
| mcp       | 共享 MCP 配置；启用 = 直接装配 MCP 客户端                            |
| extension | 扩展配置                                                   |


**启停**：`POST /ai/toolbox/{id}/toggle`（仅超管）直接改写 `AISharedTool.enabled`。

**组件**：`ToolboxPanel.vue` + `composables/usePlatformTools.ts` + `composables/usePlatformConfig.ts` + `api/toolbox.ts`。

**平台业务工具目录与全局启停**：

AI 工具箱除集中管理共享项外，还**展开展示平台业务工具并全局启用/停用**——选用哪个平台工具由 AI 工具箱**全局统一决定**（所有智能体共享），智能体配置页（F-01-05）只保留「业务工具」总开关，不再逐工具勾选。

- **数据来源**：`GET /api/ai/available-tools`（按 7 分类返回平台工具，含每个工具的全局 `enabled` 状态）
- **展示**：按 7 个模块分类（设备管理 / 设备检查器 / 元素定位 / 用例管理 / 测试执行 / 工作流 / 知识库）折叠面板，默认全部展开；每个工具显示工具名、功能说明（`summary`）、只读/写徽章（`read_only`）、启用状态
- **启停**（仅超级管理员）：每个工具「启用/停用」两键；每个分类折叠栏「全部启用/全部关闭」两键；写 `POST /ai/platform-tools/toggle`
- **默认**：新工具默认全启用；停用 = 记 `ai_platform_tools` 记录（enabled=False），启用 = 删记录回默认
- **边界**：全局共享，非智能体私有配置；智能体只通过 `enable_business_tools` 总开关决定是否启用业务工具整体

**验收标准**：

- 工具箱列表 / 创建 / 更新 / 删除 / 上传 skill 正常
- 删除 skill 类型项时清理上传目录
- 智能体配置页**不存在**自上传 skill / 自配置 MCP 的 UI 入口
- 智能体级 `mcp/save`、`mcp/test`、`skill/upload` 端点已移除（404）
- 「平台业务工具」区按 7 分类展开展示每个工具及其功能说明、只读/写标识、启用状态，默认全部展开
- 单个工具「启用/停用」、分类「全部启用/全部关闭」即时生效；非超管不可见启停按钮、调用 toggle 返回 403
- MCP / Skill 在工具箱「启用/停用」直接生效（`AISharedTool.enabled`），`import-from-toolbox` 与 `agents/{id}/tools*` 端点已移除（404）
- 能力开关与工作区 Skills 经「能力开关 / 工作区 Skills」区块读写 `platform-config`，保存智能体不覆盖这些字段



## 5. API 接口功能

鉴权：除 `/api/tools/*`（工具网关，内部服务）外全部端点需要 JWT Bearer。响应统一 `{status, data}` / `{status, message}`，JSON 字段 snake_case。

### 5.1 端点总览（39 行 · 32 个存活）


| #   | 方法   | 端点                                          | 功能                                        | 前端消费 |
| --- | ---- | ------------------------------------------- | ----------------------------------------- | ---- |
| 6   | POST | `/ai/agents/{id}/reveal-key`                | 一次性查看完整 Key（F-01-03）                      | ❌    |
| 7   | GET  | `/ai/agents/{id}/conversations`             | 智能体对话列表                                   | ✅    |
| 8   | POST | `/ai/agents/{id}/conversations/create`      | 新建对话                                      | ✅    |
| 9   | GET  | `/ai/conversations/{id}/messages`           | 消息列表                                      | ✅    |
| 10  | POST | `/ai/conversations/{id}/save-message`       | 保存消息                                      | ✅    |
| 11  | POST | `/ai/conversations/{id}/confirm-result`     | HITL 确认回传（F-02-03）                        | ✅    |
| 12  | POST | `/ai/conversations/{id}/rename`             | 重命名对话                                     | ✅    |
| 13  | POST | `/ai/conversations/{id}/delete`             | 删除对话                                      | ✅    |
| 18  | GET  | `/ai/available-tools`                       | 平台工具（按分类）                                 | ✅    |
| 19  | GET  | `/ai/available-skills`                      | workspace 技能列表                            | ✅    |
| 20  | GET  | `/ai/agents/{id}/tools`                     | ~~MCP / Skill 工具列表（已导入副本）~~ **v6.15 已移除** | 🚫   |
| 21  | POST | `/ai/agents/{id}/tools/mcp/save`            | ~~新增 / 更新 MCP~~ **v6.1 已移除**              | 🚫   |
| 22  | POST | `/ai/agents/{id}/tools/mcp/test`            | ~~测试 MCP 连通~~ **v6.1 已移除**                | 🚫   |
| 23  | POST | `/ai/agents/{id}/tools/skill/upload`        | ~~上传 skill 文件夹~~ **v6.1 已移除**             | 🚫   |
| 24  | POST | `/ai/agents/{id}/tools/{tid}/toggle`        | ~~启用 / 禁用工具~~ **v6.15 已移除**               | 🚫   |
| 25  | POST | `/ai/agents/{id}/tools/{tid}/delete`        | ~~删除工具（skill 清目录）~~ **v6.15 已移除**         | 🚫   |
| 26  | POST | `/ai/conversations/{id}/chat/stream`        | SSE 流式对话（F-02-01）                         | ✅    |
| 27  | GET  | `/ai/conversations/{id}/tasks`              | 对话关联任务                                    | ❌    |
| 28  | GET  | `/ai/conversations/{id}/tasks/{run_id}`     | 单个任务详情                                    | ❌    |
| 29  | GET  | `/ai/tasks`                                 | 任务便签看板                                    | ❌    |
| 30  | POST | `/ai/upload-avatar`                         | 上传头像（data URI）                            | ✅    |
| 31  | POST | `/ai/upload-file`                           | 上传并解析文件（F-02-04）                          | ✅    |
| 32  | GET  | `/ai/knowledge/status`                      | 知识库状态                                     | ✅    |
| 33  | GET  | `/ai/knowledge/documents`                   | 可索引文档列表                                   | ✅    |
| 34  | POST | `/ai/knowledge/reindex`                     | 重建索引                                      | ✅    |
| 35  | POST | `/ai/knowledge/documents/add`               | 手动添加文档                                    | ❌    |
| 36  | GET  | `/ai/tools/schemas`                         | 工具定义（供 AgentScope）                        | ❌    |
| 37  | GET  | `/ai/tools/agent-config/{id}`               | 智能体工具 / 技能 / 能力配置                         | ❌    |
| 38  | POST | `/ai/tools/{module}/{action}`               | 工具网关执行                                    | ❌    |
| 39  | GET  | `/ai/toolbox`                               | 共享工具箱列表                                   | ✅    |
| 40  | POST | `/ai/toolbox/create`                        | 新增共享项                                     | ✅    |
| 41  | POST | `/ai/toolbox/{id}/update`                   | 更新共享项                                     | ✅    |
| 42  | POST | `/ai/toolbox/{id}/delete`                   | 删除共享项                                     | ✅    |
| 43  | POST | `/ai/toolbox/upload-skill`                  | 上传共享 skill                                | ✅    |
| 44  | POST | `/ai/agents/{id}/tools/import-from-toolbox` | ~~导入共享项到智能体~~ **v6.15 已移除**               | 🚫   |
| 45  | POST | `/ai/platform-tools/toggle`                 | 平台业务工具全局启停（仅超管，`name` 或 `category` 二选一）   | ✅    |
| 46  | GET  | `/ai/platform-config`                       | 平台唯一智能体工具/知识库配置读取                         | ✅    |
| 47  | POST | `/ai/platform-config/update`                | 更新平台唯一智能体配置（仅超管）                          | ✅    |
| 48  | POST | `/ai/toolbox/{id}/toggle`                   | 启停共享项（直接决定平台唯一智能体是否使用，仅超管）                | ✅    |


> 端点 1~5 / 14~17 已拆分至 [PRD-08-AI助手-01-平台小助手](./PRD-08-AI助手-01-平台小助手.md) §5。端点 6 / 27~29 / 35~38 前端未直接消费（后端保留：一次性 Key 查看、任务历史、工具网关 HTTP 通道、手动加文档）；端点 21~23 于 v6.1 移除；端点 20 / 24 / 25 / 44 于 v6.15 移除（per-agent 工具副本机制下线，MCP/Skill 改为工具箱直接启用/停用）。



### 5.3 SSE 流式对话（端点 26）

**接口地址**：`POST /api/ai/conversations/{id}/chat/stream`

**请求字段**：


| 字段             | 类型     | 必填  | 说明                                    |
| -------------- | ------ | --- | ------------------------------------- |
| `message`      | string | 是*  | 用户文本（有图片时可为空）                         |
| `images`       | array  | 否   | `[{media_type, data(base64)}]`，最多 1 张 |
| `display_text` | string | 否   | 前端展示文本（含附件标记）                         |


**响应**：`text/event-stream`，事件为 AgentScope `reply_stream` 的 `event.model_dump()`，含 `type` 字段（`TEXT_BLOCK_DELTA` / `THINKING_BLOCK_`* / `TOOL_CALL_*` / `TOOL_RESULT_*` / `HINT_BLOCK` / `REQUIRE_USER_CONFIRM` / `REPLY_END` / `EXCEED_MAX_ITERS`）。终端事件附带 `_backend_msg_id`。前端经共享层 `SSEMessageBuilder.ts` 归一化处理 25 种 AgentScope SSE 事件（本表为前端渲染消费的关键子集）；`TOOL_RESULT_*` 具体为 `TOOL_RESULT_START` / `TOOL_RESULT_TEXT_DELTA` / `TOOL_RESULT_DATA_DELTA` / `TOOL_RESULT_END`。

**错误**：403 无权限 / 404 对话不存在 / 400 JSON 或消息非法。

### 5.4 错误码汇总


| 状态码 | 场景                                                        |
| --- | --------------------------------------------------------- |
| 400 | JSON 非法 / 字段校验失败 / 图片格式或超限                                |
| 401 | 未认证（`require_auth`）                                       |
| 403 | 非资源所有者（`check_agent_owner` / `check_conversation_access`） |
| 404 | Agent / 对话 / 工具不存在                                        |
| 409 | 重索引进行中 / HITL 队列满 / 工具箱重复导入                               |


---



## 6. 数据库表单


| 表                   | 表前缀 | 说明                                                          |
| ------------------- | --- | ----------------------------------------------------------- |
| `ai_shared_tools`   | ai_ | 共享工具箱（skill / mcp / extension），`enabled` 直接决定平台唯一智能体是否使用    |
| `ai_platform_tools` | ai_ | 平台业务工具**全局开关**（仅存停用记录 enabled=False，默认全启用）                  |
| `ai_conversations`  | ai_ | 对话（owner / agent / title / status / agent_scope_session_id） |
| `ai_messages`       | ai_ | 消息（content / blocks / reason / tokens / model_name / flow）  |
| `ai_execution_logs` | ai_ | 执行日志（agent / task 可空 / level / message / metadata）          |
| `tr_test_runs`      | tr_ | **跨模块**：任务历史（`ai-task-`* / `case-gen-*` 前缀），主权在 PRD-06      |


---

