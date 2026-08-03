# AI 助手模块功能分析报告

> 分析日期：2026-07-31
> 覆盖范围：`apps/ai_assistant/` + `agentscope_service/`
> 架构模式：Django 应用层 ↔ AgentScope 服务层，通过 HTTP 网关解耦通信

---

## 整体架构

```
前端 (Vue 3)
  │  HTTP REST + SSE
  ▼
Django :8765  ─────────────────────────────────────────────
  │  apps/ai_assistant/
  │  ├── auth_views     认证
  │  ├── agent_views    Agent CRUD + 健康检查 + 注册
  │  ├── conversation   对话/消息 CRUD
  │  ├── hitl_views     HITL + SSE 会话
  │  ├── model_views    模型探测
  │  ├── tool_views     MCP/Skill 管理
  │  ├── toolbox_views  共享工具箱
  │  ├── tool_gateway   ← AgentScope 工具调用入口
  │  ├── knowledge      ChromaDB RAG 管理
  │  ├── file_views     文件上传/解析
  │  └── agent_scope/   工具注册表 + 提供商 + RAG + 提示词
  │
  │  HTTP (内部)  ─────────────────────────┐
  │                                        │
  ▼                                        ▼
AgentScope :8000  ─────────────────────────────
  │  agentscope_service/
  │  ├── app            FastAPI 创建
  │  ├── factory        工具构建 + 过滤
  │  ├── platform_tool  HTTP 转发执行
  │  └── workspace      技能开关过滤
  │
  ▼
Redis :6379  (Storage + MessageBus + JWT 黑名单)
ChromaDB     (向量知识库)
```

---

## 一、认证鉴权模块

| 功能 | 核心文件 | 说明 |
|------|----------|------|
| 用户登录 | `apps/ai_assistant/views/auth_views.py:20` | JWT 双 token（access + refresh），分层中文校验 |
| 用户注册 | `apps/ai_assistant/views/auth_views.py:77` | 用户名/密码校验，重复检测 |
| Token 刷新 | `apps/ai_assistant/views/auth_views.py:131` | 用 refresh_token 换新的 access_token |
| 登出黑名单 | `apps/ai_assistant/views/auth_views.py:145` | Token 加入 Redis 黑名单，重启不丢失 |
| 当前用户查询 | `apps/ai_assistant/views/auth_views.py:165` | `/api/ai/auth/me` 返回当前用户信息 |
| 视图鉴权装饰器 | `apps/ai_assistant/decorators.py:7` | `@require_auth` 拒绝未认证请求 |
| AgentScope JWT 验证 | `agentscope_service/auth.py` | 覆盖 AgentScope 默认鉴权，走 JWT |

**API 端点**：
```
POST /api/ai/auth/login
POST /api/ai/auth/register
POST /api/ai/auth/refresh
POST /api/ai/auth/logout
GET  /api/ai/auth/me
```

---

## 二、智能体（Agent）管理模块

| 功能 | 核心文件 | 说明 |
|------|----------|------|
| 创建智能体 | `apps/ai_assistant/views/agent_views.py:137` | 支持 40+ 配置字段，含模型参数、AgentScope 配置、压缩、TTS、知识库等 |
| 更新智能体 | `apps/ai_assistant/views/agent_views.py:238` | Diff-based 工具同步，Key 变更检测，system_prompt 变更触发重新注册 |
| 删除智能体 | `apps/ai_assistant/views/agent_views.py:368` | 级联删除关联数据 |
| 智能体列表 | `apps/ai_assistant/views/agent_views.py:50` | 按 owner 过滤，含 tool_count |
| 智能体详情 | `apps/ai_assistant/views/agent_views.py:72` | 完整配置 + 关联工具列表，API Key 脱敏 |
| API Key 一次性查看 | `apps/ai_assistant/views/agent_views.py:329` | 仅首次查看完整 Key，之后只返回脱敏值 |
| 注册到 AgentScope | `apps/ai_assistant/views/agent_views.py:444` | 同步 Agent 到 AgentScope 服务，创建凭证 |

**API 端点**：
```
GET    /api/ai/agents                        # 列表
POST   /api/ai/agents/create                 # 创建
GET    /api/ai/agents/{id}                   # 详情
POST   /api/ai/agents/{id}/update            # 更新
POST   /api/ai/agents/{id}/delete            # 删除
POST   /api/ai/agents/{id}/reveal-key        # 一次性查看 API Key
POST   /api/ai/agents/{id}/register-scope    # 注册到 AgentScope
GET    /api/ai/agents/health                 # 批量健康检查
GET    /api/ai/default-system-prompt         # 默认系统提示词模板
GET    /api/ai/available-skills              # 可用工作区技能列表
```

### Agent 模型配置属性 (`AIAgent` - `apps/ai_assistant/models.py:7`)

**基础信息**：name, avatar, tags, description, model_provider, model_name, api_key, base_url

**推理参数**：temperature, max_tokens, generate_kwargs

**AgentScope 2.0**：formatter, max_iters, parallel_tool_calls, print_hint_msg

**记忆模式**：memory_mode (inmemory / longterm), long_term_memory_mode

**高级功能**：enable_meta_tool, enable_rewrite_query, enable_knowledge_base

**上下文压缩**：compression_enabled, compression_threshold, compression_keep_recent, compression_prompt, compression_template

**语音合成**：tts_enabled

**技能过滤**：skills_config（6 项工作台技能按名开关）

**阶段工具**：phase_tool_config（SOP 阶段 → 工具名称映射）

**知识源**：knowledge_sources（文档 ID 白名单）

**健康检查**：is_connected, last_checked_at, available_models

**安全**：key_revealed（一次性查看标记）

**凭证缓存**：agent_scope_id, agent_scope_credential_id, credential_hash

---

## 三、对话管理模块

| 功能 | 核心文件 | 说明 |
|------|----------|------|
| 创建对话 | `apps/ai_assistant/views/conversation_views.py:40` | 关联 Agent，生成空对话 |
| 对话列表 | `apps/ai_assistant/views/conversation_views.py:25` | 按 agent 过滤，按更新时间倒序 |
| 重命名对话 | `apps/ai_assistant/views/conversation_views.py:70` | UTF-8 编码校验 |
| 删除对话 | `apps/ai_assistant/views/conversation_views.py:57` | 级联删除消息 |
| 消息列表 | `apps/ai_assistant/views/conversation_views.py:89` | 含 blocks（ContentBlock）、reason、tokens、flow |
| 保存消息 | `apps/ai_assistant/views/conversation_views.py:107` | 支持 user/assistant/system 角色，blocks 结构 |

**API 端点**：
```
GET    /api/ai/agents/{id}/conversations              # 对话列表
POST   /api/ai/agents/{id}/conversations/create        # 创建对话
GET    /api/ai/conversations/{id}/messages             # 消息列表
POST   /api/ai/conversations/{id}/save-message         # 保存消息
POST   /api/ai/conversations/{id}/rename               # 重命名
POST   /api/ai/conversations/{id}/delete               # 删除
```

### 对话模型 (`AIConversation` - `apps/ai_assistant/models.py:125`)

| 字段 | 类型 | 说明 |
|------|------|------|
| owner | FK → User | 对话所有者 |
| agent | FK → AIAgent | 关联智能体 |
| title | CharField(500) | 对话标题 |
| status | CharField(20) | active 等 |
| agent_scope_session_id | CharField(200) | AgentScope SSE 会话 ID |

### 消息模型 (`AIMessage` - `apps/ai_assistant/models.py:153`)

| 字段 | 类型 | 说明 |
|------|------|------|
| conversation | FK → AIConversation | 所属对话 |
| role | CharField(20) | user / assistant / system |
| content | TextField | 文本内容 |
| tool_calls | TextField | 工具调用 JSON |
| **blocks** | TextField | 完整 ContentBlock 数组（thinking/input/output/state/hint） |
| **reason** | CharField(30) | 结束原因：normal / exceed_max_iters / stopped / error |
| tokens | IntegerField | 总 token 数 |
| input_tokens | IntegerField | 输入 token 数 |
| model_name | CharField(100) | 使用的模型名 |
| **flow** | CharField(20) | 传输方式：sse / fallback |

---

## 四、HITL（人机协同）模块

| 功能 | 核心文件 | 说明 |
|------|----------|------|
| 确认结果回传 | `apps/ai_assistant/views/hitl_views.py:24` | 用户决策 relay 到 AgentScope session，含执行日志 |
| SSE 会话创建 | `apps/ai_assistant/views/hitl_views.py:69` | 自动注册 Agent + 创建凭证 + 创建 session，凭证缓存复用 |

**API 端点**：
```
POST /api/ai/conversations/{id}/confirm-result       # HITL 决策回传
POST /api/ai/conversations/{id}/create-scope-session  # 创建 AgentScope SSE 会话
```

### SSE 会话创建流程

```
create_scope_session(conv_id)
  ├── Agent 未注册？
  │   └── _do_register_agentscope_agent() → AgentScope POST /agent/
  ├── 凭证缓存命中？
  │   ├── 是 → 复用 credential_id
  │   └── 否 → create_agentscope_credential() → AgentScope POST /credential/
  ├── 构建 session_body（model 参数 + generate_kwargs）
  └── call_agentscope("/sessions/", "POST") → 返回 session_id
```

---

## 五、模型连接与健康检查模块

| 功能 | 核心文件 | 说明 |
|------|----------|------|
| 连接测试 | `apps/ai_assistant/views/model_views.py:54` | 先 `/models` 探测 → 兜底 `/chat/completions` → 缓存结果 |
| 模型列表探测 | `apps/ai_assistant/views/model_views.py:113` | POST 模式从 API 配置探测，GET 模式返回缓存 |
| 批量健康检查 | `apps/ai_assistant/views/agent_views.py:375` | 30 分钟 TTL 缓存，ping 所有活跃 Agent |

**API 端点**：
```
POST /api/ai/agents/{id}/test       # 连接测试 + 模型列表
POST /api/ai/models/detect          # 从 API 配置探测模型
GET  /api/ai/agents/{id}/models     # 获取缓存模型列表
GET  /api/ai/agents/health          # 批量健康检查
```

### 提供商注册表 (`apps/ai_assistant/agent_scope/provider_registry.py`)

| 提供商 | 默认 base_url | 凭证类型 |
|--------|--------------|----------|
| dashscope | `https://dashscope.aliyuncs.com/compatible-mode/v1` | dashscope_credential |
| openai | `https://api.openai.com/v1` | openai_credential |
| anthropic | `https://api.anthropic.com/v1` | openai_credential |
| deepseek | `https://api.deepseek.com/v1` | openai_credential |
| gemini | `https://generativelanguage.googleapis.com/v1beta/openai` | openai_credential |
| custom | 用户自定义 | openai_credential |

安全校验：提供商 URL 白名单验证 + 阻止 localhost/127.0.0.1 + 生产环境强制 HTTPS。

---

## 六、工具管理模块

### 6.1 平台工具注册表

`apps/ai_assistant/agent_scope/tool_registry.py` — **唯一的工具真相源**

| 分类 | 工具名称 | 模块/动作 | 读写 |
|------|---------|-----------|:--:|
| 📱 设备管理 | get_online_devices | devices/list_online | 读 |
| | acquire_device | devices/acquire | 写 |
| | release_device | devices/release | 写 |
| 🔍 元素定位 | search_elements | elements/search | 读 |
| | list_pages | elements/list_pages | 读 |
| | fetch_page_elements | elements/fetch_page_elements | 读 |
| 📋 用例管理 | save_case | cases/save_definition | 写 |
| | get_case | cases/get_definition | 读 |
| | debug_case | cases/get_case_detail | 读 |
| ▶️ 测试执行 | run_test | runner/run_test | 写 |
| | get_run_results | runner/get_run_results | 读 |
| | stop_run | runner/stop_run | 写 |
| 📊 知识库 | search_knowledge_base | knowledge/search | 读 |

注册机制：`@_register(module, action)` 装饰器，handler 通过 `resolve(module, action)` 查找。

### 6.2 工具网关（AgentScope ↔ Django 通信核心）

`apps/ai_assistant/views/tool_gateway.py`

| 端点 | 调用方 | 功能 |
|------|--------|------|
| `GET /api/tools/schemas` | AgentScope 启动时 | 返回所有工具 Schema 定义 |
| `GET /api/tools/agent-config/<id>` | 每次 Session 创建 | 返回 Agent 专属配置（启用的工具、禁用的技能、知识源、阶段配置） |
| `POST /api/tools/<module>/<action>` | AgentScope 工具调用 | 执行工具，JWT 注入 user_id，ORM → JSON 序列化 |

### 6.3 单智能体工具管理

`apps/ai_assistant/views/tool_views.py`

| 功能 | 说明 |
|------|------|
| MCP 管理 | 添加/更新 stdio 或 HTTP MCP 服务（按名称 upsert） |
| MCP 测试 | stdio：子进程启动验证；HTTP：连通性检查（15s 超时） |
| Skill 上传 | webkitdirectory 上传，隔离到 `data/skills/{agent_id}/{name}/`，自动检测特征生成 `_manifest.json` |
| 工具启用/禁用 | toggle_tool（按 enabled 字段开关） |
| 工具删除 | 级联清理 Skill 文件目录 |

**API 端点**：
```
GET    /api/ai/agents/{id}/tools                     # 工具列表（MCP + Skill 分组）
POST   /api/ai/agents/{id}/tools/mcp/save             # 添加/更新 MCP
POST   /api/ai/agents/{id}/tools/mcp/test             # 测试 MCP 连通性
POST   /api/ai/agents/{id}/tools/skill/upload          # 上传 Skill
POST   /api/ai/agents/{id}/tools/{tool_id}/toggle      # 启用/禁用
DELETE /api/ai/agents/{id}/tools/{tool_id}             # 删除工具
```

### 6.4 共享工具箱（跨 Agent 复用）

`apps/ai_assistant/views/toolbox_views.py`

| 功能 | 说明 |
|------|------|
| 共享工具列表 | mcp / skill / extension 三类，按更新时间倒序 |
| 创建/更新/删除 | 共享 MCP 和 extension 类型的 CRUD |
| 共享 Skill 上传 | 文件存储 `data/shared_skills/{id}/`，自动特征检测 |
| 导入到智能体 | 从工具箱导入到 Agent，Skill 类型自动复制文件目录，同名去重 |

**API 端点**：
```
GET    /api/ai/toolbox                                  # 列表
POST   /api/ai/toolbox/create                           # 创建
POST   /api/ai/toolbox/{id}/update                      # 更新
POST   /api/ai/toolbox/{id}/delete                      # 删除
POST   /api/ai/toolbox/upload-skill                     # 上传共享 Skill
POST   /api/ai/agents/{id}/tools/import-from-toolbox     # 导入到 Agent
```

**模型**：`AISharedTool` - `apps/ai_assistant/models.py:101`

---

## 七、知识库（RAG）模块

| 功能 | 核心文件 | 说明 |
|------|----------|------|
| 向量检索 | `apps/ai_assistant/agent_scope/rag_service.py:59` | ChromaDB 自然语言搜索，支持 source 过滤 + 兜底后过滤 |
| 文档加载 | `apps/ai_assistant/agent_scope/rag_service.py:198` | 扫描 `dev_docs/*.md` + 生成 StepType 枚举参考文档 |
| 状态查看 | `apps/ai_assistant/views/knowledge_views.py:55` | 向量库文档数/大小 + 重建任务状态 |
| 文档列表 | `apps/ai_assistant/views/knowledge_views.py:67` | 只返回元数据（id/source/type/size），不含正文（节省 300KB） |
| 索引重建 | `apps/ai_assistant/views/knowledge_views.py:77` | 异步线程重建，互斥锁防并发 |
| 手动添加文档 | `apps/ai_assistant/views/knowledge_views.py:107` | 手动注入单篇文档到向量库 |
| Agent 级过滤 | `AIAgent.knowledge_sources` 字段 | 配置每个 Agent 可见的文档 ID 白名单 |

**API 端点**：
```
GET  /api/ai/knowledge/status              # 索引状态
GET  /api/ai/knowledge/documents           # 可索引文档列表
POST /api/ai/knowledge/reindex             # 触发全量重建
POST /api/ai/knowledge/documents/add       # 手动添加文档
```

**数据流**：
```
dev_docs/*.md → load_all_documents() → ChromaDB embedding → collection
    ↓
search(query, top_k, sources?) → [ {content, metadata, score} ]
    ↓
AgentScope Tool (search_knowledge_base) → LLM
```

---

## 八、文件上传模块

| 功能 | 核心文件 | 说明 |
|------|----------|------|
| 头像上传 | `apps/ai_assistant/views/file_views.py:74` | Base64 → data URI 存入 DB，不依赖文件系统 |
| 文件解析上传 | `apps/ai_assistant/views/file_views.py:100` | 21 种格式，20MB 上限，解析后立即清理临时文件 |

**API 端点**：
```
POST /api/ai/upload-avatar     # 头像上传
POST /api/ai/upload-file       # 文件解析上传
```

**支持的文件格式**：
- 文本类：txt, log, json, xml, csv, py, js, html, css, yaml, yml, md, markdown
- 文档类：docx（python-docx）, xlsx（openpyxl）, pdf（PyMuPDF）

---

## 九、任务看板模块

| 功能 | 核心文件 | 说明 |
|------|----------|------|
| 对话任务历史 | `apps/ai_assistant/views/conversation_views.py:138` | 通过 TestSOP 关联的 run_id 查询 TestRunRecord |
| 工作台任务便签 | `apps/ai_assistant/views/conversation_views.py:225` | 跨对话聚合 ai-task-* + case-gen-* 任务，按状态过滤 |
| 任务详情 | `apps/ai_assistant/views/conversation_views.py:258` | 单个 run_id 的详细信息 |

**API 端点**：
```
GET /api/ai/conversations/{id}/tasks            # 对话关联任务
GET /api/ai/conversations/{id}/tasks/{run_id}   # 任务详情
GET /api/ai/tasks?status=pending|running|...    # 工作台任务便签
```

**任务类型识别**：
- `ai-task-*` → execution（测试执行任务）
- `case-gen-*` → case_generation（用例生成任务）

---

## 十、AgentScope 服务层

| 功能 | 核心文件 | 说明 |
|------|----------|------|
| FastAPI 应用创建 | `agentscope_service/app.py:43` | Redis 预检 → Storage + MessageBus + WorkspaceManager 装配 |
| 业务工具构建 | `agentscope_service/tools/factory.py:96` | 从 Django HTTP 拉取 schemas → 按 Agent 配置过滤 → 动态创建 PlatformTool 子类 |
| 平台工具执行 | `agentscope_service/tools/platform_tool.py:51` | HTTP POST 到 Django 网关，JWT 鉴权，结果格式化 |
| 可过滤工作区 | `agentscope_service/filterable_workspace.py` | 6 项内置技能（Bash/Edit/Glob/Grep/Read/Write）按 Agent 配置过滤 |
| 工作区管理器 | `agentscope_service/workspace_manager.py` | Monkey-patch 注入技能过滤 + 60s TTL 缓存 |
| 子 Agent 模板 | `agentscope_service/teams/templates.py` | 自定义多 Agent 协作模板 |

### 内置工作区技能（可开关）

| 技能名 | 类 | 说明 |
|--------|---|------|
| Bash | `agentscope.tool.Bash` | Shell 命令执行 |
| Edit | `agentscope.tool.Edit` | 文件精确编辑 |
| Glob | `agentscope.tool.Glob` | 文件名模式匹配 |
| Grep | `agentscope.tool.Grep` | 文件内容搜索 |
| Read | `agentscope.tool.Read` | 文件读取 |
| Write | `agentscope.tool.Write` | 文件写入 |

### 工具调用全链路

```
LLM 发起 tool_call
  → AgentScope PlatformTool.call(**kwargs)
    → HTTP POST /api/ai/tools/{module}/{action}  (JWT 鉴权)
      → Django tool_gateway.py
        → resolve(module, action) 查找 handler
          → handler(user_id, **kwargs)
            → 调用各 App 的 api.py 函数
              → ORM 读写
            → 返回 JSON
          → _serialize_result() ORM → dict
        → JsonResponse({ok, data})
      → PlatformTool._format_result()
    → ToolChunk → LLM
```

---

## 十一、数据安全与权限

| 功能 | 核心文件 | 说明 |
|------|----------|------|
| API Key 加密存储 | `apps/ai_assistant/api.py:98` | Fernet 加密（SHA256(SECRET_KEY) 派生密钥） |
| API Key 解密 | `apps/ai_assistant/api.py:105` | 解密失败返回空字符串不崩溃 |
| API Key 脱敏展示 | `apps/ai_assistant/api.py:115` | `sk-***xxxx` 格式 |
| 一次性查看控制 | `apps/ai_assistant/views/agent_views.py:329` | key_revealed 标记，首次后只返回脱敏值 |
| 掩码更新保护 | `apps/ai_assistant/views/agent_views.py:254` | `***` 掩码跳过更新保留原值 |
| 列表脱敏 | `apps/ai_assistant/views/agent_views.py:56` | list_agents 不返回 api_key 字段 |
| Owner 权限控制 | `apps/ai_assistant/permissions.py` | Agent/Conversation 增删改查权限，legacy null-owner 共享 |
| Provider URL 安全校验 | `apps/ai_assistant/agent_scope/provider_registry.py:61` | 阻止 localhost，生产强制 HTTPS，非 custom 走白名单 |

### 权限检查矩阵

| 操作 | 检查函数 | 规则 |
|------|----------|------|
| Agent 列表 | `filter_agents_for_user` | owned + legacy(null) |
| Agent 详情 | `check_agent_owner` | owner 匹配 |
| Agent 创建 | `check_can_create_agent` | 已认证即可 |
| Agent 更新 | `check_can_update_agent` | owner 匹配 |
| Agent 删除 | `check_can_delete_agent` | owner 匹配 |
| 对话列表 | `filter_conversations_for_user` | owned + legacy(null) |
| 对话操作 | `check_conversation_access` | conv.owner + agent.owner 双重校验 |

---

## 十二、跨模块 API（防火墙 #2 写操作收敛）

`apps/ai_assistant/api.py` 通过 `__all__` 白名单对外暴露：

```python
# Agent 查询（只读）
get_agent(agent_id) → AIAgent | None
get_agent_by_scope_id(scope_id) → AIAgent | None
list_active_agents() → list[dict]

# 对话操作
get_conversation(conv_id) → AIConversation | None
get_or_create_conversation(agent, title) → (AIConversation, bool)

# 消息写入
save_message(conversation_id, role, content, ...) → AIMessage

# 加密工具
encrypt_key(plain) → str
decrypt_key(encrypted) → str
mask_key(key) → str
```

### 调用方协议

| 调用方 | 路径 | 协议 |
|--------|------|------|
| 前端 | `Vue → HTTP → Django View → api.py → ORM` | JWT Bearer |
| AgentScope Tool | `LLM → PlatformTool → HTTP → Django 网关 → handler → api.py → ORM` | JWT（同进程 HTTP） |
| Django Admin | 直连 ORM | 管理员专用 |

---

## 十三、系统提示词模板

`apps/ai_assistant/agent_scope/system_prompt.py` — 140 行中文业务提示词：

1. **平台能力声明**：设备池 / 元素定位 / 用例管理 / 测试执行 / 知识库 / 报告生成
2. **工具使用原则**：数据必须通过工具获取、空结果如实告知、写操作需确认
3. **五步智能用例生成流程**：
   - **Step 1** — 识别用例类型（ui_automation / web_automation / storage / api_testing）
   - **Step 2** — 创建任务卡片
   - **Step 3** — 探索与规划（每种类型有差异化的探索策略，含需求分析→状态机设计→场景路径设计）
   - **Step 4** — 目录与文件规划
   - **Step 5** — 导入数据 + 进度更新
4. **完整示例**：登录功能业务测试用例的端到端生成示例

---

## 十四、数据库表总览

| 表名 | Model | 说明 | 行数参考 |
|------|-------|------|----------|
| `ai_agents` | AIAgent | 智能体配置 | ~40 字段 |
| `ai_tools` | AITool | 单智能体工具配置（MCP/Skill） | — |
| `ai_shared_tools` | AISharedTool | 共享工具箱 | — |
| `ai_conversations` | AIConversation | 对话记录 | — |
| `ai_messages` | AIMessage | 消息记录（含 blocks） | — |
| `ai_tasks` | AITask | Agent 任务 | — |
| `ai_execution_logs` | AIExecutionLog | 执行日志 | — |

---

## 十五、文件清单

### Django 层 (`apps/ai_assistant/`)

```
apps/ai_assistant/
├── models.py              # 7 个 Model（Agent/Tool/SharedTool/Conversation/Message/Task/Log）
├── api.py                 # 跨模块公共 API（__all__ 白名单）
├── serializers.py         # 输入校验（Agent/Message/Conversation/Rename/ModelDetect）
├── permissions.py         # 权限检查 + 用户过滤
├── decorators.py          # @require_auth 装饰器
├── urls.py                # 50+ URL 路由
├── upload_cleanup.py      # 上传文件清理
├── views/
│   ├── auth_views.py      # 认证（login/register/refresh/logout/me）
│   ├── agent_views.py     # Agent CRUD + 注册 + 健康检查 + 提示词/技能
│   ├── conversation_views.py  # 对话/消息 CRUD + 任务看板
│   ├── hitl_views.py      # HITL + AgentScope 会话创建
│   ├── model_views.py     # 模型探测 + 连接测试
│   ├── tool_views.py      # MCP/Skill 单 Agent 管理
│   ├── tool_gateway.py    # AgentScope ↔ Django 工具网关
│   ├── toolbox_views.py   # 共享工具箱
│   ├── knowledge_views.py # ChromaDB 知识库管理
│   ├── file_views.py      # 头像/文件上传
│   └── common.py          # AgentScope HTTP 调用 + 凭证创建
├── agent_scope/
│   ├── system_prompt.py   # 默认系统提示词（140 行业务模板）
│   ├── provider_registry.py  # LLM 提供商注册表 + URL 校验
│   ├── tool_registry.py   # 平台工具注册表（handler + schema）
│   └── rag_service.py     # ChromaDB 向量存储 + 搜索
└── migrations/            # 17 个迁移文件
```

### AgentScope 服务层 (`agentscope_service/`)

```
agentscope_service/
├── app.py                     # FastAPI 应用创建入口
├── auth.py                    # JWT 鉴权覆盖
├── agent_factory.py           # 系统提示词兼容桥接
├── workspace_manager.py       # FilterableLocalWorkspaceManager
├── filterable_workspace.py    # 6 项技能可过滤工作区
├── tools/
│   ├── factory.py             # 业务工具构建 + 按 Agent 过滤
│   ├── platform_tool.py       # PlatformTool 类（HTTP 代理执行）
│   └── tool_context.py        # 工具执行上下文
└── teams/
    ├── leader.py              # Leader Agent 编排
    └── templates.py           # 子 Agent 模板
```
