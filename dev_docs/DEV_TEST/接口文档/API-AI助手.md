# API-AI助手 — /api/ai/*

> AI 助手模块（`apps/ai_assistant`）接口全集。Batch 1-3 已迁移到 DRF（Agent / 对话 / 工具箱 / 知识库 / 上传 / 平台配置 / 任务），
> 豁免工具网关（legacy 函数视图）。SSE 主对话（`chat_stream`）与 HITL（`hitl_views`）已随「主对话移除」删除。
> 真相源：`apps/ai_assistant/urls.py` + `views_drf.py` + `views_toolbox_drf.py` + `views_knowledge_drf.py` + `views_upload_drf.py` + `views/tool_gateway.py` + `serializers.py` + `models.py` + `api.py`。

## 1. 总览

> router 使用 `trailing_slash=False`：全部路径**无尾斜杠**。挂载前缀 `/api/ai/`（见 `config/urls.py`）。

| 接口 | 方法 | 鉴权 | 说明 |
|---|---|---|---|
| **agents 组** | | | |
| Agent 列表 | GET /api/ai/agents/ | 需登录(Bearer) | 当前用户可见的智能体列表 |
| Agent 创建 | POST /api/ai/agents/create/ | 需登录(Bearer) | 新建智能体（仅超管） |
| Agent 详情 | GET /api/ai/agents/{id} | 需登录(Bearer) | 单智能体详情（api_key 脱敏） |
| Agent 更新 | POST /api/ai/agents/{id}/update | 需登录(Bearer) | 更新配置（仅超管） |
| Agent 删除 | POST /api/ai/agents/{id}/delete | 需登录(Bearer) | 删除（仅超管，级联） |
| 一次性查看 Key | POST /api/ai/agents/{id}/reveal-key | 需登录(Bearer) | 一次性查看 api_key（仅超管） |
| 连接测试 | POST /api/ai/agents/{id}/test | 需登录(Bearer) | 测连通（owner；可按线路） |
| 缓存模型列表 | GET /api/ai/agents/{id}/models | 需登录(Bearer) | 缓存可用模型列表 |
| Agent 对话列表 | GET /api/ai/agents/{id}/conversations | 需登录(Bearer) | 某智能体下对话 |
| Agent 创建对话 | POST /api/ai/agents/{id}/conversations/create | 需登录(Bearer) | 新建对话 |
| Agent 健康检查 | GET /api/ai/agents/health/ | 需登录(Bearer) | 当前用户 active Agent 健康 |
| 模型探测 | POST /api/ai/models/detect/ | 需登录(Bearer) | 按 provider/base_url/key 探测模型 |
| 平台工具列表 | GET /api/ai/available-tools/ | 需登录(Bearer) | 平台业务工具（按分类含启停态） |
| workspace 技能列表 | GET /api/ai/available-skills/ | 需登录(Bearer) | 已移除，返回空 |
| **conversations 组** | | | |
| 消息列表 | GET /api/ai/conversations/{id}/messages | 需登录(Bearer) | 对话消息 |
| 保存消息 | POST /api/ai/conversations/{id}/save-message | 需登录(Bearer) | 写入一条消息 |
| 对话重命名 | POST /api/ai/conversations/{id}/rename | 需登录(Bearer) | 修改标题 |
| 对话删除 | POST /api/ai/conversations/{id}/delete | 需登录(Bearer) | 删除（级联消息） |
| 对话任务历史 | GET /api/ai/conversations/{id}/tasks | 需登录(Bearer) | ai-task-*/case-gen-* 运行记录 |
| 对话任务详情 | GET /api/ai/conversations/{id}/tasks/{run_id} | 需登录(Bearer) | 单条运行详情 |
| **tasks 组** | | | |
| 任务便签看板 | GET /api/ai/tasks/ | 需登录(Bearer) | 工作台 ai-task-*/case-gen-* 看板 |
| 任务提交 | POST /api/ai/tasks/submit/ | 需登录(Bearer) | 提交并异步执行 |
| 任务发布列表 | GET /api/ai/agent-tasks/ | 需登录(Bearer) | AITask 任务发布列表（result 为短摘要） |
| 任务发布详情 | GET /api/ai/agent-tasks/{id} | 需登录(Bearer) | 过程日志（plans / log / usage） |
| 任务发布删除 | POST /api/ai/agent-tasks/{id}/delete | 需登录(Bearer) | 删除任务发布记录 |
| 任务发布清空 | POST /api/ai/agent-tasks/clear/ | 需登录(Bearer) | 调试：清空全部任务 |
| **toolbox 组** | | | |
| 工具箱列表 | GET /api/ai/toolbox/ | 需登录(Bearer) | 共享工具箱项（含 enabled） |
| 工具箱新增 | POST /api/ai/toolbox/create/ | 需登录(Bearer) | 新增 mcp/extension |
| 工具箱更新 | POST /api/ai/toolbox/{id}/update | 需登录(Bearer) | 部分更新 |
| 工具箱删除 | POST /api/ai/toolbox/{id}/delete | 需登录(Bearer) | 删除（skill 清目录） |
| 工具箱启停 | POST /api/ai/toolbox/{id}/toggle | 需登录(Bearer) | 启停共享项 |
| 上传共享 Skill | POST /api/ai/toolbox/upload-skill/ | 需登录(Bearer) | multipart 上传 skill 文件夹 |
| **knowledge 组** | | | |
| 知识库状态 | GET /api/ai/knowledge/status/ | 需登录(Bearer) | 已索引文档数（向量库） |
| 知识库文档列表 | GET /api/ai/knowledge/documents/ | 需登录(Bearer) | 扫描 data/rag_datas |
| 知识库文档预览 | GET /api/ai/knowledge/documents/preview/ | 需登录(Bearer) | md/txt 原文；docx/pdf 旁路转 md |
| 知识库重建索引 | POST /api/ai/knowledge/reindex/ | 需登录(Bearer) | 索引 data/rag_datas/**/*.md |
| 知识库添加文档 | POST /api/ai/knowledge/documents/add/ | 需登录(Bearer) | multipart 上传到 data/rag_datas |
| **uploads 组** | | | |
| 头像上传 | POST /api/ai/upload-avatar/ | 需登录(Bearer) | base64 → data URI |
| 文件上传 | POST /api/ai/upload-file/ | 需登录(Bearer) | multipart 上传并解析 |
| **platform 组** | | | |
| 平台配置读取 | GET /api/ai/platform-config/ | 需登录(Bearer) | 平台唯一智能体能力配置 |
| 平台配置更新 | POST /api/ai/platform-config/update/ | 需登录(Bearer) | 更新（仅超管） |
| 设备提示词读取 | GET /api/ai/device-prompts/ | 需登录(Bearer) | 规划/执行/验收系统提示词 |
| 设备提示词更新 | POST /api/ai/device-prompts/update/ | 需登录(Bearer) | 更新三份提示词（仅超管） |
| 平台工具启停 | POST /api/ai/platform-tools/toggle/ | 需登录(Bearer) | 全局启停（仅超管） |
| 平台工具调试 schema | GET /api/ai/platform-tools/{name} | 需登录(Bearer) | 入参 schema（剥 user_id；设备参数附候选） |
| 平台工具调试调用 | POST /api/ai/platform-tools/{name}/invoke | 需登录(Bearer) | 真实调用；写工具仅超管 |
| **legacy tool gateway** | | | |
| 工具 schema | GET /api/ai/tools/schemas/ | 内部令牌 | 全部工具定义（服务间） |
| Agent 工具配置 | GET /api/ai/tools/agent-config/{agent_id} | 内部令牌 | per-agent 工具/技能/知识配置 |
| 工具执行 | POST /api/ai/tools/{module}/{action} | 内部令牌 | 执行业务工具（服务间） |

## 2. 通用约定

- **无尾斜杠**：所有路径均无尾斜杠（`trailing_slash=False`）。
- **信封分两类**：
  - **DRF 迁移端点**（§3~§9，ViewSet / APIView 返回 `Response`）：经全局 `EnvelopeJSONRenderer` 包裹，成功 `{status: true, data: {...}}`，失败（4xx/5xx）`{status: false, message: "..."}`。
  - **legacy 工具网关**（§10，函数视图返回 `JsonResponse`）：不走 `EnvelopeJSONRenderer`，视图内手动返回 `{status: true, data}` / `{status: false, message}`（外层形状相同，但 `data` 已是最终结果，不再二次包裹）。
- **鉴权**：全部需 `Authorization: Bearer <access_token>`，**唯一例外**是 `/api/ai/tools/*` 工具网关 —— 该前缀免 JWT（服务间调用不持有用户令牌），改由 `gateway.internal_token.InternalToolTokenMiddleware` 校验请求头 `X-Internal-Token`（= `settings.AI_TOOL_GATEWAY_TOKEN`）；令牌未配置时该前缀一律 `401`。JWT 中间件先行校验并注入 `request.user_id`，DRF 全局 `IsAuthenticated` 兜底。
- **对象级权限**：Agent 写操作仅超管；读操作「权限检查先于存在性检查 → 不存在资源返回 403」（`Forbidden`）。对话访问按 owner。
- **错误响应**：DRF 端点错误由 `EnvelopeJSONRenderer` 从 `detail`/字段错误抽取成 `{status: false, message}`。字段级校验错误取第一个字段的第一个错误文案。
- 字段命名 **snake_case**；`api_key` 落库 Fernet 加密，读接口按权限脱敏。
- 本模块无文件下载端点（文件上传返回 JSON 内容，不走 `FileResponse`）。

---

## 3. agents 组

### 3.1 Agent 列表接口：GET /api/ai/agents/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 请求 | 无请求体 |

#### 成功响应（200）

```json
{
  "status": true,                       # 请求是否成功，恒为 true
  "data": {
    "agents": [                         # 可见智能体列表
      {
        "id": 1,                        # 智能体 ID
        "name": "默认智能体",            # 名称
        "avatar": "🤖",                 # 头像（emoji 或文本）
        "tags": "设备,UI",              # 标签
        "description": "平台唯一智能体",  # 描述
        "model_provider": "dashscope",  # 模型提供商
        "model_name": "qwen-max",       # 主模型名
        "route_configs": {              # 线路配置（看板展示，无 api_key）
          "device_control": {           # 线路名
            "name": "设备控制",          # 线路展示名
            "avatar": "📱",             # 线路头像
            "planner": {                # 规划角色模型
              "model_name": "qwen-max", # 模型名
              "provider": "dashscope"   # 提供商
            },
            "health": {                 # 线路健康（无则缺省）
              "is_connected": true,     # 是否连通
              "last_checked_at": "",    # 最近检测时间
              "results": {}             # 各角色校验结果
            }
          }
        },
        "status": "active",             # 状态
        "created_at": "2026-01-01 12:00:00"  # 创建时间（字符串）
      }
    ]
  }
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 | 无 Bearer 头 |
| 401 | 登录已过期或令牌无效 | 令牌无效/过期 |

---

### 3.2 Agent 创建接口：POST /api/ai/agents/create/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer)，仅超级管理员 |
| Content-Type | application/json |

#### 请求体（`AgentInputSerializer`，全部字段可选；部分字段有校验）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| name | string | 否 | 名称；提供时不可为空（strip 后非空） |
| avatar | string | 否 | 头像，缺省 🤖 |
| tags | string | 否 | 标签 |
| description | string | 否 | 描述 |
| model_provider | string | 否 | 提供商枚举：dashscope/openai/anthropic/deepseek/gemini/custom；缺省 dashscope |
| model_name | string | 否 | 主模型名，缺省 qwen-max |
| vision_model_name | string | 否 | 视觉模型名 |
| strong_model_name | string | 否 | 强模型名 |
| strong_enabled | boolean | 否 | 强模型短路开关 |
| api_key | string | 否 | API Key（落库加密） |
| base_url | string | 否 | 自定义 base_url（校验协议/主机白名单） |
| enable_knowledge_base | boolean | 否 | 知识库开关 |
| enable_workspace_tools | boolean | 否 | workspace 工具开关 |
| enable_business_tools | boolean | 否 | 业务工具开关 |
| enable_mcp_tools | boolean | 否 | MCP 工具开关 |
| enable_skills | boolean | 否 | 技能开关 |
| status | string | 否 | 状态，缺省 active |
| skills_config | object | 否 | 技能启停配置 {"Bash": true, ...} |
| knowledge_sources | object | 否 | 知识库文档过滤 {"doc:id": true/false} |
| route_configs | object | 否 | 多线路模型配置（api_key 会加密） |
| max_loops | integer | 否 | 工作流内层循环次数，缺省 3 |

#### 成功响应（200）

```json
{
  "status": true,                       # 请求是否成功，恒为 true
  "data": {
    "id": 3                             # 新建智能体 ID
  }
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 403 | Forbidden | 非超级管理员 |
| 400 | Agent 名称不能为空 | name 提供但为空 |
| 400 | 不支持的模型提供商: {provider} | provider 不在枚举内 |
| 400 | base_url 必须使用 http 或 https | 协议非法 |
| 400 | base_url 无效 | 无法解析主机 |
| 400 | 生产环境 base_url 必须使用 https | DEBUG=False 且 http |
| 400 | base_url 不允许指向本机地址 | 主机为 localhost/127.0.0.1 等 |
| 400 | base_url 主机不在 {provider} 提供商白名单内 | 非 custom 且主机不符 |

---

### 3.3 Agent 详情接口：GET /api/ai/agents/{id}

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 请求 | 无请求体；路径 `{id}` 为整数 |

#### 成功响应（200）

```json
{
  "status": true,
  "data": {
    "agent": {
      "id": 1,                          # 智能体 ID
      "name": "默认智能体",
      "avatar": "🤖",
      "tags": "",
      "description": "",
      "model_provider": "dashscope",
      "model_name": "qwen-max",
      "vision_model_name": "",          # 视觉模型名
      "strong_model_name": "",          # 强模型名
      "strong_enabled": false,          # 强模型开关
      "api_key": "sk-***abcd",          # 脱敏 Key（仅超管可见，其余为空串）
      "base_url": "",                   # base_url（仅超管可见）
      "enable_knowledge_base": false,
      "enable_workspace_tools": false,
      "enable_business_tools": false,
      "enable_mcp_tools": false,
      "enable_skills": false,
      "skills_config": {},              # 技能启停配置
      "knowledge_sources": {},          # 知识库文档过滤
      "route_configs": {},              # 线路配置（仅超管返回脱敏+解密视图）
      "max_loops": 3,
      "status": "active",
      "is_connected": false,            # 智能体级连通状态
      "last_checked_at": null,          # 最近检测时间
      "available_models": [],           # 缓存可用模型列表
      "created_at": "2026-01-01 12:00:00"
    }
  }
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 403 | Forbidden | 不可见（非 owner 且非超管共享）或不存在 |
| 404 | not found | `{id}` 非整数 |

> 权限检查先于存在性检查：不可见的资源统一返回 403。

---

### 3.4 Agent 更新接口：POST /api/ai/agents/{id}/update

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer)，仅超级管理员 |
| Content-Type | application/json |

#### 请求体

同 §3.2（`AgentInputSerializer`，全部可选，只更新传入字段）。`api_key` 含 `***` 视为未变更跳过；`route_configs` 含 `***` 的 Key 保留旧加密值。

#### 成功响应（200）

```json
{
  "status": true,
  "data": { "id": 1 }                   # 更新的智能体 ID
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 403 | Forbidden | 非超管 |
| 404 | not found | `{id}` 非整数或超管但资源不存在 |
| 400 | Agent 名称不能为空 / 不支持的模型提供商: {provider} / base_url ... | 同 §3.2 校验 |

---

### 3.5 Agent 删除接口：POST /api/ai/agents/{id}/delete

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer)，仅超级管理员 |
| 请求 | 无请求体 |

#### 成功响应（200）

```json
{
  "status": true,
  "data": {}                            # 空对象，无业务数据
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 403 | Forbidden | 非超管 |
| 404 | not found | `{id}` 非整数或资源不存在 |

> 删除级联其工具 / 对话 / 消息。

---

### 3.6 一次性查看 Key 接口：POST /api/ai/agents/{id}/reveal-key

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer)，仅超级管理员 |
| 请求 | 无请求体 |

#### 成功响应（200）

```json
{
  "status": true,
  "data": {
    "api_key": "sk-xxxxxxxxxxxx",       # 解密后的完整 Key（仅本次返回）
    "revealed": true,                   # 是否首次成功查看
    "hint": "请立即复制保存，此 Key 仅显示一次"
  }
}
```

> 再次调用（已 `revealed`）返回脱敏 Key 且 `revealed: false`、`hint: "API Key 仅支持一次性查看，已过期"`。

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 403 | Forbidden | 非超管 |
| 404 | not found | `{id}` 非整数或不存在 |
| 400 | 未配置 API Key | 未配置 api_key |

---

### 3.7 连接测试接口：POST /api/ai/agents/{id}/test

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer)，owner |
| Content-Type | application/json |

#### 请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| route | string | 否 | 线路 device_control；传则按线路校验，不传则测智能体顶层模型 |

#### 成功响应（200，无 route）

```json
{
  "status": true,
  "data": {
    "connected": true,                  # 是否连通
    "available_models": ["qwen-max"],   # 探测到的可用模型列表
    "message": ""                       # 失败原因，成功为空串
  }
}
```

#### 成功响应（200，有 route）

```json
{
  "status": true,
  "data": {
    "connected": true,                  # 线路整体连通（三角色均连通）
    "results": {                        # 各角色校验结果
      "planner": {
        "connected": true,
        "model_name": "qwen-max",
        "message": ""
      },
      "executor": { "connected": true, "model_name": "qwen-max", "message": "" },
      "verifier": { "connected": true, "model_name": "qwen-max", "message": "" }
    },
    "last_checked": "2026-01-01 12:00:00",  # 检测时间（ISO）
    "message": ""                       # 失败时拼接未连通角色信息
  }
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 403 | Forbidden | 非 owner |
| 404 | not found | `{id}` 非整数或不存在 |

---

### 3.8 缓存模型列表接口：GET /api/ai/agents/{id}/models

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 请求 | 无请求体 |

#### 成功响应（200）

```json
{
  "status": true,
  "data": {
    "models": ["qwen-max", "qwen-plus"],  # 缓存可用模型列表
    "is_connected": true,               # 连通状态
    "last_checked": "2026-01-01 12:00:00"  # 最近检测时间（字符串）
  }
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 403 | Forbidden | 不可见或不存在 |
| 404 | not found | `{id}` 非整数 |

---

### 3.9 Agent 对话列表接口：GET /api/ai/agents/{id}/conversations

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 请求 | 无请求体 |

#### 成功响应（200）

```json
{
  "status": true,
  "data": {
    "conversations": [                  # 按 -updated_at 排序
      {
        "id": 1,                        # 对话 ID
        "title": "新对话",              # 标题
        "status": "active",             # 状态
        "agent_scope_session_id": "",   # AgentScope session ID
        "created_at": "2026-01-01 12:00:00"
      }
    ]
  }
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 403 | Forbidden | agent 不可见或不存在 |
| 404 | not found | `{id}` 非整数 |

---

### 3.10 Agent 创建对话接口：POST /api/ai/agents/{id}/conversations/create

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |

#### 请求体（`ConversationCreateSerializer`）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| title | string | 否 | 标题，缺省「新对话」，截断 500 |

#### 成功响应（200）

```json
{
  "status": true,
  "data": {
    "id": 1,                            # 新对话 ID
    "agent_scope_session_id": ""        # AgentScope session ID（可能为空）
  }
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 403 | Forbidden | agent 不可见或不存在 |
| 404 | not found | `{id}` 非整数 |

---

### 3.11 Agent 健康检查接口：GET /api/ai/agents/health/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 请求 | 无请求体 |

#### 成功响应（200）

```json
{
  "status": true,
  "data": {
    "agents": [                         # 当前用户 active 智能体
      {
        "id": 1,
        "name": "默认智能体",
        "is_connected": true,           # 智能体级连通
        "last_checked": "2026-01-01 12:00:00",
        "routes": {                     # 各线路健康
          "device_control": {
            "is_connected": true,       # 线路连通
            "last_checked": "2026-01-01 12:00:00",
            "results": {                # 各角色校验结果
              "planner": { "connected": true, "model_name": "qwen-max", "message": "" }
            }
          }
        }
      }
    ]
  }
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |

---

### 3.12 模型探测接口：POST /api/ai/models/detect/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |

#### 请求体（`ModelDetectInputSerializer`）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| model_provider | string | 否 | 提供商枚举 |
| base_url | string | 否 | 自定义 base_url |
| api_key | string | 是 | API Key（非空） |

#### 成功响应（200）

```json
{
  "status": true,
  "data": {
    "models": ["qwen-max", "qwen-plus"]  # 探测到的模型 ID 列表
  }
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 400 | API Key 不能为空 | api_key 缺失或空 |
| 400 | 不支持的模型提供商: {provider} | provider 非法 |
| 400 | base_url 必须使用 http 或 https / base_url 无效 / ... | base_url 校验（仅在 provider 提供时） |

> 历史说明：`GET /api/ai/models/detect/` 保持旧 400 语义，返回 `{status: false, message: "agent_id required"}`。

---

### 3.13 平台工具列表接口：GET /api/ai/available-tools/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 请求 | 无请求体 |

#### 成功响应（200）

```json
{
  "status": true,
  "data": {
    "categories": [                     # 按分类聚合
      {
        "key": "设备管理",              # 分类名（设备池台账，不操作手机）
        "icon": "📱",                   # 分类图标
        "color": "#6BCB77",             # 分类颜色（T0 色阶 --color-green-61）
        "tools": [                      # 该分类下工具
          {
            "name": "list_devices",     # 工具名
            "summary": "查询设备...",   # 工具摘要
            "icon": "📱",               # 工具图标
            "read_only": true,          # 是否只读
            "enabled": true             # 全局启用状态
          }
        ]
      },
      {
        "key": "设备控制",              # 分类名（会在手机上产生副作用，可整类停用）
        "icon": "🎮",
        "color": "#F7C948",             # T0 色阶 --color-yellow-63
        "tools": [
          {
            "name": "app_control",      # 启停 App（另有 tap_screen / swipe_screen / press_key / input_text / click_ratio / drag_ratio / xpath_action）
            "summary": "启动或停止指定设备上的 App；每次返回 package/activity。",
            "icon": "🎮",
            "read_only": false,
            "enabled": true
          }
        ]
      },
      {
        "key": "设备信息",              # 分类名（只读，但要连设备取数）
        "icon": "📋",
        "color": "#4ECDC4",             # T0 色阶 --color-teal-49
        "tools": [
          {
            "name": "current_app",      # 只读当前前台（另有 list_apps）
            "summary": "只读设备当前前台 App（package/activity/pid），不改变设备状态。",
            "icon": "📋",
            "read_only": true,
            "enabled": true
          }
        ]
      },
      {
        "key": "视觉识别工具",           # 分类名（OCR 文本与坐标）
        "icon": "🔍",
        "color": "#A78BFA",
        "tools": [
          {
            "name": "ocr_page",         # OCR 识别设备当前页面文本
            "summary": "OCR 识别设备当前页面的文本，返回文本、置信度、原始角点坐标与归一化中心点。",
            "icon": "🔍",
            "read_only": true,          # 只读：无设备副作用
            "enabled": true
          }
        ]
      }
    ]
  }
}
```

> `categories` 恒为 **6 类**，顺序同后端 `TOOL_CATEGORIES`：设备管理（台账 3）/ 设备控制（有手机副作用的 8 个）/ 设备信息（只读连设备 2）/ 设备检查器（1）/ 视觉识别工具（1）/ 页面流工具（2）。分类是工具箱「整类启停」的单位。

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |

---

### 3.14 workspace 技能列表接口：GET /api/ai/available-skills/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 请求 | 无请求体 |

#### 成功响应（200）

```json
{
  "status": true,
  "data": { "skills": [] }              # workspace 技能已移除，恒空
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |

---

## 4. conversations 组

> ConversationViewSet 无 list/retrieve 动作；对话列表经 §3.9 获取。

### 4.1 消息列表接口：GET /api/ai/conversations/{id}/messages

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer)，对话 owner |
| 请求 | 无请求体 |

#### 成功响应（200）

```json
{
  "status": true,
  "data": {
    "messages": [                       # 按 created_at 正序
      {
        "id": 1,                        # 消息 ID
        "role": "user",                 # user/assistant/system
        "content": "你好",              # 文本内容
        "blocks": [],                   # ContentBlock 结构列表
        "reason": "normal",             # normal/exceed_max_iters/stopped/error
        "tool_calls": "",               # 工具调用（原始字符串）
        "tokens": 0,                    # token 数
        "input_tokens": 0,              # 输入 token
        "model_name": "",               # 模型名
        "flow": "",                     # sse/fallback/''（传输方式）
        "created_at": "2026-01-01 12:00:00"
      }
    ]
  }
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 403 | Forbidden | 非 owner 或不存在 |
| 404 | conversation not found | `{id}` 非整数 |

---

### 4.2 保存消息接口：POST /api/ai/conversations/{id}/save-message

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer)，对话 owner |
| Content-Type | application/json |

#### 请求体（`MessageInputSerializer`）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| role | string | 否 | user/assistant/system，缺省 assistant |
| content | string | 否 | 文本内容，缺省空串 |
| blocks | array | 否 | 内容块列表，缺省 [] |
| reason | string | 否 | 结束原因，缺省 normal |
| tokens | integer | 否 | token 数，缺省 0 |
| input_tokens | integer | 否 | 输入 token，缺省 0 |
| model_name | string | 否 | 模型名，缺省空串 |
| flow | string | 否 | 传输方式，仅 sse/空串 |

#### 成功响应（200）

```json
{
  "status": true,
  "data": { "id": 1 }                   # 新消息 ID
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 403 | Forbidden | 非 owner 或不存在 |
| 404 | conversation not found | `{id}` 非整数 |
| 400 | 无效的角色类型 | role 非法 |
| 400 | 消息内容不能为空 | role=user 且 content/blocks 均空 |
| 400 | assistant 消息需要 content 或 blocks | role=assistant 且 content/blocks 均空 |

---

### 4.3 对话重命名接口：POST /api/ai/conversations/{id}/rename

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer)，对话 owner |
| Content-Type | application/json |

#### 请求体（`RenameInputSerializer`）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| title | string | 是 | 新标题，非空，截断 500 |

#### 成功响应（200）

```json
{
  "status": true,
  "data": { "title": "新标题" }          # 更新后的标题
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 403 | Forbidden | 非 owner 或不存在 |
| 404 | conversation not found | `{id}` 非整数 |
| 400 | 标题不能为空 | title 缺失或空 |

---

### 4.4 对话删除接口：POST /api/ai/conversations/{id}/delete

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer)，对话 owner |
| 请求 | 无请求体 |

#### 成功响应（200）

```json
{
  "status": true,
  "data": {}                            # 空对象
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 403 | Forbidden | 非 owner 或不存在 |
| 404 | conversation not found | `{id}` 非整数 |

---

### 4.5 对话任务历史接口：GET /api/ai/conversations/{id}/tasks

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer)，对话 owner |
| 请求 | 无请求体 |

#### 成功响应（200）

```json
{
  "status": true,
  "data": {
    "tasks": [                          # 最多 50 条，按 -id
      {
        "run_id": "ai-task-xxxx",       # 运行 ID
        "title": "任务标题",            # 标题
        "status": "COMPLETED",          # 大写状态
        "task_type": "execution",       # execution/case_generation
        "case_type": "",                # 用例类型
        "case_type_label": "",
        "agent_id": "1",                # 智能体 ID（字符串）
        "agent_name": "默认智能体",
        "device_serial": "",            # 设备序列号
        "device_model": "",
        "cases": [],                    # 用例列表
        "case_titles": [],
        "case_ids": [],
        "loop_count": 1,                # 循环次数
        "progress": { "current": 0, "total": 1 },  # 进度
        "started_at": "2026-01-01 12:00:00",
        "finished_at": null
      }
    ]
  }
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 403 | Forbidden | 非 owner 或不存在 |
| 404 | conversation not found | `{id}` 非整数或不存在 |
| 500 | 查询任务历史失败 | 查询异常 |

---

### 4.6 对话任务详情接口：GET /api/ai/conversations/{id}/tasks/{run_id}

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer)，对话 owner |
| 请求 | 无请求体 |

#### 成功响应（200）

```json
{
  "status": true,
  "data": {
    "task": {
      "run_id": "ai-task-xxxx",
      "status": "COMPLETED",
      "device_serial": "",
      "cases": [],                      # 选中用例
      "loop_count": 1,
      "started_at": "2026-01-01 12:00:00",
      "completed_at": null,             # 完成时间
      "summary": ""                     # 结果摘要
    }
  }
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 403 | Forbidden | 非 owner 或不存在 |
| 404 | task not found | run_id 无对应记录 |
| 500 | 查询任务详情失败 | 查询异常 |

---

## 5. tasks 组

### 5.1 任务便签看板接口：GET /api/ai/tasks/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 请求 | Query 参数 `status` 可选：all/pending/running/completed/failed/stopped（缺省 all） |

#### 成功响应（200）

```json
{
  "status": true,
  "data": {
    "tasks": [                          # ai-task-* / case-gen-*，最多 80 条
      {
        "run_id": "ai-task-xxxx",
        "title": "任务标题",
        "status": "COMPLETED",
        "task_type": "execution",
        "case_type": "",
        "case_type_label": "",
        "agent_id": "1",
        "agent_name": "默认智能体",
        "device_serial": "",
        "device_model": "",
        "cases": [],
        "case_titles": [],
        "case_ids": [],
        "loop_count": 1,
        "progress": { "current": 0, "total": 1 },
        "started_at": "2026-01-01 12:00:00",
        "finished_at": null
      }
    ]
  }
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 500 | 查询 AI 任务列表失败 | 查询异常 |

---

### 5.2 任务提交接口：POST /api/ai/tasks/submit/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |

#### 请求体（`TaskSubmitInputSerializer`）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| goal | string | 是 | 任务目标（非空） |
| attachment | string | 否 | 附件文件路径 |
| device_serial | string | 否 | 指定设备 serial（空则第一台在线） |

#### 成功响应（200）

```json
{
  "status": true,
  "data": {
    "id": 1,                            # 任务 ID
    "status": "running",                # 已标记 running（后台线程异步执行）
    "result": ""                        # 初始为空；运行中经 agent-tasks 详情读增量过程 JSON
  }
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 400 | 任务目标不能为空 | goal 缺失或空 |
| 404 | platform agent not found | 平台唯一智能体不存在 |

> 提交后立即返回。运行中工作流在「规划完成 / 每一轮执行+验收 / 每一个目标完成」检查点把与终态同构的 JSON 写入 `result`（`run.status=running`），不改任务 `status`。终态仍由 `finalize_task` 落 completed/failed + 全量 result + token 用量。

---

### 5.3 任务发布列表接口：GET /api/ai/agent-tasks/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 请求 | 无请求体 |

#### 成功响应（200）

```json
{
  "status": true,
  "data": {
    "tasks": [                          # AITask，最多 100 条，按 -id
      {
        "id": 1,                        # 任务 ID
        "title": "任务标题",            # 标题（goal 前 100 字符）
        "goal": "任务目标",
        "status": "completed",          # pending/running/completed/failed
        "result": "已完成 3 项",       # 短摘要，非整份过程 JSON
        "device_serial": "",
        "created_at": "2026-01-01 12:00:00"
      }
    ]
  }
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |

> 无平台智能体时返回 `{tasks: []}`（不报错）。

---

### 5.4 任务发布删除接口：POST /api/ai/agent-tasks/{id}/delete

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 请求 | 无请求体；路径参数 `id` 为任务 ID |

#### 成功响应（200）

```json
{
  "status": true,
  "data": {}
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 404 | 任务不存在 | 无平台智能体，或任务不属于平台智能体 |

---

### 5.5 任务发布详情接口：GET /api/ai/agent-tasks/{id}

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 请求 | 无请求体；路径参数 `id` 为任务 ID |

#### 成功响应（200）

```json
{
  "status": true,
  "data": {
    "id": 1,
    "title": "打开 govee APP",
    "goal": "打开 govee APP",
    "status": "completed",
    "device_serial": "RF8N21MSW7A",
    "created_at": "2026-09-08 10:17:00",
    "started_at": "2026-09-08 10:17:01",
    "finished_at": "2026-09-08 10:18:20",
    "input_tokens": 0,
    "output_tokens": 0,
    "cache_input_tokens": 0,
    "model_usage": {},
    "deepseek_cost": 0.0,
    "run": {
      "status": "success",
      "summary": "完成 …",
      "plans": [{
        "goal": "启动应用并进入设备页",
        "steps": [
          { "action": "启动 govee", "assert": "前台应用为 govee 首页" },
          { "action": "点击设备入口", "assert": "进入设备列表页" }
        ]
      }],
      "log": [{
        "action": "启动 govee",
        "assert": "前台应用为 govee 首页",
        "loop": 1,
        "executor": { "action": "启动 govee", "result": "PASS", "message": "已启动" },
        "verifier": { "action": "启动 govee", "assert": "前台应用为 govee 首页", "actual": "已在首页", "result": true }
      }],
      "usage": {},
      "models": { "planner": "…", "executor": "…", "verifier": "…", "max_loops": 3 }
    }
  }
}
```

> 运行中即可读到增量 `run.plans` / `run.log` / `run.summary`（如「已规划 N 个步骤」）；`data.status` 仍为 `running`，`run.status` 为 `running`。终态把全量过程写入 `ai_tasks.result`。
> 新协议：`plans[].steps` 为 `{action, assert}`；`log[]` 按步骤重试记录 `executor` / `verifier`（`verifier.result` 为 boolean）。旧任务可能仍是字符串 steps + goal 级 log，前端详情页兼容折叠展示。
> `deepseek_cost` 为 DeepSeek 官方价目（命中/未命中输入 + 输出，高峰 ×2）估算费用（元，4 位小数）。无分模型用量时按 `deepseek-v4-flash` 对任务总量计费；非 DeepSeek 模型不计。

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 404 | 任务不存在 | 无平台智能体，或任务 ID 不存在 |

---

### 5.6 任务发布清空接口：POST /api/ai/agent-tasks/clear/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 请求 | 无请求体 |

调试用：删除平台智能体下全部 `AITask`。

#### 成功响应（200）

```json
{
  "status": true,
  "data": { "deleted": 8 }
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |

---

## 6. toolbox 组

### 6.1 工具箱列表接口：GET /api/ai/toolbox/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 请求 | 无请求体 |

#### 成功响应（200）

```json
{
  "status": true,
  "data": {
    "items": [                          # 按 -updated_at
      {
        "id": 1,                        # 共享项 ID
        "name": "my-skill",             # 名称
        "item_type": "skill",           # skill/mcp/extension
        "description": "3 个文件 — ...",# 描述
        "config_json": "{...}",         # 配置 JSON（字符串）
        "enabled": true,                # 是否启用
        "created_at": "2026-01-01 12:00:00"
      }
    ]
  }
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |

---

### 6.2 工具箱新增接口：POST /api/ai/toolbox/create/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |

#### 请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| name | string | 是 | 名称（非空） |
| item_type | string | 是 | 枚举 mcp / extension |
| description | string | 否 | 描述 |
| config_json | string/object | 否 | 配置，object 会自动转 JSON 字符串 |

#### 成功响应（200）

```json
{
  "status": true,
  "data": { "id": 1 }                   # 新共享项 ID
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 400 | name is required | name 缺失或空 |
| 400 | item_type must be 'mcp' or 'extension' | item_type 非法 |

---

### 6.3 工具箱更新接口：POST /api/ai/toolbox/{id}/update

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |

#### 请求体（部分更新）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| name | string | 否 | 名称 |
| description | string | 否 | 描述 |
| config_json | string/object | 否 | 配置 |

#### 成功响应（200）

```json
{
  "status": true,
  "data": {}                            # 空对象
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 404 | not found | `{id}` 非整数或不存在 |

---

### 6.4 工具箱删除接口：POST /api/ai/toolbox/{id}/delete

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 请求 | 无请求体 |

#### 成功响应（200）

```json
{
  "status": true,
  "data": {}                            # 空对象
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 404 | not found | `{id}` 非整数或不存在 |

> skill 类型删除时同步清理 `engines/ai/skills/{id}/` 目录。

---

### 6.5 工具箱启停接口：POST /api/ai/toolbox/{id}/toggle

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |

#### 请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| enabled | boolean | 否 | 目标状态，缺省 true |

#### 成功响应（200）

```json
{
  "status": true,
  "data": { "enabled": true }           # 更新后的启用状态
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 404 | not found | `{id}` 非整数或不存在 |

---

### 6.6 上传共享 Skill 接口：POST /api/ai/toolbox/upload-skill/

以「文件夹」为单位上传自定义 Skill。浏览器 `<input type="file" webkitdirectory>` 选中的文件夹里，
每个文件的**相对路径**由前端经 `paths` 字段显式提交——Django 会把上传文件名归一为 basename
（`UploadedFile._set_name` 内的 `os.path.basename`），文件名里拿不到目录层级。

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | multipart/form-data |

#### 请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| files | file[] | 是 | 文件夹内全部文件（`request.FILES.getlist("files")`） |
| paths | string[] | 是 | 与 `files` **一一对应且顺序一致**的相对路径，值取浏览器的 `webkitRelativePath`（如 `my-skill/references/a.md`） |
| name | string | 是 | skill 名 = 文件夹名；必须与 `paths` 的顶层目录名一致 |

约束：文件夹根目录必须存在 `SKILL.md`，其 frontmatter 必须含非空 `name` 与 `description`；
该 Skill 的**介绍**（列表返回的 `description`）即取自 `SKILL.md` frontmatter 的 `description`（去首尾空白），
与本地 Skill 同一来源——不使用文件数量/类型统计摘要；
文件后缀必须在白名单内（`py/sh/bash/js/ts/json/yaml/yml/md/markdown/txt/toml/cfg/ini/env`）；
整个文件夹总大小不超过 50MB；`engines/ai/skills/{文件夹名}` 已存在时拒绝且不改动既有内容。

#### 成功响应（200）

```json
{
  "status": true,
  "data": { "id": 1 }                   # 新 skill 项 ID（文件存 engines/ai/skills/{文件夹名}/，子目录层级保留）
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 400 | no files uploaded | 无文件 |
| 400 | name is required | name 缺失或空 |
| 400 | 非法文件夹名: {name} | name 含 `/`、`\` 或 `..` |
| 400 | 缺少文件的相对路径信息，请重新选择整个 Skill 文件夹后再上传 | 未提交 `paths` |
| 400 | 相对路径数量({n})与文件数量({m})不一致，请重新选择 Skill 文件夹 | `paths` 与 `files` 数量不等 |
| 400 | 存在缺少相对路径的文件，请重新选择 Skill 文件夹 | 某条相对路径为空 |
| 400 | 非法相对路径: {raw} | 绝对路径或含 `..` 段 |
| 400 | 只接受文件夹上传，请选择包含 SKILL.md 的文件夹: {rel} | 相对路径缺少子路径（单文件） |
| 400 | 文件不在 skill 文件夹 {name}/ 下: {rel} | 顶层目录名与 `name` 不一致 |
| 400 | 文件夹根目录缺少 SKILL.md | 根目录无 `SKILL.md` |
| 400 | SKILL.md 解析失败: {err} | frontmatter 无法解析 |
| 400 | SKILL.md 缺少 frontmatter 的 name/description 字段 | frontmatter 字段缺失或为空 |
| 400 | 不支持的文件类型: {ext或'无后缀'}（{rel}） | 后缀不在白名单 |
| 400 | 总大小 {size_mb}MB 超过 50MB 限制 | 总大小超 50MB |
| 400 | 已存在同名 skill 文件夹: {name} | 目标目录已存在 |

> 校验全部在创建记录与写盘之前完成；失败时既不落库也不写文件。

---

## 7. knowledge 组

> 文档根目录：`data/rag_datas`。列表/上传走磁盘；检索与重建索引走向量库（仅 `*.md`）。

### 7.1 知识库状态接口：GET /api/ai/knowledge/status/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |

#### 成功响应（200）

```json
{
  "status": true,
  "data": {
    "doc_count": 3,
    "db_size_bytes": 0,
    "db_size_mb": 0.0,
    "collection_name": "project_knowledge",
    "reindex": {
      "running": false,
      "last_indexed": null,
      "message": ""
    }
  }
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |

---

### 7.2 知识库文档列表接口：GET /api/ai/knowledge/documents/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |

#### 成功响应（200）

```json
{
  "status": true,
  "data": {
    "documents": [
      {
        "id": "项目文档/a.md",
        "name": "a.md",
        "source": "项目文档/a.md",
        "type": "project_doc",
        "size": 12,
        "ext": "md"
      }
    ],
    "total": 1
  }
}
```

`type`：一级目录 `项目文档` → `project_doc`，`参考` → `reference`，`手动` → `manual`，其余为空字符串。

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |

---

### 7.3 知识库文档预览接口：GET /api/ai/knowledge/documents/preview/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Query | `path` 相对 `data/rag_datas` 的路径（禁止 `..`） |

#### 成功响应（200）

```json
{
  "status": true,
  "data": {
    "path": "说明.md",
    "name": "说明.md",
    "kind": "markdown",
    "content": "# 说明正文",
    "converted": true
  }
}
```

Word（`.docx`）与 PDF：若旁路尚无同名 `.md` 则转换并写入，再返回 Markdown；已有同名 `.md` 则直接读取。

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | 缺少文件路径 / 非法文件路径 / 不支持预览该类型 / 文档转换失败 | 参数或转换错误 |
| 404 | 找不到该文档 | 文件不存在 |
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |

---

### 7.4 知识库重建索引接口：POST /api/ai/knowledge/reindex/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 请求 | 无请求体 |

#### 成功响应（200）

```json
{
  "status": true,
  "data": {
    "message": "已索引 2 个文档",
    "indexed": [{"doc_id": "...", "source": "data/rag_datas/a.md"}],
    "failed": []
  }
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |

---

### 7.5 知识库添加文档接口：POST /api/ai/knowledge/documents/add/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | multipart/form-data |
| 请求 | `file` 必填；`subdir` 可选（`项目文档` / `参考` / `手动`） |

#### 成功响应（200）

```json
{
  "status": true,
  "data": {
    "id": "手册.md",
    "name": "手册.md",
    "source": "手册.md",
    "type": "",
    "size": 12,
    "ext": "md"
  }
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | 请选择要导入的文件 / 非法文件名 / 不支持的文件类型 / 文件过大 / 不支持的目标目录 / 文档保存失败 | 校验或写盘失败 |
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |

---

## 8. uploads 组

### 8.1 头像上传接口：POST /api/ai/upload-avatar/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |

#### 请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| image | string | 是 | base64 图片（可带 `data:...;base64,` 前缀，自动剥离） |

#### 成功响应（200）

```json
{
  "status": true,
  "data": {
    "url": "data:image/png;base64,xxxx"  # 生成 data URI
  }
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 400 | no image data | image 缺失或空 |
| 400 | 头像上传失败，请重试 | base64 解码失败 |

---

### 8.2 文件上传接口：POST /api/ai/upload-file/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | multipart/form-data |

#### 请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| file | file | 是 | 上传文件（`request.FILES.get("file")`） |

#### 成功响应（200，图片类）

```json
{
  "status": true,
  "data": {
    "filename": "shot.png",             # 原始文件名
    "size": 12345,                      # 字节数
    "type": "png",                      # 扩展名（小写）
    "media_type": "image/png",          # 媒体类型
    "data_uri": "data:image/png;base64,..."  # base64 data URI
  }
}
```

#### 成功响应（200，文档类）

```json
{
  "status": true,
  "data": {
    "filename": "spec.txt",
    "size": 1234,
    "type": "txt",
    "content": "全文内容...",           # 解析后文本（超 50000 字符截断）
    "preview": "前 300 字符...",         # 预览
    "parse_error": null                 # 解析错误信息（无则 null）
  }
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 400 | No file uploaded | 无文件 |
| 400 | Unsupported file type: .{ext}. Supported: ... | 扩展名不在白名单 |
| 400 | File too large ({size} bytes). Max: {max_size} bytes | 图片 >5MB / 文档 >20MB |

---

## 9. platform 组

### 9.1 平台配置读取接口：GET /api/ai/platform-config/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 请求 | 无请求体 |

#### 成功响应（200）

```json
{
  "status": true,
  "data": {
    "agent_id": 1,                      # 平台唯一智能体 ID
    "agent_name": "默认智能体",         # 智能体名
    "enable_workspace_tools": false,    # workspace 工具开关
    "enable_business_tools": false,     # 业务工具开关
    "enable_mcp_tools": false,          # MCP 工具开关
    "enable_skills": false,             # 技能开关
    "enable_knowledge_base": false,     # 知识库开关
    "skills_config": {},                # 技能启停配置
    "knowledge_sources": {}             # 知识库文档过滤
  }
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 404 | platform agent not found | 平台唯一智能体不存在 |

---

### 9.2 平台配置更新接口：POST /api/ai/platform-config/update/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer)，仅超级管理员 |
| Content-Type | application/json |

#### 请求体（部分更新，未传字段不变）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| enable_workspace_tools | boolean | 否 | workspace 工具开关 |
| enable_business_tools | boolean | 否 | 业务工具开关 |
| enable_mcp_tools | boolean | 否 | MCP 工具开关 |
| enable_skills | boolean | 否 | 技能开关 |
| enable_knowledge_base | boolean | 否 | 知识库开关 |
| skills_config | object | 否 | 技能启停配置 |
| knowledge_sources | object | 否 | 知识库文档过滤 |

#### 成功响应（200）

与 §9.1 相同（返回更新后的完整配置）。

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 403 | Forbidden | 非超级管理员 |
| 404 | platform agent not found | 平台唯一智能体不存在 |

---

### 9.2a 设备提示词读取接口：GET /api/ai/device-prompts/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |

#### 成功响应（200）

```json
{
  "status": true,
  "data": {
    "agent_id": 1,
    "planner": "## 角色\n...",
    "executor": "## 角色\n...",
    "verifier": "## 角色\n..."
  }
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| agent_id | int | 平台唯一智能体 ID |
| planner | string | 规划模型系统提示词（Markdown） |
| executor | string | 执行模型系统提示词（Markdown） |
| verifier | string | 验收模型系统提示词（Markdown） |

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 404 | platform agent not found | 平台唯一智能体不存在 |

---

### 9.2b 设备提示词更新接口：POST /api/ai/device-prompts/update/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer)，仅超级管理员 |
| Content-Type | application/json |

#### 请求体（三份必填，一次全写）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| planner | string | 是 | 规划模型系统提示词（去空白后不可空） |
| executor | string | 是 | 执行模型系统提示词（去空白后不可空） |
| verifier | string | 是 | 验收模型系统提示词（去空白后不可空） |

#### 成功响应（200）

与 §9.2a 相同（返回更新后的完整提示词）。

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | planner/executor/verifier 系统提示词不能为空 等 | 任一份去空白后为空，或缺少字段 |
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 403 | Forbidden | 非超级管理员 |
| 404 | platform agent not found | 平台唯一智能体不存在 |

---

### 9.3 平台工具启停接口：POST /api/ai/platform-tools/toggle/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer)，仅超级管理员 |
| Content-Type | application/json |

#### 请求体（`name` / `category` 二选一）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| name | string | 否 | 单工具名（如 `list_devices`） |
| category | string | 否 | 整分类名（如「设备管理」） |
| enabled | boolean | 否 | 目标状态，缺省 true |

#### 成功响应（200）

```json
{
  "status": true,
  "data": { "updated": ["list_devices"] }  # 受影响的工具名列表
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 403 | Forbidden | 非超级管理员 |
| 400 | name 或 category 必填其一 | 两者均未传 |
| 404 | tool not found | name 不在工具表 |
| 404 | category not found | category 无匹配工具 |

> 启用 = 删除停用记录（回默认启用）；停用 = upsert `enabled=False`。默认（无记录）＝启用。

---

### 9.4 平台工具调试 schema：GET /api/ai/platform-tools/{name}

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 请求 | 无请求体 |

#### 成功响应（200）

```json
{
  "status": true,
  "data": {
    "name": "acquire_device",
    "summary": "锁定一台在线设备用于独占测试。",
    "read_only": false,
    "parameters": [
      { "name": "serial", "type": "str", "required": true },
      { "name": "timeout", "type": "int", "required": false, "default": 300 }
    ]
  }
}
```

> `parameters` **不含** `user_id`（由服务端从 JWT 注入）。停用工具仍可查询 schema。

带 `options` 的参数是**候选值**：调试页把它渲染为可选择控件，同时保留手输。

```json
{
  "status": true,
  "data": {
    "name": "tap_screen",
    "summary": "按像素坐标点击或长按设备屏幕",
    "read_only": false,
    "parameters": [
      {
        "name": "serial",
        "type": "str",
        "required": true,
        "options": [{ "value": "RF8N21MSW7A", "label": "Pixel 6 (RF8N21MSW7A)" }]
      },
      { "name": "mode", "type": "str", "required": false, "default": "click" },
      { "name": "x", "type": "int", "required": false, "default": 0 },
      { "name": "y", "type": "int", "required": false, "default": 0 }
    ]
  }
}
```

> - `options[].value` 可直接提交；`options[].label` 为展示标签。
> - 设备类候选（当前为 `list_apps` / `input_text` / `tap_screen` / `swipe_screen` / `press_key` / `current_app` / `click_ratio` / `drag_ratio` / `xpath_action` 的 `serial`）只返回**对请求者可见、在线且未被占用**的设备，可见性口径与设备管理列表一致。
> - 候选为空数组表示当前没有可选设备，仍可手输后提交。
> - `acquire_device` / `release_device` 属设备池占用记账、不操作手机，其 `serial` 不带候选。

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 404 | tool not found | name 不在平台工具表 |

---

### 9.5 平台工具调试调用：POST /api/ai/platform-tools/{name}/invoke

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer)；**写工具**（`read_only=false`）仅超级管理员 |
| Content-Type | application/json |

#### 请求体

工具 kwargs 的 JSON 对象（可 `{}`）。若含 `user_id` 字段，服务端**丢弃**并用 JWT 身份注入。未知键返回 400。

#### 成功响应（200）

```json
{
  "status": true,
  "data": {
    "result": [ { "serial": "RF8..." } ]
  }
}
```

> `result` 形状与智能体调用同一工具一致（如 `screenshot_page` 含 `image.base64` + `summary`）。本接口走 JWT，**不得**使用 `/api/ai/tools/{module}/{action}` 内部令牌网关。

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 403 | Forbidden | 非超管调用写工具 |
| 400 | 未知参数 / 缺少必填参数 / 请求体必须是 JSON 对象 / 设备未注册… | 入参或前置条件错误（请求者可自行修正） |
| 404 | tool not found | name 不在平台工具表 |
| 500 | 工具执行失败: … | **工具或引擎内部故障**（实现缺陷、设备侧异常）；服务端同时记录含工具名与请求者的错误日志 |

> 失败按成因区分状态码：4xx = 请求者可修正的入参与前置条件问题；5xx = 工具/引擎内部故障。
> **不得**把内部故障折成 4xx（否则排查时会把工具 Bug 误判成参数问题）。

---

## 10. legacy tool gateway（豁免路径）

> Django 函数视图 + `JsonResponse`（`@csrf_exempt`），不走 `EnvelopeJSONRenderer`；
> 响应为视图内手动信封 `{status: true, data}` / `{status: false, message}`（与 DRF 信封形状相同，但 `data` 已是最终结果）。
>
> **鉴权（内部令牌）**：JWT 中间件对该前缀豁免（服务间调用不持有用户令牌），改由
> `gateway.internal_token.InternalToolTokenMiddleware` 校验请求头 —— **本节 3 个端点全部要求**：
>
> ```http
> X-Internal-Token: <settings.AI_TOOL_GATEWAY_TOKEN>
> ```
>
> 令牌未配置（`AI_TOOL_GATEWAY_TOKEN` 为空）或请求头缺失/不匹配时，一律返回：
>
> ```json
> { "status": false, "message": "内部令牌无效" }
> ```
>
> 状态码 `401`。CORS 预检（`OPTIONS`）不校验令牌。

### 10.1 工具 schema 接口：GET /api/ai/tools/schemas/

| 项 | 值 |
|---|---|
| 鉴权 | 内部令牌（`X-Internal-Token`） |
| 请求 | 无请求体 |

#### 成功响应（200）

```json
{
  "status": true,
  "data": {
    "categories": [                     # 工具分类元数据
      { "key": "设备管理", "icon": "📱", "color": "#6BCB77" },
      { "key": "视觉识别工具", "icon": "🔍", "color": "#A78BFA" }
    ],
    "tools": [                          # 全部工具 schema
      {
        "name": "list_devices",         # 工具名
        "summary": "查询设备...",        # 摘要（docstring 首行）
        "category": "设备管理",          # 分类
        "icon": "📱",
        "module": "devices",            # 分发 module
        "action": "list_all",           # 分发 action
        "read_only": true               # 是否只读
      }
    ]
  }
}
```

---

### 10.2 Agent 工具配置接口：GET /api/ai/tools/agent-config/{agent_id}

| 项 | 值 |
|---|---|
| 鉴权 | 内部令牌（`X-Internal-Token`） |
| 请求 | 无请求体；`{agent_id}` 为 Django 主键（int）或 AgentScope UUID |

#### 成功响应（200）

```json
{
  "status": true,
  "data": {
    "enabled_tools": ["list_devices"],  # 可用平台工具名列表
    "disabled_skills": [],              # 需隐藏的 workspace 技能名（已移除，恒空）
    "knowledge_sources": [],            # 启用知识库文档 ID 列表
    "capability_flags": {               # 能力开关
      "enable_workspace_tools": false,
      "enable_business_tools": false,
      "enable_mcp_tools": false,
      "enable_skills": false,
      "enable_knowledge_base": false
    }
  }
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | agent not found | 主键与 AgentScope UUID 均未命中 |

---

### 10.3 工具执行接口：POST /api/ai/tools/{module}/{action}

| 项 | 值 |
|---|---|
| 鉴权 | 内部令牌（`X-Internal-Token`） |
| Content-Type | application/json |

#### 请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| （工具参数） | - | - | 请求体为 JSON 对象，键为工具函数形参（如 `serial`、`query`、`case_ids` 等），`user_id` 由服务端注入 |

#### 成功响应（200）

```json
{
  "status": true,
  "data": { ... }                       # 工具执行结果（dict/list/str/primitive）
}
```

#### 失败响应

```json
{
  "status": false,
  "message": "工具未找到: devices/list_all"  # 错误文案
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | 工具未找到: {module}/{action} | 无匹配 handler |
| 400 | 无效的 JSON 请求体 | 请求体非合法 JSON |
| 400 | {ValueError 文案} | 工具抛出 ValueError |
| 500 | 工具执行失败: {e} | 工具抛出其他异常 |

> `(module, action) → 工具` 映射见 `apps/ai_assistant/tools.py` 的 `TOOL_META`（如 `devices/list_all → list_devices`、`runner/run_test → run_test`、`cases/save_definition → save_case`）。
