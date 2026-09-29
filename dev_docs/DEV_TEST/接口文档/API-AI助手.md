# API-AI助手 — /api/ai/*

> AI 助手模块（`apps/ai_assistant`）接口全集。Batch 1-3 已迁移到 DRF（Agent / 对话 / 工具箱 / 上传 / 平台配置 / 任务），
> 豁免工具网关（legacy 函数视图）。SSE 主对话（`chat_stream`）与 HITL（`hitl_views`）已随「主对话移除」删除。
> 知识库（RAG）能力已整体下线：`/api/ai/knowledge/*` 全部端点已删除（统一 404），
> `views_knowledge_drf.py` / `rag_service.py` 已删除，`kb_files.py` 更名为 `attachments.py`（仅保留任务附件解析）。
> 真相源：`apps/ai_assistant/urls.py` + `views_drf.py` + `views_toolbox_drf.py` + `views_upload_drf.py` + `views/tool_gateway.py` + `serializers.py` + `models.py` + `api.py`。

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
| **uploads 组** | | | |
| 头像上传 | POST /api/ai/upload-avatar/ | 需登录(Bearer) | base64 → data URI |
| 文件上传 | POST /api/ai/upload-file/ | 需登录(Bearer) | multipart 上传并解析 |
| **platform 组** | | | |
| 平台配置读取 | GET /api/ai/platform-config/ | 需登录(Bearer) | 平台唯一智能体能力配置 |
| 平台配置更新 | POST /api/ai/platform-config/update/ | 需登录(Bearer) | 更新（仅超管） |
| 模型调试配置 | GET /api/ai/model-debug/{role}/ | 需登录(Bearer)，仅超级管理员 | 单角色生效配置（模型 / 工具 / Skill；不下发提示词） |
| 模型调试对话 | POST /api/ai/model-debug/{role}/chat | 需登录(Bearer)，仅超级管理员 | 单角色对话（挂该角色真实工具、会真机操作、不落库；不设前端等待上限；有设备点击时返回日志检查块） |
| 日志关键词目录 | GET /api/ai/log-keywords/ | 需登录(Bearer) | 关键词 → 功能模块 / 功能点对照表（只读；含取值来源与更新时间） |
| 平台工具启停 | POST /api/ai/platform-tools/toggle/ | 需登录(Bearer) | 全局启停（仅超管） |
| 平台工具调试 schema | GET /api/ai/platform-tools/{name} | 需登录(Bearer) | 入参 schema（剥 user_id；设备参数附候选） |
| 平台工具调试调用 | POST /api/ai/platform-tools/{name}/invoke | 需登录(Bearer) | 真实调用；写工具仅超管 |
| **legacy tool gateway** | | | |
| 工具 schema | GET /api/ai/tools/schemas/ | 内部令牌 | 全部工具定义（服务间） |
| Agent 工具配置 | GET /api/ai/tools/agent-config/{agent_id} | 内部令牌 | per-agent 工具/技能配置 |
| 工具执行 | POST /api/ai/tools/{module}/{action} | 内部令牌 | 执行业务工具（服务间） |

## 2. 通用约定

- **无尾斜杠**：所有路径均无尾斜杠（`trailing_slash=False`）。
- **信封分两类**：
  - **DRF 迁移端点**（§3~§8，ViewSet / APIView 返回 `Response`）：经全局 `EnvelopeJSONRenderer` 包裹，成功 `{status: true, data: {...}}`，失败（4xx/5xx）`{status: false, message: "..."}`。
  - **legacy 工具网关**（§9，函数视图返回 `JsonResponse`）：不走 `EnvelopeJSONRenderer`，视图内手动返回 `{status: true, data}` / `{status: false, message}`（外层形状相同，但 `data` 已是最终结果，不再二次包裹）。
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
| enable_workspace_tools | boolean | 否 | workspace 工具开关 |
| enable_business_tools | boolean | 否 | 业务工具开关 |
| enable_mcp_tools | boolean | 否 | MCP 工具开关 |
| enable_skills | boolean | 否 | 技能开关 |
| status | string | 否 | 状态，缺省 active |
| skills_config | object | 否 | 技能启停配置 {"Bash": true, ...} |
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
      "enable_workspace_tools": false,
      "enable_business_tools": false,
      "enable_mcp_tools": false,
      "enable_skills": false,
      "skills_config": {},              # 技能启停配置
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
        "executor": { "result": "PASS", "click_timer": "2026-09-28 17:01:12.645", "screenshot": "ai_tasks/1/s1_l1.jpg" },
        "verifier": { "result": "PASS", "click_timer": "2026-09-28 17:01:12.645", "logAssertionTimer": "2026-09-28 17:01:13.100", "logAssertionInfo": "switch_on", "screenshot": "ai_tasks/1/s1_verify.jpg", "actual": "已在首页" }
      }],
      "usage": {},
      "models": { "planner": "…", "executor": "…", "verifier": "…", "max_loops": 3 }
    }
  }
}
```

> 运行中即可读到增量 `run.plans` / `run.log` / `run.summary`（如「已规划 N 个步骤」）；`data.status` 仍为 `running`，`run.status` 为 `running`。终态把全量过程写入 `ai_tasks.result`。
> 新协议：`plans[].steps` 为 `{action, assert}`；`log[]` 按步骤重试记录 `executor` / `verifier`。旧任务可能仍是字符串 steps + goal 级 log，前端详情页兼容折叠展示。
> `log[].executor` 为**执行模型输出契约**的三个字段：`result`（`PASS`/`FAIL`）、`click_timer`（**点击前的时间戳**，北京时间毫秒；本步无点击时为空串）、`screenshot`（**点击后截图的相对路径**，MEDIA 相对路径；本步未截图时为空串）。该契约不含 `action` / `message` —— **存量旧记录**里仍是 `{action, result, message}`，前端详情页按旧字段如实兼容展示、不报错。
> `log[].verifier` 为**验收模型输出契约**的六个字段：`result`（`PASS`/`FAIL`，不再是布尔）、`click_timer`（**点击前的时间戳**，抄平台下发的执行侧证据；本步无点击时为空串）、`logAssertionTimer`（**检测到日志关键词的时间戳**，取 `check_device_log` 返回的命中时间戳；未检测到为空串）、`logAssertionInfo`（**本轮检查的日志关键词**，平台按模型对检查工具的调用自动填）、`screenshot`（**验证截图的相对路径**，抄本次截图返回的路径；未取到为空串）、`actual`（截图里实际看到了什么，也是失败重试时回灌给执行模型的原因）。判定口径：**日志检测到 + 截图确认两个条件都满足才判 PASS**。该契约不含 `action` / `assert` —— **存量旧记录**里仍是 `{action, assert, actual, result}` 且 `result` 为布尔，前端详情页按旧字段如实兼容展示、不报错。
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

## 7. uploads 组

### 7.1 头像上传接口：POST /api/ai/upload-avatar/

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

### 7.2 文件上传接口：POST /api/ai/upload-file/

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

## 8. platform 组

### 8.1 平台配置读取接口：GET /api/ai/platform-config/

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
    "skills_config": {}                 # 技能启停配置
  }
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 404 | platform agent not found | 平台唯一智能体不存在 |

---

### 8.2 平台配置更新接口：POST /api/ai/platform-config/update/

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
| skills_config | object | 否 | 技能启停配置 |

#### 成功响应（200）

与 §8.1 相同（返回更新后的完整配置）。

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 403 | Forbidden | 非超级管理员 |
| 404 | platform agent not found | 平台唯一智能体不存在 |

---

### 8.2g 模型调试配置接口：GET /api/ai/model-debug/{role}/

工具箱「模型调试」来源与单模型调试页的数据源。role 取值 planner / executor / verifier。

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer)，仅超级管理员 |

#### 成功响应（200）

```json
{
  "status": true,
  "data": {
    "agent_id": 10,
    "agent_name": "自动化小助手",
    "role": {
      "role": "executor",
      "label": "执行模型 Executor",
      "vision": true,
      "needs_device": true,
      "model": { "provider": "deepseek", "model_name": "deepseek-chat", "has_api_key": true, "configured": true },
      "tools": [
        { "name": "tap_screen", "read_only": false, "category": "设备控制", "enabled": true }
      ]
    },
    "skills": { "gate_on": true, "shared_by_roles": true, "items": [{ "name": "skill-a", "path": "/abs/path" }] }
  }
}
```

| 字段 | 说明 |
|---|---|
| role.tools | 该角色**实际装配**的工具子集（取自引擎角色类，非另抄常量）：规划=页面流工具、执行=视觉/设备操作工具集、验收=截图工具 |
| 不下发提示词 | 响应**不含系统提示词正文**：提示词是引擎常量（`engines/ai/agents/config.py`），前端不展示、不可编辑 |
| role.needs_device | 该角色工具子集里是否有工具需要设备（按工具签名是否含 `serial` 参数判定）：规划=false、执行/验收=true；前端据此决定是否要求先选设备 |
| role.model | 模型连接摘要；**只回是否已配置（has_api_key），不回 api_key / base_url 明文** |
| skills.shared_by_roles | 恒 true：Skill 由装配链路整组下发，**三模型共用**（非按角色分配） |

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | 未知角色: {role}，可选 planner, executor, verifier | role 不在白名单 |
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 403 | Forbidden | 非超级管理员 |
| 404 | platform agent not found | 平台唯一智能体不存在 |

---

### 8.2h 单角色调试对话接口：POST /api/ai/model-debug/{role}/chat

用该角色的系统提示词、模型连接与**真实工具子集**发起一次对话，用于确认提示词修改是否生效。**挂载该角色实际装配的工具（可能真实操作设备）**，**不写入会话 / 消息表**。前端不设等待上限（模型多轮 ReAct + 抓屏可能远超 5 分钟）。本轮产生设备副作用点击时，响应带一份平台装配的**日志检查**（点击前时间点 + 点击后截图路径 + 该时间点后 5 秒日志）；读窗需等到「最后一次点击 + 5 秒」，因此这类对话的返回会比纯文本对话晚约 5 秒。

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer)，仅超级管理员 |
| Content-Type | application/json |

#### 请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| text | string | 是 | 发给该角色的文本（去空白后不可空） |
| serial | string | 条件必填 | 该角色 `needs_device=true` 时必填；服务端校验其**对请求者可见 + 在线 + 未被占用**，不满足返回 400 且不触发模型调用。以 `当前设备 serial：{serial}` 前缀进入模型输入 |

#### 成功响应（200）

```json
{
  "status": true,
  "data": {
    "role": "executor", "label": "执行模型 Executor", "model_name": "deepseek-chat",
    "reply": "…模型回复…", "thinking": ["…思考块…"],
    "tool_usage": [
      { "type": "call", "name": "current_app", "input": { "serial": "R5CT62RH88F" } },
      { "type": "result", "name": "current_app", "state": "success", "output": "{\"package\": \"com.govee.home\"}" }
    ],
    "log_check": {
      "clicks": [{ "action_time": "2026-09-28 10:51:03.219", "screenshot_path": "ai_tasks/12/s1.jpg" }],
      "log": { "conclusion": "hit", "threshold_seconds": 5.0, "window_line_count": 3, "hits": [] }
    },
    "usage": { "input_tokens": 1200, "output_tokens": 300 }, "cost": 0.0012
  }
}
```

| 字段 | 说明 |
|---|---|
| reply | 模型回复原文（平台不改写）。**执行模型**（`role=executor`）的回复即其输出契约：`{"result": "PASS|FAIL", "click_timer": "点击前时间戳", "screenshot": "点击后截图相对路径"}`（本步无点击 / 未截图时对应值为空串）；**验收模型**（`role=verifier`）为 `{"result": "PASS|FAIL", "click_timer": "点击前时间戳", "logAssertionTimer": "检测到日志关键词的时间戳", "logAssertionInfo": "本轮检查的日志关键词", "screenshot": "验证截图相对路径", "actual": "实际结果说明"}`（未检测到日志关键词 / 未取到路径时对应值为空串；`logAssertionInfo` 由平台按检查工具调用自动填）；规划模型为 `{"plan": {…}}` |
| tool_usage | 本轮工具调用轨迹（引擎从上下文回溯，脱敏无 base64）：`type=call` 带 `input`，`type=result` 带 `state` / `output` |
| log_check | 本轮**设备点击证据**（平台装配，不依赖模型抄写；本轮没有任何副作用点击时该键不出现）：`clicks[]` 为每次点击的**点击前时间点**（北京时间毫秒）与**点击后截图路径**（该次点击后未截图时为空串）；`log` 为该时间点后 5 秒窗口内的日志证据（原始日志 + 命中标注，与任务步骤证据同源）。窗口在对话**之前**开启；日志端口全部处于关闭监听 / 采集未启用时 `log` 为 `null`（平台**不会**为了调试打开端口） |
| log_evidence | **验收角色**（`role=verifier`）专有：平台按取证基准从**日志文件回溯**取出的设备日志证据块（形状与任务详情 `log_evidence` 同源：`conclusion` / `window_line_count` / `hits[]`（含关键词与时间戳）/ `lines[]` 等），用于让验收模型自己读出 `logAssertionTimer`。取不到窗口内日志时该键不出现（原因见 `log_basis.note`） |
| log_basis | 该证据的**取证基准**：`basis_time`（实际使用的基准时刻，北京时间毫秒）、`from_message`（`true`=取自消息里第一个毫秒时间戳；`false`=消息里没有时刻，退回「最近一个取证窗」）、`files[]`（实际读取的日志文件）、`note`（取不到时的如实原因，如「窗口内无日志」「日志端口都未开启监听」）。取证窗 = 基准后 5 秒（阈值同生产）；**从日志文件回溯**是为了覆盖「点击到验收已超过内存缓冲保留时长」的情形，口径与任务链路一致但**不是生产步骤的取证窗**；端口监听关着时平台不取证据也不打开端口 |
| log_assertion_info | 本轮验收**实际检查的日志关键词**（平台按模型对只读工具 `check_device_log` 的调用自动填，多个按调用顺序以「、」连接）；模型没检查过日志时该键不出现。关键词表（关键词 → 功能点）随验收输入一并下发，模型只报关键词、由平台按规则判定「检测到 / 未检测到」；判定口径为「日志检测到 + 截图确认两个条件都满足才判 PASS」 |

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | 未知角色: {role}，可选 planner, executor, verifier | role 不在白名单 |
| 400 | 调试内容不能为空 | text 缺失或去空白后为空 |
| 400 | 「{角色}」需要先选定一台设备（候选：对当前用户可见 + 在线 + 未被占用） | 该角色 needs_device=true 但未给 serial |
| 400 | 设备 {serial} 当前不可用（需对当前用户可见、状态在线且未被占用），请重新选择 | serial 不可见 / 不在线 / 已被占用 |
| 400 | 「{角色}」的 model_name 未配置，请到智能体配置页填写 … | 该角色模型未配置（装配**之前**校验） |
| 400 | 「{角色}」的 api_key 未配置（或无法解密），请到智能体配置页重新填写 | API Key 缺失或解密失败 |
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |
| 403 | Forbidden | 非超级管理员 |
| 404 | platform agent not found | 平台唯一智能体不存在 |

---

### 8.2i 日志关键词目录接口：GET /api/ai/log-keywords/

AI 工具箱「日志关键词」来源的只读数据源：当前「串口日志关键词 → 功能模块 / 功能点」对照表。该表既是日志证据等级判定（强证据 / 疑似周期）的依据，也是只读日志查询工具还原功能点的依据。**只读**：不写文件、不写库、不启停任何端口。

取值优先级：**采集正在运行时取运行中的关键词索引**（`origin=runtime`，即判定真正在用的那份）；采集尚未创建时直读配置文件（`origin=file`）；两者都拿不到时返回空列表（`origin=none`）与可读 `note`。关键词保持**表内顺序**，分组与排序由前端派生。

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer)，登录即可读（与「无线端口」列表同口径；无写入口） |
| Content-Type | — |

#### 成功响应（200）

```json
{
  "status": true,
  "data": {
    "keywords": [
      { "keyword": "switch_on", "features": [{ "id": 0, "module": "设备开关", "feature": "打开设备成功" }] },
      { "keyword": "color_configs_set_success", "features": [
        { "id": 2, "module": "音效律动", "feature": "灯光颜色设置成功" },
        { "id": 17, "module": "彩色模式", "feature": "手动-颜色设置成功" }
      ] }
    ],
    "keyword_count": 67, "feature_count": 56,
    "origin": "runtime",
    "keyword_file": "config/device_log_keywords.json",
    "updated_at": "2026-09-28 18:20:11",
    "note": ""
  }
}
```

| 字段 | 说明 |
|---|---|
| keywords | 逐关键词的对照条目，保持表内顺序；`features` 为该关键词对应的**全部**功能点（编号 + 模块 + 名称），一个关键词可对应多个 |
| keyword_count / feature_count | 关键词数与功能点数（后者按「模块 + 编号 + 名称」去重） |
| origin | 取值来源：`runtime` 运行中的采集索引 / `file` 关键词表文件 / `none` 都取不到 |
| keyword_file / updated_at | 对照表文件路径与其最后修改时间（北京时间，秒精度；取不到为空串） |
| note | 表不可用时的可读原因（正常为空串）；此时 `keywords` 为空列表 |

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 鉴权失败 |

> 表不可用不是错误：接口仍返回 200，靠 `note` 说明原因，页面据此给空态。

---

### 8.3 平台工具启停接口：POST /api/ai/platform-tools/toggle/

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

### 8.4 平台工具调试 schema：GET /api/ai/platform-tools/{name}

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

### 8.5 平台工具调试调用：POST /api/ai/platform-tools/{name}/invoke

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

## 9. legacy tool gateway（豁免路径）

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

### 9.1 工具 schema 接口：GET /api/ai/tools/schemas/

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

### 9.2 Agent 工具配置接口：GET /api/ai/tools/agent-config/{agent_id}

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
    "capability_flags": {               # 能力开关
      "enable_workspace_tools": false,
      "enable_business_tools": false,
      "enable_mcp_tools": false,
      "enable_skills": false
    }
  }
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | agent not found | 主键与 AgentScope UUID 均未命中 |

---

### 9.3 工具执行接口：POST /api/ai/tools/{module}/{action}

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
