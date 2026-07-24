# AI Engine Rules — Android-AutoTests

## 技术栈

AgentScope 2.0 + FastAPI + Uvicorn + Redis + ChromaDB

## 服务架构

```
run_agentscope.py          # 独立启动入口（uvicorn）
    ↓
agentscope_service/app.py  # create_agentscope_app()
    ↓
agentscope.app.create_app( # AgentScope 框架工厂
    storage=RedisStorage,          # 会话/Agent 状态
    message_bus=RedisMessageBus,   # 流式消息推送
    workspace_manager=LocalWorkspaceManager,  # 工作区文件
    extra_agent_tools=build_business_tools,   # 业务 Tool 注入
    custom_subagent_templates=SUB_AGENT_TEMPLATES,  # Agent Team
)
```

## Agent 创建流程

```
Django AIAgent (ai_agents 表)
    ↓ agent_factory.py: build_agent_from_db()
    ├── 解密 api_key
    ├── 选择 Model: DashScopeChatModel / OpenAIChatModel
    ├── 选择 Credential: DashScopeCredential / OpenAICredential
    ├── 构建 system_prompt: 平台约束 + SOP 四阶段工作流 + 用户自定义
    └── 返回 Agent(name, system_prompt, model, toolkit=None)
    ↓
extra_agent_tools factory 注入业务 toolkit
    ↓
Agent 就绪 → reply_stream() 处理对话
```

## Model 提供商映射

| provider | Model 类 | Credential 类 | 默认模型 |
|----------|---------|--------------|---------|
| `dashscope` | `DashScopeChatModel` | `DashScopeCredential` | `qwen-max` |
| `openai` | `OpenAIChatModel` | `OpenAICredential` | `gpt-4o` |
| `anthropic` | `OpenAIChatModel` | `OpenAICredential` | — |
| `custom` | `OpenAIChatModel` | `OpenAICredential` | — |

> Anthropic 和 Custom 走 OpenAI-compatible 协议，通过 `base_url` 区分。

## Tool 开发规则

### 新建 Tool 的步骤

1. 在 `agentscope_service/tools/{domain}_tools.py` 中创建 `ToolBase` 子类
2. 在 `agentscope_service/tools/factory.py` 中 `_ALL_BUSINESS_TOOLS` 列表注册实例

### Tool 基类模板

```python
from agentscope.tool import ToolBase, ToolChunk
from agentscope.permission import PermissionDecision, PermissionBehavior, PermissionContext
from agentscope.message import TextBlock

class MyNewTool(ToolBase):
    name = "my_new_tool"
    description = "简短描述工具功能，LLM 据此选择工具"
    input_schema = {
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "参数说明"},
        },
        "required": ["param1"],
    }
    is_concurrency_safe = False  # 写操作设为 False
    is_read_only = False         # 有副作用设为 False

    async def check_permissions(self, tool_input, context):
        return PermissionDecision(
            behavior=PermissionBehavior.ALLOW,
            reason="所有用户可调用"
        )

    async def call(self, params: dict) -> ToolChunk:
        result = await run_sync(some_django_operation, params)
        return ToolChunk(
            content=[TextBlock(type="text", text=json.dumps(result))]
        )
```

### Tool 开发约束

| 规则 | 说明 |
|------|------|
| 必须继承 `ToolBase` | 框架通过基类发现和注册 |
| 必须有 `name` `description` `input_schema` | LLM Function Calling 三要素 |
| 读 Tool 设 `is_read_only=True` | 框架借此判断是否需要用户确认 |
| 写 Tool 必须走 Django `api.py` | 禁止 Tool 内直接 ORM 写入 |
| 返回值用 `ToolChunk` | 包装 `TextBlock` 或 `HintBlock` |
| 异步桥接 `run_sync()` | 封装 `sync_to_async`，8s 超时 |

## Agent Team 模板

```python
from agentscope.app._types import SubAgentTemplate

SubAgentTemplate(
    type="element-inspector",    # 唯一标识
    description="...",            # Leader 分配任务时的参考
    system_prompt_template="...", # 角色系统提示词
)
```

> 预设角色列表：Read `agentscope_service/teams/` → `SubAgentTemplate.type` 字段。

## 鉴权集成

```python
# app.py
app.dependency_overrides[default_dep] = get_current_user_id
```

AgentScope 默认通过 `X-User-ID` header 识别用户 → 替换为 JWT Bearer token 验证（与 Django 共享 `SECRET_KEY`）。

## RAG 知识库

| 组件 | 技术 | 位置 |
|------|------|------|
| 向量存储 | ChromaDB PersistentClient | `data/chromadb/` |
| Collection | `project_knowledge` | `dev_docs/` 下 `.md` 文件 + 步骤类型参考 |
| 检索接口 | `KnowledgeBaseSearchTool` → `document_store.search()` | `tools/rag_tool.py` |
| 初始化 | `python agentscope_service/rag/init_kb.py` | 首次运行 |

## Redis 依赖

| 用途 | 组件 |
|------|------|
| Agent 状态存储 | `RedisStorage` |
| 实时消息推送 | `RedisMessageBus` |
| Django Channels 后端 | `channels_redis` |

> **Redis 不可用时**：AgentScope 无法启动，AI 对话自动降级到 Django 阻塞模式。
