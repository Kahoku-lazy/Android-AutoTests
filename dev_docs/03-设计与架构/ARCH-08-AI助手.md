# ARCH-08 — AI 助手 (AI Assistant)

> **版本**：v3.0 · **日期**：2026-08-21 · **关联模块**：`apps/ai_assistant/` · 前端 `frontend/src/modules/ai-assistant/`

## 文档内容简述

本文档是 **AI 助手模块**的架构设计，覆盖该模块而非平台全貌：

- **架构四图**：架构全景图 · 模块包图（含防火墙）· 数据流图 · API 关系图（§1.2~1.5）
- **后端架构**：进程内 Agent 构建 + 单请求 SSE 流 + HITL 线程安全 + 工具双通道（§3）
- **API 设计**：41 REST 端点 + SSE（§4）
- **数据模型**：7 表 ER 图（§5）

## 你能从文档获取什么信息

- **AgentScope 如何集成**：`agent_scope/` 作为 Django 进程内模块，`agent_factory.build_agent()` 直接构建 Agent，不再经 HTTP 注册
- **工具如何编排**：`tool_registry.py` 的 30 平台工具单一真相源，`InProcessPlatformTool` 进程内直调 handler；能力开关决定 Toolkit 组装；MCP / Skill 统一由 AI 工具箱导入（智能体禁止自配置）
- **SSE 流如何工作**：单请求 async view + asyncio.Queue，AgentScope `reply_stream` 直接消费逐 token 流式返回
- **端点消费**：41 端点中前端消费 34，7 个后端保留（reveal-key / 任务历史 / 工具网关 / 手动加文档）

## 关联文档

- **架构总纲**：[`ARCH-00-平台总体架构`](./ARCH-00-平台总体架构.md) §3.2（ai_assistant 行）· §4.5 AI 工具编排与 SSE · A.3 Tool 清单
- **需求规格**：[`PRD-08-AI助手`](../02-PRD需求/PRD-08-AI助手.md) — **契约以 PRD §5 为准**

---

## 1. 模块架构概览

### 1.1 架构定位

AI 助手是平台的**自然语言交互中枢**（**L3 业务 App 层**），通过 AgentScope ReAct 推理引擎，让用户以对话方式驱动全流程测试。AgentScope 已从独立 FastAPI 服务迁移为 Django 进程内模块（`apps/ai_assistant/agent_scope/`），Agent 在 Django 进程内构建、运行、流式返回，不再有独立 `agentscope_service/` 目录与 :8000 端口——即 ARCH-00 部署形态的「AgentScope in-process」，非独立分层。

模块在 L3 内承担智能体配置、对话记录与工具编排（30 个 Tool 单一真相源 `tool_registry.py`）；AI 引擎不直连设备、不直写数据库，一切通过 Tool 调用各业务模块 api.py。

### 1.2 架构全景图

> 四层：前端组件 → API 网关（JWT）→ Django 后端（views + agent_scope 进程内）→ 业务模块（Tool 编排）。

```mermaid
flowchart TD
    U["👤 用户浏览器<br/>ai-assistant 3 路由"]

    U -->|"① HTTP REST + JWT"| GATEWAY["API 网关层<br/>JWT 中间件 · urls.py 注册 41 端点"]
    U -->|"③ SSE + JWT 流式"| GATEWAY

    GATEWAY --> V["① 前端组件层 · ai-assistant/<br/>智能体看板 · 对话窗口 · 工具箱 · 知识库 · 评测中心"]

    V --> BE["② 后端层 · apps/ai_assistant/<br/>views/（3 视图模块 + DRF 组）· api.py · models.py（7 表）"]

    BE --> AS["🤖 AgentScope 进程内 · agent_scope/<br/>agent_factory · tool_registry(26 Tool) · in_process_tool · rag_service"]

    AS -->|"进程内直调 handler"| BIZ["④ 业务模块 · device_pool / element_locator / case_manager / test_runner / workflow<br/>经各模块 api.py + 只读 ORM"]

    style U fill:#e3f2fd,stroke:#2196f3
    style GATEWAY fill:#fff3e0,stroke:#ff9800
    style V fill:#e8f5e9,stroke:#4caf50
    style BE fill:#e8eaf6,stroke:#3f51b5
    style AS fill:#f7a8c4,stroke:#3a7a10
    style BIZ fill:#fff8e1,stroke:#ffc107
```

### 1.3 模块包图

> 箭头 = import 方向。ai_assistant 是聚合层，允许 import 任意下层；下层禁止 import 它（agent_scope 内部实现除外）。

```mermaid
flowchart TD
    AI["apps/ai_assistant/<br/>models · views/ · api.py · agent_scope/"]

    DP["device_pool"] -->|"api.list_devices / get_online_devices / acquire / release"| AI
    DI["device_inspector"] -->|"api.capture_snapshot / save_snapshot_to_elements"| AI
    EL["element_locator"] -->|"models.Element / Page（只读）+ api.import_snapshot_page"| AI
    CM["case_manager"] -->|"api.save_* / api_api / api_lock + models（只读）"| AI
    TR["test_runner"] -->|"api.get_run_results / stop_run"| AI
    WF["workflow"] -->|"api.get_document_digest / list_document_summaries（只读）"| AI

    style AI fill:#f7a8c4,stroke:#3a7a10
    style DP fill:#e8f5e9,stroke:#4caf50
    style DI fill:#e8f5e9,stroke:#4caf50
    style EL fill:#e8f5e9,stroke:#4caf50
    style CM fill:#e8f5e9,stroke:#4caf50
    style TR fill:#e8f5e9,stroke:#4caf50
    style WF fill:#e8f5e9,stroke:#4caf50
```

> 注：箭头方向为「数据/依赖来源」视角。实际 `tool_registry.py` 与 `views/` 反向 import 这些下层模块（见 §6.3）。聚合层消费方向：`evaluator` / `dashboard` import `ai_assistant.api` / `ai_assistant.permissions`。

**防火墙规则**：

```
ai_assistant ──✅ import──→ device_pool.api / element_locator.models / case_manager.api* / test_runner.api / workflow.api
ai_assistant ──✅ import──→ 各模块 models（只读查询）
ai_assistant ──❌ import──→ 下层内部实现（service / runner / consumer / state_machine）
下层模块     ──❌ import──→ ai_assistant.agent_scope（内部实现，仅 evaluator 经 api.py 白名单）
```

### 1.4 数据流图

> 用户消息 → SSE view → 进程内 Agent → reply_stream 事件 → SSE 推送 → 消息持久化。

```mermaid
flowchart LR
    subgraph FE["前端"]
        INPUT["输入栏<br/>消息 + 图片/文件"]
        BUBBLE["消息气泡<br/>流式渲染"]
        CONFIRM["HITL 确认弹窗"]
    end

    subgraph DJ["Django views/"]
        CHAT["chat_views.chat_stream<br/>(async view)"]
        QUEUE["asyncio.Queue"]
        HITL["hitl_views.send_confirm_result"]
    end

    subgraph AS["agent_scope/ 进程内"]
        FACTORY["agent_factory.build_agent"]
        STREAM["Agent.reply_stream"]
        TOOLS["InProcessPlatformTool.call"]
    end

    subgraph DB["存储"]
        MSG["ai_messages"]
        EXEC["ai_execution_logs"]
    end

    INPUT -->|"POST /chat/stream"| CHAT
    CHAT --> FACTORY
    FACTORY --> STREAM
    STREAM -->|"SSE 事件"| QUEUE
    QUEUE -->|"text/event-stream"| BUBBLE
    STREAM -->|"RequireUserConfirmEvent"| CONFIRM
    CONFIRM -->|"POST /confirm-result"| HITL
    HITL -->|"call_soon_threadsafe"| QUEUE
    STREAM --> TOOLS
    STREAM -->|"持久化 user/assistant"| MSG
    HITL -->|"审计"| EXEC

    style FE fill:#e8f5e9,stroke:#4caf50
    style DJ fill:#e8eaf6,stroke:#3f51b5
    style AS fill:#f7a8c4,stroke:#3a7a10
    style DB fill:#f5f5f5,stroke:#999
```

### 1.5 API 关系图

> 41 端点 → 前端消费映射，标注前端消费状态（抽象角色）。

```mermaid
flowchart TB
    subgraph API["后端 41 端点（urls.py）"]
        A["agents CRUD + reveal-key + health"]
        C["conversations + messages + chat/stream"]
        T["tools / available-*"]
        K["knowledge status/documents/reindex"]
        TB["toolbox + import"]
        U["upload-avatar / upload-file"]
        GW["tools/schemas + tools/{module}/{action}"]
        TASK["conversations/{id}/tasks + /ai/tasks"]
    end

    subgraph FE["前端抽象角色"]
        BOARD["智能体看板"]
        DETAIL["智能体配置"]
        CHAT["对话窗口"]
        TOOLBOX["AI 工具箱"]
        KB["知识库"]
        EVAL["评测中心"]
    end

    A -->|"列表/详情/创建/更新/删除"| BOARD
    A -->|"详情/创建/更新"| DETAIL
    C -->|"会话/消息/流式/HITL"| CHAT
    T -->|"工具/技能/MCP 配置"| DETAIL
    K -->|"状态/文档/重建"| KB
    TB -->|"列表/创建/导入"| TOOLBOX
    U -->|"头像/文件"| DETAIL

    GW -.->|"❌ 前端未消费（供外部 AgentScope）"| NO["—"]
    TASK -.->|"❌ 前端未消费（任务历史后端保留）"| NO
    REVEAL["reveal-key"] -.->|"❌ 前端未消费（一次性查看）"| NO
    MODELS["agents/{id}/models GET"] -.->|"❌ 前端未消费（详情内嵌缓存）"| NO

    style API fill:#e8f5e9,stroke:#4caf50
    style FE fill:#e3f2fd,stroke:#2196f3
    style GW fill:#f5f5f5,stroke:#999
    style TASK fill:#f5f5f5,stroke:#999
    style REVEAL fill:#f5f5f5,stroke:#999
    style MODELS fill:#f5f5f5,stroke:#999
    style NO fill:#f5f5f5,stroke:#999
```

**数据同步方式**：

| 数据 | 同步方式 |
|------|------|
| 智能体列表 | 首次 `loadAgents` + 手动刷新 + **30min 健康检查轮询**（`checkAgentsHealth`） |
| 对话消息 | 首次 `getMessages` + **SSE 流式增量** + 终端事件后端持久化 |
| 知识库状态 | 首次 `getKnowledgeStatus` + 手动「重建索引」 |

---

## 3. 后端架构

### 3.1 文件结构

```
apps/ai_assistant/
├── models.py              7 表（ai_ 前缀）：AIAgent/AITool/AISharedTool/AIConversation/AIMessage/AITask/AIExecutionLog
├── api.py                 跨模块 __all__ 白名单 + 写操作（Agent/对话 CRUD）+ 加密工具 + evaluator 接口
├── serializers.py         DRF 入参校验与输出 DTO（Agent/对话/消息组）
├── views_drf.py           DRF 视图：AgentViewSet + ConversationViewSet + health/detect/available/tasks APIView
├── views_toolbox_drf.py   AI 工具箱 DRF 视图（共享项 CRUD · 上传 skill · 导入）
├── views_knowledge_drf.py 知识库 DRF 视图（状态/文档/重索引）
├── views_upload_drf.py    头像/文件上传 DRF 视图
├── permissions.py         所有权检查（check_agent_owner / check_conversation_access / filter_*_for_user）
├── decorators.py          require_auth（遗留函数视图用，sync/async 双支持）
├── urls.py                DRF router（agents/conversations，无尾斜杠）+ 遗留/豁免路径
├── views/                 遗留与豁免视图模块（仅 3 文件）
│   ├── chat_views.py        SSE 流式对话（async，进程内 Agent）— 豁免
│   ├── hitl_views.py        HITL 内存会话注册表 + deliver_confirm_result（DRF 视图共用）
│   └── tool_gateway.py      HTTP 工具网关（schemas/agent-config/执行）— 豁免
├── agent_scope/            Django 进程内 AgentScope 模块
│   ├── agent_factory.py     进程内构建 AgentScope Agent
│   ├── tool_registry.py     30 平台工具单一真相源 + handler 注册
│   ├── in_process_tool.py   进程内工具封装（InProcessPlatformTool）
│   ├── provider_registry.py 模型提供商 → base_url/credential 映射
│   ├── rag_service.py       ChromaDB 知识库（唯一所有者）
│   └── skill_registry.py    workspace 技能（Bash/Edit/Glob/Grep/Read/Write）映射
├── management/commands/    init_knowledge_base · migrate_platform_tools · cleanup_uploads
├── migrations/             21 迁移（0001~0021）
├── admin.py                Django Admin 注册
└── apps.py                 verbose_name="AI 助手"
```

> Batch 1/2 起 Agent 组与对话组迁移到 DRF（`views_drf.py`），原 `agent_views.py`/`model_views.py`/`conversation_views.py` 已删除；SSE（`chat_stream`）与工具网关保留函数视图（豁免）。

### 3.2 核心设计：进程内 Agent 构建

```
build_agent(agent_model, user_id)  → AgentScope Agent
  1. 解密 api_key（decrypt_key，失败返回 ""）
  2. provider = get_provider_config(provider, base_url)  → base_url + credential 类型
  3. model = dashscope ? DashScopeChatModel : OpenAIChatModel（其余 OpenAI 兼容）
  4. toolkit = _build_toolkit（按能力开关组装）
  5. ModelConfig / ContextConfig（压缩触发比）/ ReActConfig（max_iters / parallel_tool_calls）
  6. system_prompt = agent_model.system_prompt（无默认，纯对话模型）
```

**Toolkit 组装（能力开关）**：

```
_build_toolkit(agent_model, user_id)
  enable_workspace_tools → 6 内置文件工具（skills_config 逐工具过滤）
  enable_business_tools  → 30 平台工具（AITool tool_type="platform" 逐工具过滤，无配置默认只读子集）
  enable_mcp_tools       → MCP 客户端（AITool tool_type="mcp"）
  enable_skills          → skill 目录（AITool tool_type="skill" 的 dir_path）
```

### 3.3 核心设计：单请求 SSE 流

```
chat_stream（async Django view，运行在 Daphne 事件循环）
  ├─ require_auth + check_conversation_access
  ├─ save_message(user, flow="sse")
  ├─ asyncio.Queue + asyncio.Task(_agent_stream)
  │    ├─ build_agent（sync → thread pool，thread_sensitive=False）
  │    ├─ _restore_context（从 ai_messages 恢复历史到 agent.state.context）
  │    ├─ reply_stream 事件循环 → queue.put(SSE)
  │    ├─ RequireUserConfirmEvent → 等待 confirm_queue（120s）→ 续跑
  │    └─ ReplyEnd / ExceedMaxIters → save_message(assistant) + 附 _backend_msg_id
  └─ event_generator → StreamingHttpResponse（text/event-stream，2min 心跳）
```

- `_sta` = `sync_to_async(thread_sensitive=False)`，DB 操作在泛型线程池跑，响应发出后仍可写
- `_bg_agent_tasks` / `_active_agent_tasks` 持有 Task 引用防 GC + 取消 stale 任务

### 3.4 核心设计：HITL 线程安全投递

```
send_confirm_result（sync view，Daphne 线程池）
  → _agent_sessions[conv_id]（in-memory registry + threading.Lock）
  → _main_loop.call_soon_threadsafe(confirm_queue.put_nowait, data)
  → 审计写 AIExecutionLog
```

`chat_stream` 首次运行时 `set_main_loop()` 记录主事件循环引用，跨线程安全投递确认结果。

### 3.5 核心设计：工具双通道

| 通道 | 文件 | 场景 | 是否走 HTTP |
|------|------|------|:--:|
| 进程内 | `in_process_tool.py` | 当前 Agent 工具调用 | ❌（`asyncio.to_thread` 直调 handler） |
| HTTP | `tool_gateway.py` | `/api/tools/{module}/{action}` 供外部 AgentScope | ✅（httpx） |

两者共享 `tool_registry.py` 的 `TOOL_SCHEMAS` + `resolve()`，handler 签名统一 `handler(user_id, **kwargs)`。`tool_gateway` 的 `tool_schemas` / `agent_config` 端点返回工具定义与每智能体配置。

---

## 4. API 设计

> 响应信封统一 `{status, data}` / `{status, message}`；字段 snake_case。**完整字段契约以 PRD §5 为准**，本节只列概览。

### 4.1 REST 端点（41 个）+ SSE

> **端点口径**：41 REST 方法端点 = ARCH-00 路径条目口径的 **15 条 path + DRF 生成路由**（Batch 1-3 已全量收官，SSE 与工具网关豁免函数视图）；本节按方法端点列全量消费映射。

| 组 | 方法 | 路径 | 前端消费 |
|------|------|------|:--:|
| Agent | GET | `/api/ai/agents` | ✅ |
| Agent | POST | `/api/ai/agents/create` | ✅ |
| Agent | GET | `/api/ai/agents/{id}` | ✅ |
| Agent | POST | `/api/ai/agents/{id}/update` | ✅ |
| Agent | POST | `/api/ai/agents/{id}/delete` | ✅ |
| Agent | POST | `/api/ai/agents/{id}/reveal-key` | ❌ |
| Agent | GET | `/api/ai/agents/{id}/conversations` | ✅ |
| Agent | POST | `/api/ai/agents/{id}/conversations/create` | ✅ |
| 对话 | GET | `/api/ai/conversations/{id}/messages` | ✅ |
| 对话 | POST | `/api/ai/conversations/{id}/save-message` | ✅ |
| 对话 | POST | `/api/ai/conversations/{id}/confirm-result` | ✅ |
| 对话 | POST | `/api/ai/conversations/{id}/rename` | ✅ |
| 对话 | POST | `/api/ai/conversations/{id}/delete` | ✅ |
| 对话 | POST | `/api/ai/conversations/{id}/chat/stream`（SSE） | ✅ |
| 模型 | POST | `/api/ai/models/detect` | ✅ |
| 模型 | POST | `/api/ai/agents/{id}/test` | ✅ |
| 模型 | GET | `/api/ai/agents/{id}/models` | ❌ |
| 模型 | GET | `/api/ai/agents/health` | ✅ |
| 工具 | GET | `/api/ai/available-tools` | ✅ |
| 工具 | GET | `/api/ai/available-skills` | ✅ |
| 工具 | GET | `/api/ai/agents/{id}/tools` | ✅ |
| 工具 | POST | `/api/ai/agents/{id}/tools/{tid}/toggle` | ✅ |
| 工具 | POST | `/api/ai/agents/{id}/tools/{tid}/delete` | ✅ |
| 任务 | GET | `/api/ai/conversations/{id}/tasks` | ❌ |
| 任务 | GET | `/api/ai/conversations/{id}/tasks/{run_id}` | ❌ |
| 任务 | GET | `/api/ai/tasks` | ❌ |
| 上传 | POST | `/api/ai/upload-avatar` | ✅ |
| 上传 | POST | `/api/ai/upload-file` | ✅ |
| 知识库 | GET | `/api/ai/knowledge/status` | ✅ |
| 知识库 | GET | `/api/ai/knowledge/documents` | ✅ |
| 知识库 | POST | `/api/ai/knowledge/reindex` | ✅ |
| 知识库 | POST | `/api/ai/knowledge/documents/add` | ❌ |
| 工具网关 | GET | `/api/ai/tools/schemas` | ❌ |
| 工具网关 | GET | `/api/ai/tools/agent-config/{id}` | ❌ |
| 工具网关 | POST | `/api/ai/tools/{module}/{action}` | ❌ |
| 工具箱 | GET | `/api/ai/toolbox` | ✅ |
| 工具箱 | POST | `/api/ai/toolbox/create` | ✅ |
| 工具箱 | POST | `/api/ai/toolbox/{id}/update` | ✅ |
| 工具箱 | POST | `/api/ai/toolbox/{id}/delete` | ✅ |
| 工具箱 | POST | `/api/ai/toolbox/upload-skill` | ✅ |
| 工具箱 | POST | `/api/ai/agents/{id}/tools/import-from-toolbox` | ✅ |

### 4.2 响应格式（Agent 详情，Batch 1 起 DRF 信封）

```json
{
  "status": true,
  "data": {
    "agent": {
      "id": 1,
      "name": "测试助手",
      "model_provider": "dashscope",
      "model_name": "qwen-max",
      "api_key": "sk-***abcd",
      "enable_workspace_tools": false,
      "enable_business_tools": true,
      "enable_mcp_tools": false,
      "enable_skills": false,
      "knowledge_sources": { "doc:02-PRD需求/PRD-02-设备管理.md": true },
      "is_connected": true,
      "tools": [
        { "id": 1, "name": "save_case", "tool_type": "platform", "config_json": "{}", "enabled": true }
      ]
    }
  }
}
```

> Agents/Conversations 组已迁 DRF，成功响应由 `EnvelopeJSONRenderer` 统一包裹为 `{status: true, data: {...}}`；
> 错误为 `{status: false, message}` + HTTP 状态码。toolbox/knowledge/uploads/agent tools 组（Batch 3）暂为过渡形态。

> 完整字段表（能力开关 / AgentScope 参数 / 工具列表）见 PRD §5.2。

---

## 5. 数据模型

### 5.1 ER 图

```mermaid
erDiagram
    auth_user ||--o{ ai_agents : "owner (SET_NULL)"
    auth_user ||--o{ ai_conversations : "owner (SET_NULL)"

    ai_agents ||--o{ ai_tools : "agent (CASCADE)"
    ai_agents ||--o{ ai_conversations : "agent (CASCADE)"
    ai_agents ||--o{ ai_tasks : "agent (CASCADE)"
    ai_agents ||--o{ ai_execution_logs : "agent (CASCADE)"

    ai_conversations ||--o{ ai_messages : "conversation (CASCADE)"
    ai_tasks ||--o{ ai_execution_logs : "task (SET_NULL, 可空)"

    ai_agents {
        int id PK
        int owner_id FK "auth_user, SET_NULL"
        string name
        text avatar "data URI"
        string tags
        text description
        string model_provider "dashscope/openai/anthropic/deepseek/gemini/custom"
        string model_name
        string api_key "Fernet 加密"
        string base_url
        text system_prompt
        float temperature
        int max_tokens
        string formatter
        int max_iters
        bool parallel_tool_calls
        string memory_mode "inmemory/longterm"
        text generate_kwargs
        bool compression_enabled
        int compression_threshold
        bool tts_enabled
        bool enable_knowledge_base
        bool enable_workspace_tools
        bool enable_business_tools
        bool enable_mcp_tools
        bool enable_skills
        json skills_config "逐 workspace 工具开关"
        json knowledge_sources "逐文档开关"
        string status
        bool is_connected
        text available_models "JSON 列表"
        string agent_scope_id
        string agent_scope_credential_id
        string credential_hash
        bool key_revealed
        datetime last_checked_at
        datetime created_at
        datetime updated_at
    }

    ai_tools {
        int id PK
        int agent_id FK
        string name
        string tool_type "platform/mcp/skill"
        text config_json
        bool enabled
        datetime created_at
    }

    ai_shared_tools {
        int id PK
        string name
        string item_type "skill/mcp/extension"
        text description
        text config_json
        bool enabled
        datetime created_at
        datetime updated_at
    }

    ai_conversations {
        int id PK
        int owner_id FK "auth_user, SET_NULL"
        int agent_id FK
        string title
        string status "active"
        string agent_scope_session_id
        datetime created_at
        datetime updated_at
    }

    ai_messages {
        int id PK
        int conversation_id FK
        string role "user/assistant/system"
        text content
        text tool_calls
        text blocks "ContentBlock JSON 数组"
        string reason "normal/exceed_max_iters/stopped/error"
        int tokens
        int input_tokens
        string model_name
        string flow "sse/fallback"
        datetime created_at
    }

    ai_tasks {
        int id PK
        int agent_id FK
        string title
        text description
        string status
        text result
        datetime scheduled_at
        datetime started_at
        datetime finished_at
        datetime created_at
    }

    ai_execution_logs {
        int id PK
        int agent_id FK
        int task_id FK "SET_NULL, 可空"
        string level "info/warn/error"
        text message
        text metadata
        datetime created_at
    }
```

> `ai_tasks`（AITask）当前无视图使用；任务历史由 `test_runner.TestRunRecord`（`tr_test_runs`）以 `run_id` 前缀 `ai-task-*` / `case-gen-*` 支撑。

---

## 6. 模块边界与跨模块交互

### 6.1 边界规则

| 规则 | 说明 |
|------|------|
| AgentScope 进程内直连 | 构建 / 推理 / Tool 编排全在 Django 进程内，无独立服务 / 端口 |
| AI 不直连设备 / 数据库 | 一切通过 Tool 调用各模块 api.py / 只读 ORM |
| 工具单一真相源 | `tool_registry.py` `TOOL_SCHEMAS` 定义 30 平台工具 + handler 注册 |
| 写操作走 api.py | 跨模块写走目标 App 的 api.py，禁止直接 ORM 写 |
| 工具箱集中管理 | skill 上传 / MCP 配置唯一入口是 AI 工具箱（`views_toolbox_drf.py`）；智能体只能 `import-from-toolbox` 导入副本，禁止自配置 |
| 知识库唯一所有者 | ChromaDB 由 `rag_service.py` 独占，AgentScope 不直接接触；引用键 `doc:`（按文件）/ `dir:`（按目录，检索时动态展开为目录下当前全部文件） |
| API Key 安全 | Fernet 加密 + 脱敏 + 一次性 reveal + base_url 白名单防 SSRF |
| 所有权隔离 | Agent / 对话按 `owner_id` 过滤，非所有者 403 |

### 6.2 对外接口（api.py `__all__`）

```python
get_agent(agent_id) -> AIAgent | None               # 只读
get_agent_by_scope_id(scope_id) -> AIAgent | None   # 只读
list_active_agents() -> list[dict]                  # 只读
get_conversation(conv_id) -> AIConversation | None  # 只读
get_or_create_conversation(agent, title) -> tuple   # 写
save_message(conversation_id, role, content, ...)   # 写
encrypt_key(plain) -> str                           # 加密
decrypt_key(encrypted) -> str                       # 解密（失败返回 ""）
mask_key(key) -> str                                # 脱敏
# 跨模块接口（供 evaluator 等，避免直接 import agent_scope 内部）
get_provider_config(provider, base_url, model_name) -> dict
search_knowledge(query, top_k, sources) -> list[dict]
get_kb_doc_count() -> int
```

### 6.3 跨模块消费者

| 消费方 | 调用方式 | 用途 |
|------|------|------|
| **evaluator** | `api.get_provider_config` / `search_knowledge` / `get_kb_doc_count`（`require_auth` 已于 2026-08-20 下沉 `shared/auth/`，fix-cross-app-firewall） | NL 用例生成 / 执行 |
| **dashboard** | `ai_assistant.api.filter_agents_for_user`（原 `permissions` 违规已于 2026-08-20 修复改走 api） | 聚合层复用权限过滤 |

---

## 7. 设计要点

| 要点 | 说明 |
|------|------|
| 进程内 Agent | `agent_factory.build_agent()` 直接构建，消除 HTTP 注册 / session 往返，Django 进程即 AgentScope 运行时 |
| 单请求 SSE | async view + asyncio.Queue 替换旧「create-session + subscribe + trigger」三请求流，真逐 token 流式 |
| 能力开关 | 四组 `enable_*` 开关决定 Toolkit 组装，新建默认纯对话模型，避免过度授权 |
| 工具双通道 | 进程内直调为主，HTTP `tool_gateway` 保留供外部 AgentScope；共享 `tool_registry` 单一真相源 |
| HITL 线程安全 | in-memory registry + `call_soon_threadsafe` 跨线程投递确认结果 |
| 安全闭环 | Key 加密 + 脱敏 + 一次性 reveal + base_url 白名单防 SSRF |
| 知识库隔离 | ChromaDB 由 `rag_service.py` 独占，`knowledge_sources` 逐智能体过滤文档 |
| 工具箱集中管理 | 智能体配置页仅保留「从 AI 工具箱选取」导入面板；MCP/Skill 自配置 UI 与端点（`mcp/save`、`mcp/test`、`skill/upload`）已移除 |

---

## 变更记录

| 版本 | 日期 | 变更摘要 |
|------|------|----------|
| v3.0 | 2026-08-21 | **五层口径回填 + 事实同步**：§1.1 去「横跨后端层与 AI 引擎层」改 L3 业务 App + in-process 说明（非独立分层）；§1.2 图去旧 L2 标签（BE）、views/ 收敛 3 文件；§6.1 工具箱落点改 `views_toolbox_drf.py`；§6.3 dashboard/evaluator 违规改 ✅（2026-08-20 fix-cross-app-firewall：filter_agents_for_user→api、require_auth→shared/auth/）；§4.1 补端点口径（41 方法端点 = 15 path + DRF 生成）；关联指针改 §3.2/§4.5/A.3 |
| v1.0 | 2026-07-16 | 初始版本：基于 `项目架构.md` 与旧 PRD 重构 |
| v1.1 | 2026-07-16 | 代码对照审计：端点 32→37，views 文件 5→9 |
| v1.2 | 2026-07-22 | 多类型用例生成：Tool 24→28，任务卡片双位置同步 |
| v2.0 | 2026-08-18 | 按 ARCH-02 格式重构：补架构四图 + 防火墙 + 契约偏差登记；同步代码真相——AgentScope 独立服务→进程内（`agent_scope/`，无 tools/ 目录、system_prompt.py、rag/ 目录）；Tool 28→14 平台工具 + 能力开关（workspace/business/mcp/skills）；端点校正 44（移除 register-scope/create-scope-session/send/avatars，新增 toolbox/available-tools/available-skills/tools 网关）；表 6→7（新增 `ai_shared_tools`）；登记 TD-04~TD-08 |
| v2.1 | 2026-08-19 | 工具箱集中管理收紧：移除端点 `mcp/save`、`mcp/test`、`skill/upload` 及前端「MCP 服务器」「Skills」面板（44→41）；智能体只能从工具箱导入 skill/MCP |
| v2.2 | 2026-08-19 | DRF 迁移（Batch 0-2）：Agent 组 + 对话/消息/任务/HITL 组迁移到 DRF（`views_drf.py`：AgentViewSet/ConversationViewSet/health/detect/available/tasks APIView）；`urls.py` 改 `DefaultRouter(trailing_slash=False)`；写库收敛到 `api.py`（19 处视图直写 ORM 已收敛 15 处）；响应统一 `{status, data}` 信封（前端 `data.data` 解包）；删除 `agent_views.py`/`model_views.py`/`conversation_views.py`；新增 `tests/ai_assistant/` live-server 接口测试 70 例；SSE 与工具网关豁免 |
| v2.3 | 2026-08-19 | 知识库目录树化：`helpers/kb-tree.ts` 按 `dev_docs/` 本地目录构建折叠树 + `KbTreeView.vue` 递归树组件；知识库 Tab 与导入弹窗支持目录级（`dir:` 动态展开）与文件级（`doc:`）混选；`rag_service.search` 前置 `_resolve_sources` 统一展开引用键并修复 `doc:` 前缀过滤不匹配 |
| v2.4 | 2026-08-19 | DRF 迁移 Batch 3 完成（全量迁移收官）：工具箱/知识库/上传/Agent 工具管理迁移到 DRF（`views_toolbox_drf.py`/`views_knowledge_drf.py`/`views_upload_drf.py`）；写库全部收敛 `api.py`；删除 `toolbox_views.py`/`knowledge_views.py`/`file_views.py`/`tool_views.py`/`common.py`；Swagger 收录 37 个 ai 路径；全模块仅 SSE 与工具网关保留函数视图（豁免） |
| v2.5 | 2026-08-19 | 设备管理新增只读工具 `list_devices`（devices/list_all）：返回设备管理口径全量设备（ONLINE + BUSY，含使用人/剩余占用时间，按可见性过滤），修复 AI 回答设备数时漏报使用中设备；平台工具 14→15 |
| v2.6 | 2026-08-19 | 承接设备检查器快照化（ARCH-03 v1.7）：新增「设备检查器」工具分类与 2 工具——`capture_page`（inspector/capture，只读，抓取 JSON 并落库快照）/ `save_page_to_elements`（inspector/save_elements，写工具，基于快照按自定义目录/页面名写入元素定位）；工具 15→17、分类 5→6；包图增 device_inspector 依赖；element_locator 依赖补 api.import_snapshot_page |
| v2.6 | 2026-08-19 | §3.1 文件结构对齐 v2.4 迁移结果：模块级补 `views_toolbox_drf.py`/`views_knowledge_drf.py`/`views_upload_drf.py`，`views/` 收敛为 chat_views/hitl_views/tool_gateway 3 文件（删除已下线的 file_views/knowledge_views/tool_views/toolbox_views/common）；全景图端点计数 44→41 |
| v2.7 | 2026-08-19 | 新增「工作流」工具分类与 2 只读工具——`list_page_flows`（workflow/list_page_flows）/`get_page_flow`（workflow/get_page_flow，返回页面流语义摘要）；平台工具 23→25、分类 6→7；包图/全景图/防火墙清单增 workflow 依赖（AI 只经 `workflow.api` 调 `get_document_digest`/`list_document_summaries`，语义编译在 `workflow/semantics.py` 纯函数）；正文工具计数 17→25 对齐代码真相 |
| v2.8 | 2026-08-20 | 用例工具可执行性修复：case-manager 新增 `api_ai.py`（`get_case_digest` 结构化 digest / `save_ai_definition` 校验写入 / `validate_steps` 步骤白名单校验，api.py 门面再导出）；`get_case`/`save_case` handler 改走 api_ai（UI 步骤落 `steps_json`、Web 落 `steps_json` 字符串）；`in_process_tool._format_result` 新增 dict 与单模型实例 JSON 序列化分支（详情类工具不再 str() 化为标题；关系字段只输出原始外键 id，防事件循环线程懒加载 ORM 致 SynchronousOnlyOperation）；save_case schema 增 directory_id/package_name/enabled/priority；步骤白名单与语义沿用 `models/step_types.py` `STEP_TYPE_META` |
| v2.9 | 2026-08-20 | 执行引擎状态打通：test_runner.api 新增 `get_run_status`（TestRunRecord 状态/设备/用例快照/结果计数/汇总）；新增只读工具 `get_run_status`（runner/get_run_status）；`get_run_results` handler 信封化（`{run_status, results}`，run 不存在 400）；平台工具 25→26 |
| v3.0 | 2026-08-25 | 页面结构分析语义增强（工具入参 + handler 校验）：新增 `agent_scope/llm_semantic.py`（`validate_semantic` 纯校验，rid 真实性 + metrics 枚举防幻觉）；新增工具 `analyze_page`（inspector/analyze，纯规则分区，无 LLM）与 `save_page_semantic`（inspector/save_semantic，语义命名提交校验）；对齐 `save_case` 的「工具入参 + handler 校验」模式，不依赖 `generate_structured_output`（thinking 模型不支持强制 tool_choice）；平台工具 28→30 |
