# AgentScope Tools — Android-AutoTests

> **规则**：开发新的 AgentScope 功能前，必须先阅读 [AgentScope 2.0.3 开发者文档](https://docs.agentscope.io/versions/2.0.3/zh)，理解 API 使用方法后再设计执行方案。建议从 [Message & Event](https://docs.agentscope.io/versions/2.0.3/zh/building-blocks/message-and-event.md) 开始。
>
> **文档地址**：https://docs.agentscope.io/versions/2.0.3/zh

## 项目已使用的 AgentScope 功能

| 模块 | API | 用途 |
|------|-----|------|
| **应用框架** | `create_app()` `RedisStorage` `RedisMessageBus` `LocalWorkspaceManager` | FastAPI 应用工厂 + Redis 会话存储/消息总线 + 本地工作区 |
| **Agent** | `Agent(name, system_prompt, model, toolkit)` + `reply_stream()` | 构建对话 Agent，通过 SSE 事件流返回响应 |
| **模型** | `DashScopeChatModel` `OpenAIChatModel` | 阿里百炼 / OpenAI / Anthropic / 自定义兼容提供商 |
| **凭证** | `DashScopeCredential` `OpenAICredential` | API Key 管理，加密存储于 Django DB |
| **Tool 基类** | `ToolBase` `ToolChunk` | 所有业务 Tool 继承 `ToolBase`，流式输出用 `ToolChunk` |
| **Plan 工具** | `TaskCreate` `TaskGet` `TaskList` `TaskUpdate` | AgentScope 内置子任务追踪，基于 `agent.state.tasks_context` 跨 ReAct 轮次保持 |
| **消息** | `TextBlock` `HintBlock` | Tool 返回值中构造结构化文本/提示消息 |
| **权限** | `PermissionDecision` `PermissionBehavior` `PermissionContext` | Tool 执行前后的权限决策（允许/拒绝/需确认） |
| **Agent Team** | `SubAgentTemplate` | 多个角色模板，按 type 字段区分 |
| **鉴权** | `dependency_overrides[get_current_user_id]` | 用项目 JWT 验证替换 AgentScope 默认 X-User-ID |
| **知识库** | ChromaDB（自建，非 AgentScope 内置） | 向量检索 RAG，通过自定义 Tool 接入 |

> **核心模式**：项目通过 `extra_agent_tools=build_business_tools` 将 Django ORM 操作封装为 AgentScope Tool，LLM 通过 Function Calling 自动选择工具。Agent 本身不直接访问数据库，所有平台操作必经 Tool 层。

## Tool 清单

> **获取完整 Tool 列表**：Read `agentscope_service/tools/factory.py` → `_ALL_BUSINESS_TOOLS` 列表。每个 Tool 的 `name`/`description`/`input_schema` 在其类定义中。Plan Tool 是 AgentScope 框架内置的 (TaskCreate/Get/List/Update)，基于 `agent.state.tasks_context`。

## 新增 Tool 流程

在 `agentscope_service/tools/{domain}_tools.py` 新增 ToolBase 子类 → 在 `factory.py` 注册。

## 文件结构

> `ls agentscope_service/tools/` — 按 domain 拆分（`element_tools.py`、`case_tools.py`、`task_tools.py` 等），`factory.py` 为注册中心。
