# PRD-08 — AI 助手 (AI Assistant)

> 关联模块：`apps/ai_assistant/` · 前端：`frontend/src/modules/ai-assistant/`
> 关联全局：[`需求大纲.md`](./需求大纲.md) §5.8
> 关联上游：[`PRD-02-设备管理`](./PRD-02-设备管理.md) · [`PRD-03-设备检查器`](./PRD-03-设备检查器.md) · [`PRD-04-元素定位`](./PRD-04-元素定位.md) · [`PRD-05-用例管理`](./PRD-05-用例管理.md) · [`PRD-06-执行引擎`](./PRD-06-执行引擎.md) · [`PRD-09-工作流工作台`](./PRD-09-工作流工作台.md)（经 26 个平台 Tool 调用各模块）
> 版本：v6.12 · 状态：评审中 · 日期：2026-08-21

**修订记录**

| 版本 | 日期 | 变更摘要 |
|------|------|----------|
| v6.12 | 2026-08-21 | 代码真相校正：§2.7 工具名 `create_runner_task` 不存在（实为 `run_test`/`get_run_status`/`stop_run`）；§2.2 移除 MCP/Skill 自配置残留（统一走工具箱导入）；§2.7 补 HintCard 提示变体 `sop_card`（Phase1~4）/`task_card`/`prd_case_preview`；§2.9 上传文档格式 13→16（补 log/markdown/yml）；§5.3 SSE 事件补注（SSEMessageBuilder 25 种，校正 TOOL_RESULT_* 变体） |
| v6.11 | 2026-08-20 | 执行引擎状态打通：新增只读工具 `get_run_status`（runner/get_run_status，返回 TestRunRecord 状态/设备/计划用例快照/已完成结果数与汇总/起止时间）；`get_run_results` 信封化（返回 `{run_status, results}`，run 不存在报 400 而非空列表，运行中与无结果可区分）；平台业务工具 25→26 |
| v6.10 | 2026-08-20 | 用例工具可执行性修复：`get_case` 改返回结构化 digest（元信息 + steps 步骤数组 / API config 四模块 / storage rows，修复旧行为只返回标题）；`save_case` 的 UI/Web 步骤写入 `steps_json`（执行器消费 steps_data，修复旧行为落 legacy 文本字段致用例不可执行）并新增**写侧校验**（步骤类型须在 `STEP_TYPE_META` 白名单且与平台匹配、click/wait 类必填 xpath、断言类必填 expected_text、Web 操作必填 selector/url，非法即拒不入库）；schema 新增 directory_id/package_name/enabled/priority 参数；`in_process_tool._format_result` 新增 dict 与单模型实例 JSON 序列化分支（详情类工具不再被 str() 化为标题），并修复模型外键字段懒加载致 `SynchronousOnlyOperation`（关系字段只输出原始外键 id，不在事件循环线程访问相关对象） |
| v6.9 | 2026-08-19 | 新增「工作流」工具分类与 2 个只读工具——`list_page_flows`（workflow/list_page_flows，按标题/doc_id 搜，可按目录过滤，返回 doc_id/标题/目录/节点连线数）与 `get_page_flow`（workflow/get_page_flow，返回页面流语义摘要：节点、页面间跳转 links、每页 navigation_entries（可点击元素与去向，含 XPath）与 elements（页面下元素，source 标注 snapshot/web_snapshot/builtin_pool/unknown）、paths 路径文字描述；digest 由 workflow 模块 `semantics.py` 编译）；平台业务工具 23→25、分类 6→7 |
| v6.8 | 2026-08-19 | 工作台顶栏随子项切换：标题/副标题按 4 个子项（智能体看板/AI工具箱/知识库/评测中心）分别展示 |
| v6.7 | 2026-08-19 | 导航重构：视图 Tab 改为侧边栏「AI 助手」分组子项（智能体看板 / AI工具箱 / 知识库 / 评测中心），各自独立路由（/ai-assistant/agents、/ai-assistant/toolbox、/ai-assistant/knowledge、/ai-assistant/evaluator，/ai-assistant 重定向到 /ai-assistant/agents） |
| v6.6 | 2026-08-19 | PRD/ARCH 分工回退：§4.2/§4.3 移除 build_agent 与 SSE 类级伪代码、§4.1/§2.8 移除进程内实现细节（asyncio.Queue/call_soon_threadsafe 等），改产品口径并指向 ARCH-08 §3.2/§3.3 |
| v6.5 | 2026-08-19 | 承接设备检查器快照化（PRD-03 v1.7）：新增「设备检查器」工具分类与 2 个工具——`capture_page`（inspector/capture，只读，实时抓取 dump/OCR 返回 JSON 并落库快照）与 `save_page_to_elements`（inspector/save_elements，写工具，基于已存快照按 AI 自定义目录/页面名保存到元素定位）；平台业务工具 15→17、分类 5→6；写工具需逐智能体启用（AITool 记录），只读工具进默认兜底 |
| v6.4 | 2026-08-19 | 格式对齐 PRD-03：文头补关联上游 PRD 链接；§5.1 标题校正为「44 行编号 · 41 存活」消除与 v6.1 计数矛盾；§10 views/ 目录描述校正（模块级 views_drf/views_toolbox_drf/views_knowledge_drf/views_upload_drf + views/ 仅 chat_views/hitl_views/tool_gateway） |
| v5.0 | 2026-07-27 | 前端 JS 时代基线（Agent 便签 + 任务看板 + 5 步向导 + 45 项验收） |
| v6.0 | 2026-08-18 | 同步代码真相：AgentScope 由独立服务迁入 Django 进程内（`agent_scope/`）；Tool 28→14 平台工具 + 能力开关（workspace/business/mcp/skills）；前端全面 TS 化（`api/*.ts` + `constants.ts` + `index.logic.ts`）；5 步向导→分区表单；任务看板 UI 移除（任务历史改由 test_runner `TestRunRecord` 支撑）；数据表 6→7（新增 `ai_shared_tools`）；按 PRD-02 十章结构重构 |
| v6.1 | 2026-08-19 | 工具箱集中管理收紧：智能体禁止自上传 skill / 自配置 MCP，一律从 AI 工具箱导入；移除端点 21~23（`mcp/save`、`mcp/test`、`skill/upload`）及前端「MCP 服务器」「Skills」面板；端点总数 44→41 |
| v6.2 | 2026-08-19 | 知识库目录树化：文档按 `dev_docs/` 本地目录折叠展示（知识库 Tab + 导入弹窗）；引用支持目录级（`dir:` 动态展开）与文件级（`doc:`）混选；修复 `doc:` 前缀与检索过滤不匹配问题 |
| v6.3 | 2026-08-19 | 设备管理新增只读工具 `list_devices`（`devices/list_all`）：返回设备管理口径全量设备（在线 + 使用中，含使用人 / 锁定人 / 剩余占用时间，按用户可见性过滤）；平台业务工具 14→15 |

---

## 1. 功能定位

AI 助手是平台的**智能对话中枢**，用户通过自然语言对话驱动全流程测试——无需逐个操作设备管理、元素定位、用例管理、执行引擎等模块。AgentScope ReAct 推理引擎作为 Django 进程内模块运行，通过 26 个平台业务 Tool 编排跨模块能力。

**核心职责**：

- **智能体管理**：创建 / 编辑 / 删除 AI 智能体，配置模型提供商、API Key、系统提示词、参数与能力开关
- **流式对话**：SSE 逐 token 流式回复，展示思考过程、工具调用、HITL 确认；支持文件 / 图片上传
- **自然语言操控**：通过 26 个平台 Tool 完成设备操控、页面抓取、元素检索、用例生成、测试执行、页面流查阅、知识库检索
- **知识库管理**：ChromaDB 向量库状态、文档列表、重建索引；按智能体过滤可用文档
- **评测中心**：自然语言用例生成与执行
- **AI 工具箱**：集中管理共享 skill / MCP / 扩展，跨智能体复用；**智能体不允许自行上传 skill 或配置 MCP，必须从 AI 工具箱导入**（见 §2.12）

AI 助手是**管理模块（有写操作）**：所有写操作走 `api.py` → ORM，跨模块写走目标 App 的 `api.py`；AI 引擎不直连设备、不直写数据库，一切通过 Tool 调用 Django。

---

## 2. 功能详细规格

### 2.1 智能体看板（F-01-01）

主工作台「智能体看板」Tab，以便签卡片网格展示全部智能体。每张卡片显示名称、模型、健康状态（绿点 = 已连通）。点击卡片进入对话；点击编辑进入配置页。

**健康检查**：`GET /ai/agents/health` 批量检测全部 active 智能体连通性，30 分钟轮询一次（`HEALTH_CHECK_INTERVAL_MS`）。

**组件**：`index.vue` + `AgentStickyNote.vue` + `useAgentBoard`（`index.logic.ts`）。

**边界状态**：

| 场景 | 行为 |
|------|------|
| 无智能体 | 空态「还没有智能体」，引导「+ 新建智能体」 |
| 健康检查失败（Key 失效/网络） | 卡片状态点变红，不阻断列表 |
| 数据加载中 | 便签加载动画（`WbLoader`） |

**验收标准**：

- 列表按创建时间展示全部智能体，卡片含名称 / 模型 / 健康状态点
- 健康检查 30 分钟轮询，状态点与后端 `is_connected` 一致
- 无智能体时展示空态引导

### 2.2 智能体创建 / 编辑（F-01-02）

配置页采用**分区表单**（自上而下六个区块，非分步向导），新建与编辑共用 `AgentDetail.vue`。

| 区块 | 字段 | 说明 |
|------|------|------|
| 基本信息 | 名称 · 头像 · 标签 · 描述 | 名称必填；头像 emoji 或上传图片（存 data URI） |
| 模型配置 | 提供商 · 模型名 · API Key · base_url · temperature · max_tokens | 6 提供商；「检测模型」从 API 拉取可用模型列表 |
| 系统提示词 | system_prompt | 新建默认空（纯对话模型） |
| 工具 / 技能 | 平台工具勾选 · workspace 技能开关 · 知识库文档 · 从 AI 工具箱选取（MCP / Skill） | 见 F-01-05 能力开关；MCP / Skill 不自配置，统一走工具箱导入（§2.12） |
| 高级配置 | formatter · max_iters · 记忆模式 · 上下文压缩 · TTS · generate_kwargs | AgentScope 2.0 参数 |
| 保存 | 底部操作栏 | 新建含工具配置，编辑 diff 同步 |

**模型提供商**（`provider_registry.py`）：

| 提供商 | base_url（默认） |
|------|------|
| dashscope | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| openai | `https://api.openai.com/v1` |
| anthropic | `https://api.anthropic.com/v1` |
| deepseek | `https://api.deepseek.com/v1` |
| gemini | `https://generativelanguage.googleapis.com/v1beta/openai` |
| custom | 用户自定义（OpenAI 兼容） |

**组件**：`AgentDetail.vue` + `AgentBasicInfo` / `AgentModelConfig` / `AgentPromptEditor` / `AgentToolsPanel` / `AgentAdvancedConfig` / `AgentFormFooter` + `useAgentTools`。

**边界状态**：

| 场景 | 行为 |
|------|------|
| 名称空 | 表单提示「Agent 名称不能为空」 |
| temperature 越界 | 提示「温度必须在 0-2 之间」 |
| max_tokens 越界 | 提示「max_tokens 必须在 1-128000 之间」 |
| base_url 指向本机 / 非白名单主机 | 提示「base_url 主机不在 X 提供商白名单内」 |
| generate_kwargs 非法 JSON | 提示「generate_kwargs 必须是合法的 JSON 字符串」 |
| API Key 未填（检测模型时） | 提示「请先填写 API Key」 |

**验收标准**：

- 6 个提供商均可选，切换时自动带出默认模型与 formatter
- 「检测模型」成功后返回模型列表并合并去重内置模型
- 保存后跳转智能体看板，卡片反映最新配置

### 2.3 API Key 安全（F-01-03）

API Key 全程加密存储（Fernet），列表 / 详情只返回脱敏值，完整 Key 仅一次性查看。

| 规则 | 行为 |
|------|------|
| 写入 | 明文 Key 经 `encrypt_key()` 加密后落库，DB 值不以 `sk-` 开头 |
| 展示 | 列表不返回 Key；详情返回 `mask_key()` 脱敏值（前 3 + `***` + 后 4） |
| 一次性查看 | `POST /agents/{id}/reveal-key` 仅首次返回明文，之后返回脱敏值 + `revealed: false` |
| 更新 | 前端回传 `***` 掩码视为未变更，跳过更新保留原值；Key 变更后 `key_revealed` 复位 |

**验收标准**：

- `GET /ai/agents` 响应无 `api_key` 字段
- `GET /ai/agents/{id}` 的 `api_key` 为脱敏值
- reveal-key 首次返回明文，二次返回脱敏；Key 变更后可再次查看一次
- 解密失败返回空字符串而非崩溃，不 fallback 原文

### 2.4 模型连接测试与检测（F-01-04）

- **连接测试**（`POST /agents/{id}/test`）：调 `/models` 或 `/chat/completions` 验证连通性，回写 `is_connected` + `available_models` + `last_checked_at`
- **模型检测**（`POST /models/detect`）：用 provider + api_key + base_url 拉取可用模型列表，供配置页合并去重

**边界状态**：

| 场景 | 行为 |
|------|------|
| API Key 无效 | `connected: false`，message 返回 HTTP 状态与错误摘要 |
| 网络不可达 | `connected: false`，message 返回连接错误 |

**验收标准**：

- 连接成功返回 `connected: true` + 模型列表；失败返回 `connected: false` + message
- 检测到的模型与内置模型合并去重，当前选中模型始终在列表中

### 2.5 能力开关（F-01-05）

智能体通过四组能力开关决定可用的工具集，构建时由 `agent_factory` 按开关组装 Toolkit：

| 开关字段 | 默认 | 启用后注入的工具 |
|------|:--:|------|
| `enable_workspace_tools` | false | 6 个 AgentScope 内置文件工具（Bash / Edit / Glob / Grep / Read / Write），受 `skills_config` 逐工具开关 |
| `enable_business_tools` | false | 26 个平台业务工具（见 §4.1），受 `AITool(tool_type=platform)` 逐工具开关 |
| `enable_mcp_tools` | false | 从 AI 工具箱导入的 MCP 客户端（`AITool(tool_type=mcp)`） |
| `enable_skills` | false | 从 AI 工具箱导入的 skill 目录（`AITool(tool_type=skill)`） |
| `enable_knowledge_base` + `knowledge_sources` | false / {} | 知识库文档过滤：`doc:相对路径` 按文件引用；`dir:相对目录` 按目录动态引用（检索时展开为目录下当前全部文件） |

新建智能体默认**纯对话模型**（全部开关 false，无默认系统提示词）。

**验收标准**：

- 未启用 business_tools 时，`/api/tools/agent-config` 返回 `enabled_tools: []`
- 启用 workspace_tools 但 `skills_config` 关闭 Bash 时，构建出的 Toolkit 不含 Bash
- `knowledge_sources` 只导入的文档 / 目录参与 `search_knowledge_base` 检索；目录引用（`dir:`）动态展开，新增 / 删除文件自动生效

### 2.6 SSE 流式对话（F-02-01）

对话页发起 `POST /conversations/{id}/chat/stream`，AgentScope 在 Django 进程内运行，`reply_stream` 事件经 SSE 逐 token 流式返回。单请求完成「构建 Agent → 恢复上下文 → 流式回复 → 持久化」。

**流式生命期**：构建 Agent（进程内）→ 保存用户消息 → 恢复历史上下文 → `reply_stream` 消费事件 → SSE 推送 → 终端事件时后端持久化 assistant 消息。

**模型状态**（`MODEL_STATUS_MAP`）：思考中 / 调用模型 / 调用工具 / 输出中 / 已完成。

**组件**：`ChatView.vue` + `useSSE` + `api/sse.ts`（`streamChat` 用原生 fetch 读 ReadableStream，401 自动刷新重试一次）。

**边界状态**：

| 场景 | 行为 |
|------|------|
| 消息为空且无附件 | 400「消息不能为空」 |
| 无权限访问对话 | 403 |
| 对话不存在 | 404 |
| 2 分钟无事件 | SSE 发送心跳注释 `: heartbeat` |
| 客户端断开 / 换对话 | 取消旧 agent Task（`CancelledError`），保留已生成内容，后台续跑 |
| 模型服务不可用 | 顶部降级横幅「AI 模型服务暂不可用…」 |
| 同一对话重复请求 | 取消上一 stale Task，保留最新 |

**验收标准**：

- 回复逐 token 渲染，非整段一次性
- 切换 / 关闭对话后已生成内容不丢失，历史消息从后端加载
- 401 时自动刷新 token 并重试一次
- 终端事件（REPLY_END / ExceedMaxIters）后端持久化 assistant 消息

### 2.7 消息渲染（F-02-02）

每条消息经 `MessageBubble` 渲染，按内容块类型区分：

| 内容块 | 渲染 | 说明 |
|------|------|------|
| 文本 | Markdown + Mermaid 图表 | `useMarkdown` 渲染 |
| 思考块 | `ThinkingBlock`（默认折叠） | ReAct 推理过程，多轮可折叠 |
| 工具调用 | `ToolCallCard`（折叠 / 展开） | 工具名 + 参数 + 结果 |
| 提示块 | `HintCard` | SOP 阶段卡片 / 任务卡片（内嵌进度）/ PRD 用例预览卡片 |
| 数据块 | 图片气泡 | 用户上传图片 |

**任务卡片**（内嵌于对话流）：`run_test` / `get_run_status` / `stop_run` 工具调用时，`ChatView` 解析输出维护内嵌进度卡片（PENDING → RUNNING → COMPLETED / FAILED / STOPPED）。

**组件**：`MessageBubble.vue` + `ThinkingBlock` / `ToolCallCard` / `HintCard` + `useMarkdown` / `useMessageStore`。

**HintCard 提示变体**（`hint.type` 区分，见 `HintCard.vue`）：

| type | 渲染 | 说明 |
|------|------|------|
| `sop_card` | SOP 工作流卡片 | 阶段徽标 Phase1~4（`phase-1`~`phase-4`）、需求、用例设计列表、下一步提示 |
| `task_card` | 任务卡片 | 状态徽标（PENDING/RUNNING/COMPLETED/FAILED/STOPPED）、run_id、标题、设备、用例数 |
| `prd_case_preview` | PRD 用例预览卡片 | 生成用例总数 / P0 必测 / P1 应测统计 + 「导入到用例库」按钮 |
| 其他 / 字符串 | 通用提示块（`hint-block`） | 兜底渲染 |

**验收标准**：

- Markdown 与 Mermaid 正常渲染；思考块默认折叠可展开
- 工具调用卡片折叠 / 展开切换正常，含参数与结果
- 任务卡片随工具调用更新进度与终态

### 2.8 HITL 工具确认（F-02-03）

Agent 执行写操作工具前，若需要用户确认，流中返回 `RequireUserConfirmEvent`，前端弹出确认对话框；用户 ALLOW / DENY / 全部允许 / 全部拒绝后，结果经 `POST /conversations/{id}/confirm-result` 回传正在运行的 Agent。

**实现**：进程内会话注册表接收确认结果并回传给运行中的 Agent（实现结构见 ARCH-08 §3.3）。

**组件**：`ConfirmDialog.vue` + `useToolConfirm`。

**边界状态**：

| 场景 | 行为 |
|------|------|
| 确认超时（2 分钟） | 记录 warning，终止本轮回复 |
| 无活跃 agent session | 400「No active agent session…」 |
| 确认队列已满 | 409「Agent is busy」 |

**验收标准**：

- 确认弹窗展示工具名与参数，支持单个 / 全部允许 / 拒绝
- ALLOW 后 Agent 继续执行，DENY 后跳过该工具
- 确认结果经 `AIExecutionLog` 记录审计

### 2.9 文件 / 图片上传（F-02-04）

对话输入栏支持上传文档与图片：

| 类型 | 支持格式 | 大小上限 | 处理 |
|------|------|:--:|------|
| 文档 | txt / log / md / markdown / json / xml / csv / py / js / html / css / yaml / yml / docx / xlsx / pdf | 20MB | 解析为文本注入消息（超 5 万字符截断） |
| 图片 | png / jpg / jpeg / webp / gif | 5MB | base64 编码，随消息以 DataBlock 发送 |

**组件**：`ChatInput.vue` + `api/agents.ts`（`uploadFile`）。头像上传走 `upload-avatar`（data URI 存 DB）。

**边界状态**：

| 场景 | 行为 |
|------|------|
| 不支持的文件类型 | 400「Unsupported file type」 |
| 文件超限 | 400「File too large」 |
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

| 场景 | 行为 |
|------|------|
| 索引重建进行中 | 409「索引重建已在进行中」 |
| ChromaDB 不可用 | 状态返回 doc_count 0，不崩溃 |
| 知识库为空 | 检索跳过，返回空列表 |
| 目录键对应目录已删除 | 展开为空，检索跳过该键 |
| 历史 `doc:` 键 | 完全兼容（剥前缀比对 source） |

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

「AI 工具箱」Tab **集中管理**跨智能体复用的共享项（skill / MCP / 扩展）。

**集中管理规则（硬约束）**：

- 智能体**不允许自行上传 skill、不允许自行配置 MCP**——智能体配置页不提供任何自上传 / 自配置入口（v6.1 起移除「MCP 服务器」「Skills」面板及对应端点）
- 智能体只能通过**「从 AI 工具箱选取」**导入共享项，导入生成 per-agent `AITool` 副本
- 工具箱是 skill 上传 / MCP 配置的**唯一入口**

| 项类型 | 说明 |
|------|:--:|
| skill | 上传 skill 文件夹，存 `data/shared_skills/{id}/` |
| mcp | 共享 MCP 配置 |
| extension | 扩展配置 |

**导入**：`POST /agents/{id}/tools/import-from-toolbox` 生成 per-agent `AITool` 副本（skill 复制文件目录）。重复导入同名项返回 409。

**组件**：`ToolboxPanel.vue` + `api/toolbox.ts`；智能体配置页仅保留「从 AI 工具箱选取」导入面板。

**验收标准**：

- 工具箱列表 / 创建 / 更新 / 删除 / 上传 skill 正常
- 导入后智能体工具列表出现副本；同名重复导入 409
- 删除 skill 类型项时清理上传目录
- 智能体配置页**不存在**自上传 skill / 自配置 MCP 的 UI 入口
- 智能体级 `mcp/save`、`mcp/test`、`skill/upload` 端点已移除（404）

---

## 3. 布局与视觉设计

> 全部颜色 / 字号引用 Doodle Craft 主题令牌（[`frontend/AGENTS.md` §2](../../frontend/AGENTS.md)）。

### 3.1 主工作台布局

```
┌─────────────────────────────────────────────┐
│ 侧边栏：「AI 助手」分组（可展开，4 子项）         │
│  🤖智能体看板 | 🧰AI工具箱 | 📚知识库 | 📊评测中心│
├─────────────────────────────────────────────┤
│ WorkbenchHeader（标题 + 「+ 新建智能体」）        │
├─────────────────────────────────────────────┤
│ 智能体看板：便签卡片网格（AgentStickyNote × N）    │
└─────────────────────────────────────────────┘
```

- 页面底色：米白纸纹叠加点阵底纹
- 智能体卡片为便签风格（微旋转排列，hover 归正放大），健康状态点绿 / 红

### 3.2 配置页布局（分区表单）

```
┌─ 基本信息（名称/头像/标签/描述）─────┐
├─ 模型配置（提供商/模型/Key/温度）────┤
├─ 系统提示词 ───────────────────────┤
├─ 工具/技能（平台工具/workspace/知识库/从 AI 工具箱选取）┤
├─ 高级配置（记忆/压缩/TTS）─────────┤
└─ 底部操作栏（保存/取消）────────────┘
```

### 3.3 对话页布局

```
┌────────────────────────────────────────────┐
│ 左侧：会话列表（新建/重命名/删除）               │
├────────────────────────────────────────────┤
│ 右侧：消息流（MessageBubble 流式渲染）          │
│       顶部状态徽标（模型状态 + 连接模式 + 消息数）  │
│       底部：输入栏（附件/图片 + 发送/停止）        │
└────────────────────────────────────────────┘
```

---

## 4. 后端功能逻辑

### 4.1 平台业务工具（26 个）

`tool_registry.py` 的 `TOOL_SCHEMAS` 是平台工具的**单一真相源**，按 7 分类：

| 分类 | 工具 | 只读 |
|------|------|:--:|
| 设备管理 | `list_devices` · `get_online_devices` · `acquire_device` · `release_device` | 2 读 2 写 |
| 设备检查器 | `capture_page` · `save_page_to_elements` | 1 读 1 写 |
| 元素定位 | `search_elements` · `list_pages` · `fetch_page_elements` · `list_web_groups` · `search_web_elements` · `list_api_groups` · `search_api_endpoints` | 7 读 |
| 用例管理 | `save_case`（UI/Storage/Web） · `save_api_test_case` · `get_case` · `debug_case` · `list_case_directories` · `search_cases` | 4 读 2 写 |
| 测试执行 | `run_test` · `get_run_results` · `get_run_status` · `stop_run` | 2 读 2 写 |
| 工作流 | `list_page_flows` · `get_page_flow` | 2 读 |
| 知识库 | `search_knowledge_base` | 1 读 |

> 设备检查器工具（v6.5）：`capture_page`（`inspector/capture`，参数 serial + method，实时抓取 dump/OCR 返回 JSON 并落库快照，复用检查器 capture 链路，见 PRD-03 v1.7）；`save_page_to_elements`（`inspector/save_elements`，参数 snapshot_id + folder_path + page_label + element 筛选，经 element-locator api 写入，见 PRD-04 v7.2）。写工具需逐智能体启用（AITool 记录），只读工具进无配置默认兜底。

> 元素定位扩展：新增 4 个只读查询工具覆盖 Web 元素与 API 接口资产 —— `list_web_groups`/`search_web_elements`（`el_web_groups`/`el_web_elements`，搜名称/定位表达式/URL/描述/标签）、`list_api_groups`/`search_api_endpoints`（`el_api_groups`/`el_api_endpoints`，搜名称/URL/描述/标签，可按 method 过滤）；同批修复 `list_pages` 按不存在的 `updated_at` 排序的崩溃（改 `-created_at`）。

> 用例管理扩展：新增 2 个只读查询工具补上「浏览/搜索」盲区 —— `list_case_directories`（`cases/list_directories`，两级目录树，可按 case_type 过滤）与 `search_cases`（`cases/search`，跨 UI/Storage/API/Web 四类型按标题/用例ID 模糊搜，可叠加 case_type/directory_id 过滤，返回精简字段；完整详情仍走 `get_case`），形成「目录 → 搜索 → 详情」查询链。

> 用例工具可执行性修复（v6.10）：`get_case` 返回结构化 digest（case_id/title/case_type/目录/优先级/enabled/package_name + steps 步骤数组（UI/Web）或 config 四模块（API）或 rows（storage）），由 case-manager `api_ai.get_case_digest` 产出；`save_case` 经 `api_ai.save_ai_definition` 落库——UI 步骤写 `steps_json`（执行器消费 steps_data）、Web 写 `steps_json` 字符串，并做**写侧校验**（`api_ai.validate_steps`：类型 ∈ `STEP_TYPE_META` 且 target 与 case_type 匹配、click/wait 类必填 xpath、断言类必填 expected_text、Web 操作必填 selector/url，非法即拒绝不落库）；schema 新增 directory_id/package_name/enabled/priority。`debug_case` 就绪检查与 `search_cases` 总数返回仍为已知缺口，未在本版修复。

> 工作流扩展（v6.9）：新增 2 个只读查询工具连接页面流 —— `list_page_flows`（`workflow/list_page_flows`，按标题/doc_id 关键词搜索，可按 directory_id 过滤，返回 doc_id/标题/目录/节点连线数/更新时间）与 `get_page_flow`（`workflow/get_page_flow`，参数 doc_id，返回页面流语义摘要：nodes（起点/页面/弹窗/API/终点及页面归属）、links（跳转关系，含节点名与端口名）、每页 navigation_entries（可点击元素与去向，含 XPath）与 elements（页面下元素，source 标注 snapshot/web_snapshot/builtin_pool/unknown）、paths（起点到终点文字路径）、parse_warnings（悬空连线等异常不静默））。语义摘要由 workflow 模块 `semantics.py` 纯函数编译，AI 只读消费、不写图（见 PRD-09）。

> 测试执行扩展（v6.11）：新增只读工具 `get_run_status`（`runner/get_run_status`，参数 run_id，返回执行运行状态摘要：status（透传 DB 值，可能大小写混存）/device_serial/selected_cases 计划用例快照/result_count 已完成结果条数/summary 汇总/起止时间——运行中 result_count 恒 0，因 TestResult 在整轮结束后批量落库）；`get_run_results` 信封化（返回 `{run_status, results}`，run 不存在报 400 而非空列表）。数据出口为 `test_runner.api.get_run_status` / `get_run_results`。

工具执行：进程内直调各模块 handler，**不走 HTTP**；写操作工具校验调用者身份（user_id 非空）。实现结构见 ARCH-08 §3.2。

### 4.2 Agent 构建口径（进程内）

每次发起对话时按智能体配置**进程内构建 Agent**：

- 解密 API Key → 选择模型（dashscope 用 DashScope 通道，其余 OpenAI 兼容）
- 按四组能力开关组装工具集（workspace + business + mcp + skills，见 F-01-05）
- 应用参数配置（max_iters / 上下文压缩等 AgentScope 2.0 参数）
- system_prompt 直接取智能体配置（**无默认提示词**，新建智能体即纯对话模型）

### 4.3 SSE 流式对话口径

单次请求完成「鉴权 → 保存用户消息 → 恢复历史上下文 → 流式回复 → 持久化 assistant 消息」全链路：

- 后台任务消费 Agent 的流式事件并逐条转为 SSE 推送
- 遇 HITL 确认事件暂停，等待用户确认结果回传后续跑
- 终端事件（REPLY_END / ExceedMaxIters）时后端持久化 assistant 消息
- 客户端断开 / 换对话时取消旧任务，保留已生成内容

> 事件循环、队列与跨线程投递的实现结构见 ARCH-08 §3.3。

### 4.4 知识库（ChromaDB）

- 存储：`data/chromadb`，collection `project_knowledge`，`rag_service.py` 是唯一所有者
- 文档：`dev_docs/*.md`（内容截断 4000 字符）+ 生成的步骤类型参考
- 检索：`search(query, top_k=5, sources=[...])`；`sources` 过滤（单值时用 where 过滤，多值时 post-filter）；`dir:` 键检索前动态展开为目录下当前全部文件 source，`doc:` 键剥前缀比对
- 缓存：文档列表按文件 mtime + 60s TTL 缓存

### 4.5 任务历史口径

任务看板 UI 已移除，任务历史由 **test_runner 的 `TestRunRecord`**（`tr_test_runs`）支撑，通过 `run_id` 前缀区分：

| 前缀 | 类型 | 关联 |
|------|------|------|
| `ai-task-` | 执行任务 | 经 `TestSOP` 关联对话 |
| `case-gen-` | 用例生成任务 | 不关联具体对话（对话内无条件包含） |

`ai_tasks` 表（`AITask`）当前无视图使用，仅 admin 注册与 `AIExecutionLog` 可空外键。

---

## 5. API 接口功能

鉴权：除 `/api/tools/*`（工具网关，内部服务）外全部端点需要 JWT Bearer。响应统一 `{status, data}` / `{status, message}`，JSON 字段 snake_case。

### 5.1 端点总览（44 行编号 · 41 个存活）

| # | 方法 | 端点 | 功能 | 前端消费 |
|---|------|------|------|:--:|
| 1 | GET | `/ai/agents` | 智能体列表 | ✅ |
| 2 | POST | `/ai/agents/create` | 创建智能体（F-01-02） | ✅ |
| 3 | GET | `/ai/agents/{id}` | 智能体详情（含脱敏 Key） | ✅ |
| 4 | POST | `/ai/agents/{id}/update` | 更新智能体 | ✅ |
| 5 | POST | `/ai/agents/{id}/delete` | 删除智能体 | ✅ |
| 6 | POST | `/ai/agents/{id}/reveal-key` | 一次性查看完整 Key（F-01-03） | ❌ |
| 7 | GET | `/ai/agents/{id}/conversations` | 智能体对话列表 | ✅ |
| 8 | POST | `/ai/agents/{id}/conversations/create` | 新建对话 | ✅ |
| 9 | GET | `/ai/conversations/{id}/messages` | 消息列表 | ✅ |
| 10 | POST | `/ai/conversations/{id}/save-message` | 保存消息 | ✅ |
| 11 | POST | `/ai/conversations/{id}/confirm-result` | HITL 确认回传（F-02-03） | ✅ |
| 12 | POST | `/ai/conversations/{id}/rename` | 重命名对话 | ✅ |
| 13 | POST | `/ai/conversations/{id}/delete` | 删除对话 | ✅ |
| 14 | POST | `/ai/models/detect` | 检测可用模型（F-01-04） | ✅ |
| 15 | POST | `/ai/agents/{id}/test` | 连接测试（F-01-04） | ✅ |
| 16 | GET | `/ai/agents/{id}/models` | 缓存的可用模型 | ❌ |
| 17 | GET | `/ai/agents/health` | 全部智能体健康检查 | ✅ |
| 18 | GET | `/ai/available-tools` | 平台工具（按分类） | ✅ |
| 19 | GET | `/ai/available-skills` | workspace 技能列表 | ✅ |
| 20 | GET | `/ai/agents/{id}/tools` | MCP / Skill 工具列表（已导入副本） | ✅ |
| 21 | POST | `/ai/agents/{id}/tools/mcp/save` | ~~新增 / 更新 MCP~~ **v6.1 已移除** | 🚫 |
| 22 | POST | `/ai/agents/{id}/tools/mcp/test` | ~~测试 MCP 连通~~ **v6.1 已移除** | 🚫 |
| 23 | POST | `/ai/agents/{id}/tools/skill/upload` | ~~上传 skill 文件夹~~ **v6.1 已移除** | 🚫 |
| 24 | POST | `/ai/agents/{id}/tools/{tid}/toggle` | 启用 / 禁用工具 | ✅ |
| 25 | POST | `/ai/agents/{id}/tools/{tid}/delete` | 删除工具（skill 清目录） | ✅ |
| 26 | POST | `/ai/conversations/{id}/chat/stream` | SSE 流式对话（F-02-01） | ✅ |
| 27 | GET | `/ai/conversations/{id}/tasks` | 对话关联任务 | ❌ |
| 28 | GET | `/ai/conversations/{id}/tasks/{run_id}` | 单个任务详情 | ❌ |
| 29 | GET | `/ai/tasks` | 任务便签看板 | ❌ |
| 30 | POST | `/ai/upload-avatar` | 上传头像（data URI） | ✅ |
| 31 | POST | `/ai/upload-file` | 上传并解析文件（F-02-04） | ✅ |
| 32 | GET | `/ai/knowledge/status` | 知识库状态 | ✅ |
| 33 | GET | `/ai/knowledge/documents` | 可索引文档列表 | ✅ |
| 34 | POST | `/ai/knowledge/reindex` | 重建索引 | ✅ |
| 35 | POST | `/ai/knowledge/documents/add` | 手动添加文档 | ❌ |
| 36 | GET | `/ai/tools/schemas` | 工具定义（供 AgentScope） | ❌ |
| 37 | GET | `/ai/tools/agent-config/{id}` | 智能体工具 / 技能 / 能力配置 | ❌ |
| 38 | POST | `/ai/tools/{module}/{action}` | 工具网关执行 | ❌ |
| 39 | GET | `/ai/toolbox` | 共享工具箱列表 | ✅ |
| 40 | POST | `/ai/toolbox/create` | 新增共享项 | ✅ |
| 41 | POST | `/ai/toolbox/{id}/update` | 更新共享项 | ✅ |
| 42 | POST | `/ai/toolbox/{id}/delete` | 删除共享项 | ✅ |
| 43 | POST | `/ai/toolbox/upload-skill` | 上传共享 skill | ✅ |
| 44 | POST | `/ai/agents/{id}/tools/import-from-toolbox` | 导入共享项到智能体 | ✅ |

> 端点 6 / 16 / 27~29 / 35~38 前端未直接消费（后端保留：一次性 Key 查看、任务历史、工具网关 HTTP 通道、手动加文档）；端点 21~23 于 v6.1 移除（智能体禁止自配置 MCP / 自上传 skill，统一走工具箱导入）。

### 5.2 智能体详情（端点 3）

**接口地址**：`GET /api/ai/agents/{id}`

**响应 `agent` 字段**（核心）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` / `name` / `avatar` / `tags` / `description` | — | 基本信息 |
| `model_provider` / `model_name` / `base_url` | string | 模型配置 |
| `api_key` | string | **脱敏值**（`mask_key`） |
| `system_prompt` | string | 系统提示词 |
| `temperature` / `max_tokens` | number | 采样参数 |
| `formatter` / `max_iters` / `parallel_tool_calls` / `print_hint_msg` | — | AgentScope 参数 |
| `memory_mode` / `long_term_memory_mode` / `enable_meta_tool` / `enable_rewrite_query` | — | 记忆 / 元工具 |
| `enable_knowledge_base` / `enable_workspace_tools` / `enable_business_tools` / `enable_mcp_tools` / `enable_skills` | boolean | 能力开关 |
| `generate_kwargs` | string | JSON 字符串 |
| `skills_config` / `knowledge_sources` | object | 逐工具 / 逐文档开关 |
| `compression_*` / `tts_enabled` | — | 压缩 / TTS |
| `status` | string | active 等 |
| `is_connected` / `last_checked_at` / `available_models` | — | 健康状态 |
| `tools[]` | array | 每项含 `id/name/tool_type/config_json/enabled` |

### 5.3 SSE 流式对话（端点 26）

**接口地址**：`POST /api/ai/conversations/{id}/chat/stream`

**请求字段**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `message` | string | 是* | 用户文本（有图片时可为空） |
| `images` | array | 否 | `[{media_type, data(base64)}]`，最多 1 张 |
| `display_text` | string | 否 | 前端展示文本（含附件标记） |

**响应**：`text/event-stream`，事件为 AgentScope `reply_stream` 的 `event.model_dump()`，含 `type` 字段（`TEXT_BLOCK_DELTA` / `THINKING_BLOCK_*` / `TOOL_CALL_*` / `TOOL_RESULT_*` / `HINT_BLOCK` / `REQUIRE_USER_CONFIRM` / `REPLY_END` / `EXCEED_MAX_ITERS`）。终端事件附带 `_backend_msg_id`。前端经共享层 `SSEMessageBuilder.ts` 归一化处理 25 种 AgentScope SSE 事件（本表为前端渲染消费的关键子集）；`TOOL_RESULT_*` 具体为 `TOOL_RESULT_START` / `TOOL_RESULT_TEXT_DELTA` / `TOOL_RESULT_DATA_DELTA` / `TOOL_RESULT_END`。

**错误**：403 无权限 / 404 对话不存在 / 400 JSON 或消息非法。

### 5.4 错误码汇总

| 状态码 | 场景 |
|:--:|------|
| 400 | JSON 非法 / 字段校验失败 / 图片格式或超限 |
| 401 | 未认证（`require_auth`） |
| 403 | 非资源所有者（`check_agent_owner` / `check_conversation_access`） |
| 404 | Agent / 对话 / 工具不存在 |
| 409 | 重索引进行中 / HITL 队列满 / 工具箱重复导入 |

### 5.5 契约变更

| 版本 | 变更 |
|------|------|
| v5.0 | 端点 37→…（补齐 knowledge/health/tasks） |
| v6.0 | 端点校正为 44（补齐 toolbox/available-tools/available-skills/tools 网关）；移除 register-scope / create-scope-session / send 阻塞兜底 / avatars 文件端点；`GET /models/detect` 改为 POST（检测）+ `GET /agents/{id}/models`（缓存）；头像改 data URI 存 DB |

---

## 6. 数据来源表

| 表 | 表前缀 | 说明 |
|------|:--:|------|
| `ai_agents` | ai_ | 智能体配置（模型 / 参数 / 能力开关 / 健康 / 凭据缓存 / Key 揭示） |
| `ai_tools` | ai_ | 每智能体工具配置（mcp / skill / platform），`tool_type` 区分 |
| `ai_shared_tools` | ai_ | 共享工具箱（skill / mcp / extension） |
| `ai_conversations` | ai_ | 对话（owner / agent / title / status / agent_scope_session_id） |
| `ai_messages` | ai_ | 消息（content / blocks / reason / tokens / model_name / flow） |
| `ai_tasks` | ai_ | 智能体任务（**当前无视图使用**） |
| `ai_execution_logs` | ai_ | 执行日志（agent / task 可空 / level / message / metadata） |
| `tr_test_runs` | tr_ | **跨模块**：任务历史（`ai-task-*` / `case-gen-*` 前缀），主权在 PRD-06 |

---

## 7. 非功能需求

| 类别 | 指标 | 目标值 |
|------|------|:--:|
| 性能 | SSE 首 token | 心跳 2 分钟无事件触发；流式逐 token 推送 |
| 可靠性 | SSE 断开恢复 | 切换 / 关闭保留已生成内容，后台续跑 |
| 并发 | 同对话重复请求 | 取消 stale Task，保留最新 |
| 安全 | API Key | 加密存储 + 脱敏 + 一次性查看；base_url 白名单防 SSRF |
| 数据隔离 | 所有权 | Agent / 对话列表按 `owner_id` 过滤 |
| 兼容性 | 模型提供商 | 6 家（dashscope/openai/anthropic/deepseek/gemini/custom） |

---

## 8. 非目标（Non-goals）

| 不做的功能 | 原因 |
|------|------|
| AI 直连设备 / 直写数据库 | 一切通过 Tool 调 Django，架构红线 |
| Agent Team（Leader + Worker 多智能体编排） | 当前单 Agent 进程内构建，无多智能体派发 |
| 独立任务看板 UI（TaskStickyNote 网格） | 已移除，任务进度内嵌对话流 HintCard |
| 长期记忆 / 元工具 / TTS 深度能力 | 字段已建模，能力未产品化 |
| 图片多张上传 | 每次仅支持 1 张（后端校验） |

---

## 9. 关键约束速查

| 编号 | 约束 | 实施位置 |
|------|------|------|
| C-01 | 写操作收敛：View / Tool → api.py → ORM；跨模块写走目标 api.py | `api.py` |
| C-02 | 平台工具单一真相源 | `agent_scope/tool_registry.py` `TOOL_SCHEMAS` |
| C-03 | AgentScope 进程内直连，禁止直连 DB / 设备 | `agent_scope/` |
| C-04 | API Key 加密存储 + 脱敏 + 一次性查看 | `api.py` `encrypt_key/mask_key` + `reveal-key` |
| C-05 | base_url 白名单校验（禁本机 / 非白名单主机） | `provider_registry.py` |
| C-06 | 知识库 ChromaDB 由 `rag_service.py` 唯一拥有 | `rag_service.py` |
| C-07 | 响应 `{status, data}` / `{status, message}`，snake_case | 全部端点 |
| C-08 | 所有权隔离：Agent / 对话按 `owner_id` 过滤 | `permissions.py` |

---

## 10. 相关文件索引

| 层 | 文件 | 说明 |
|------|------|------|
| 前端 | `frontend/src/modules/ai-assistant/index.vue` | 主工作台（4 Tab） |
| 前端 | `frontend/src/modules/ai-assistant/index.logic.ts` | 编排器 `useAgentBoard` |
| 前端 | `frontend/src/modules/ai-assistant/AgentDetail.vue` | 智能体配置（分区表单） |
| 前端 | `frontend/src/modules/ai-assistant/ChatView.vue` | 对话页 |
| 前端 | `frontend/src/modules/ai-assistant/EvaluatorTab.vue` | 评测中心 |
| 前端 | `frontend/src/modules/ai-assistant/KnowledgeBase.vue` | 知识库管理 |
| 前端 | `frontend/src/modules/ai-assistant/api/*.ts` | 数据层（agents / conversations / sse / toolbox） |
| 前端 | `frontend/src/modules/ai-assistant/composables/` | useSSE / useConversation / useMessageStore / useAgentTools 等 |
| 前端 | `frontend/src/modules/ai-assistant/constants.ts` | 常量 / 状态映射 |
| 后端 | `apps/ai_assistant/models.py` | 7 表定义 |
| 后端 | `apps/ai_assistant/urls.py` | 44 端点路由 |
| 后端 | `apps/ai_assistant/views_drf.py` / `views_toolbox_drf.py` / `views_knowledge_drf.py` / `views_upload_drf.py` | 模块级 DRF 视图（agent / toolbox / knowledge / upload） |
| 后端 | `apps/ai_assistant/views/`（chat_views.py / hitl_views.py / tool_gateway.py） | SSE 对话 / HITL 确认 / 工具网关 |
| 后端 | `apps/ai_assistant/api.py` | 跨模块白名单 + 加密工具 |
| 后端 | `apps/ai_assistant/serializers.py` | 输入校验 |
| 后端 | `apps/ai_assistant/permissions.py` | 所有权检查 |
| 后端 | `apps/ai_assistant/agent_scope/` | agent_factory / tool_registry / in_process_tool / provider_registry / rag_service / skill_registry |

---

## 附录A：功能边界规则

| 边界 | 规则 |
|------|------|
| 我能做什么 | 智能体管理 · SSE 流式对话 · HITL · 文件 / 图片上传 · 知识库管理 · 评测中心 · 工具箱 |
| 我不能做什么 | 直接操作设备（走 device_pool Tool）、直接定位元素（走 element_locator Tool）、直接执行测试（走 test_runner Tool）、直接写业务数据（走各模块 api.py） |
| 如需越界 | 通过 26 平台 Tool 调用各模块 api.py / 只读 ORM；跨模块写走目标 App 的 `api.py` |
| 数据可见性 | Agent / 对话 / 消息按 `owner_id` 隔离，非所有者 403 |
