# AI 助手模块化重构方案

> 日期：2026-07-13 · 模块：ai_assistant / agentscope_service / 前端 AI 助手 · 目标：三层解耦

---

## 一、现状问题

| 层 | 文件 | 行数 | 问题 |
|----|------|:--:|------|
| Django views | `views.py` | ~1200 | 28 端点混在一个文件：Auth + Agent CRUD + 对话 + 消息 + 文件上传 + 模型检测 + AgentScope 注册 + SSE + 头像 + HITL |
| 前端 ChatView | `ChatView.vue` | ~2800 | SSE 流处理 + 消息渲染 + Tool 可视化 + HITL 确认 + 文件上传 + Mermaid 图表 + 任务卡片 + KB 检索 全耦合 |
| Tool 工厂 | `factory.py` | ~70 | 全量注入 25 Tool，忽略 agent 级 `ai_tools` 配置 |
| 权限 | `permissions.py` | 完整实现 | 从未被 views.py 调用 |
| 序列化 | `serializers.py` | 完整实现 | 从未被 views.py 使用 |

---

## 二、Django views 拆分

`apps/ai_assistant/views.py` → 按子域拆为 6 个文件：

```
apps/ai_assistant/
├── views/
│   ├── __init__.py          # 汇总导出
│   ├── auth_views.py        # login, register, refresh, logout, me
│   ├── agent_views.py       # CRUD + list + health + test + register-scope
│   ├── conversation_views.py # create, list, rename, delete, messages, send, stream, save-message
│   ├── file_views.py        # upload-avatar, serve-avatar, upload-file
│   ├── model_views.py       # detect-models, list-available-models
│   └── hitl_views.py        # create-scope-session, confirm-result
├── permissions.py           # 接入 views，每个 view 入口调权限检查
├── serializers.py           # 接入 views，统一输入校验 + 输出格式化
└── urls.py                  # 路由指向 views/ 子模块
```

**收益**：单文件 < 250 行；新增端点明确归属哪个子域；权限和序列化器真正发挥作用。

---

## 三、前端 ChatView 拆分

`ChatView.vue` (~2800 行) → 1 主组件 + 8 子组件 + 4 composables：

### 3.1 子组件拆分

```
frontend/src/modules/ai-assistant/
├── ChatView.vue                  # 主框架 ~300 行：布局 + Tab 切换 + 消息列表
├── components/
│   ├── MessageBubble.vue         # 单条消息气泡（user/assistant/system）
│   ├── ThinkingBlock.vue         # 思考过程折叠面板
│   ├── ToolCallCard.vue          # 工具调用卡片（参数 + 结果）
│   ├── HintCard.vue              # SOP 状态卡片 / 任务卡片
│   ├── ConfirmDialog.vue         # HITL 确认弹窗
│   ├── FileUploader.vue          # 文件上传区域
│   ├── MermaidRenderer.vue       # Mermaid 图表渲染
│   └── ChatInput.vue             # 输入框 + 发送 + 停止
├── composables/
│   ├── useSSE.js                 # SSE 流连接/重连/事件解析
│   ├── useMessageStore.js        # 消息列表状态 + 持久化
│   ├── useToolCalls.js           # Tool 调用状态跟踪
│   └── useConversation.js        # 对话管理（创建/切换/重命名/删除）
```

### 3.2 数据流

```
ChatView (布局 + 路由参数)
  ├── useConversation()    → 当前对话 ID / 列表
  ├── useSSE(convId)       → SSE 连接 + 事件回调
  │     ├── onTextDelta    → useMessageStore.append()
  │     ├── onToolCall     → useToolCalls.start()
  │     ├── onToolResult   → useToolCalls.finish()
  │     └── onConfirmReq   → ConfirmDialog.show()
  ├── useMessageStore()    → messages[] (共享状态)
  └── useToolCalls()       → toolCalls[] (共享状态)
```

**收益**：每个文件 < 400 行；composable 可独立测试；SSE 逻辑不再与 UI 耦合。

---

## 四、Tool 工厂改造

`factory.py` 改为按 agent 配置注入：

```python
# 改造前（全量注入，忽略 agent 配置）
def build_business_tools(user_id, agent_id, session_id):
    return list(_ALL_BUSINESS_TOOLS)  # 始终 25 个

# 改造后（按 agent 的 ai_tools 表过滤 + 注入 user_id）
def build_business_tools(user_id, agent_id, session_id):
    agent = AIAgent.objects.get(id=agent_id)
    enabled_names = set(
        agent.tools.filter(enabled=True).values_list('name', flat=True)
    )
    selected = [t for t in _ALL_BUSINESS_TOOLS if t.name in enabled_names]
    for tool in selected:
        tool._user_id = user_id          # 注入用户上下文
        tool._session_id = session_id
    return selected
```

**Tool 权限改造**：每个 Tool 的 `check_permissions` 从无条件 `ALLOW` 改为：

```python
async def check_permissions(self, tool_input, context):
    if self.is_read_only:
        return PermissionDecision(behavior=PermissionBehavior.ALLOW)
    # 写操作：验证用户是否有权操作目标资源
    return PermissionDecision(
        behavior=PermissionBehavior.ALLOW if self._user_id else PermissionBehavior.DENY,
        reason="需登录"
    )
```

**收益**：agent 配置的 tool 选择真正生效；Tool 获知调用者身份；权限框架不空转。

---

## 五、公共代码去重

### 5.1 Provider → BaseURL 映射

当前在 5 处重复定义（`views.py`、`agent_factory.py` 等），抽取为：

```python
# agentscope_service/provider_registry.py
PROVIDER_DEFAULTS = {
    "dashscope":  {"base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "credential": "dashscope"},
    "openai":     {"base_url": "https://api.openai.com/v1",                         "credential": "openai"},
    "anthropic":  {"base_url": "https://api.anthropic.com",                         "credential": "openai"},
    "custom":     {"base_url": "",                                                   "credential": "openai"},
}

def get_provider_config(provider, base_url_override=""):
    defaults = PROVIDER_DEFAULTS.get(provider, {})
    return {
        "base_url": base_url_override or defaults.get("base_url", ""),
        "credential_type": defaults.get("credential", "openai"),
    }
```

### 5.2 JWT 工具统一

`shared/auth/jwt_auth.py` 已被 Django 和 AgentScope 共享，但 `config/agentscope_config.py` 和 `agentscope_service/auth.py` 各自有独立配置。统一为一个入口：

```python
# config/agentscope_config.py 已存在，确保所有 AgentScope 侧读取同一来源
from shared.auth.jwt_auth import JWTConfig, verify_token, create_access_token
```

---

## 六、分阶段实施

| 阶段 | 内容 | 风险 |
|:--:|------|:--:|
| **Phase 1** | `permissions.py` + `serializers.py` 接入现有 views | 低 — 纯增量 |
| **Phase 2** | views 拆分为 6 个子模块 + urls 更新 | 中 — 需回归测试 28 端点 |
| **Phase 3** | ChatView 拆分为 8 子组件 + 4 composables | 中 — SSE 流逻辑需仔细迁移 |
| **Phase 4** | Tool 工厂改造（agent 级配置 + user_id 注入） | 中 — 影响所有 Tool 调用 |
| **Phase 5** | Provider 映射去重 + JWT 配置统一 | 低 — 纯重构 |

---

## 七、文件变更清单

| 文件 | 操作 |
|------|------|
| `apps/ai_assistant/views.py` | 拆为 `views/` 下 6 个文件 |
| `apps/ai_assistant/urls.py` | 路由指向新 views 子模块 |
| `apps/ai_assistant/permissions.py` | 接入 views，每个写操作调权限检查 |
| `apps/ai_assistant/serializers.py` | 接入 views，统一校验和格式化 |
| `frontend/.../ChatView.vue` | 缩减到 ~300 行主框架 |
| `frontend/.../components/` | 新建 8 个子组件 |
| `frontend/.../composables/` | 新建 4 个 composable |
| `agentscope_service/tools/factory.py` | 按 agent 配置过滤 + 注入 user_id |
| `agentscope_service/tools/*.py` | 各 Tool 的 check_permissions 改为检查 user_id |
| `agentscope_service/provider_registry.py` | **新建** — 统一 provider 映射 |
