# AI 助手技术架构与功能设计文档

> 模块：`ai-assistant` | 更新：2026-07-02 | 前端 2769 行 | 后端 17 个 API + 19 个 AgentScope Tool

---

## 1. 架构概览

```
┌──────────────────────────────────────────────────────────────┐
│  Vue 前端 (3 页面)                                           │
│  index.vue (459行)    AgentDetail.vue (788行)   ChatView.vue (1325行) │
│       │                      │                        │
│       ▼                      ▼                        ▼
│  /api/ai/agents       /api/ai/agents/:id      /api/ai/conversations/:id/send
│       │                      │                        │
├───────┼──────────────────────┼────────────────────────┼──────┤
│  Django :8765                │                        │      │
│  apps/ai_assistant/          │                        │      │
│  ├─ models.py  (6 表)        │                        │      │
│  ├─ views.py  (17 端点)      │                        │      │
│  ├─ urls.py                  │                        │      │
│  └─ dashboard_views.py       │                        │      │
│              │                                        │      │
│  ┌───────────┼─────────────── 跨模块通信 ─────────────┤      │
│  │  device_pool  │  element_locator  │  case_manager  │      │
│  │  test_runner  │  report_generator │                │      │
│  └───────────────────────────────────────────────────┘      │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  AgentScope :8000 (FastAPI + Redis)                          │
│  ├─ agentscope_service/app.py                                │
│  ├─ agent_factory.py     (Django → AgentScope Agent)         │
│  ├─ tools/               (19 个业务 Tool)                    │
│  │   ├─ element_tools.py  (2)  get_test_points, search_elements │
│  │   ├─ case_tools.py     (4)  save/get/list/debug_test_case │
│  │   ├─ task_tools.py     (2)  fetch_page_elements, create_runner_task │
│  │   ├─ device_tools.py   (3)  get_online/acquire/release    │
│  │   ├─ runner_tools.py   (3)  run/get_results/stop          │
│  │   ├─ report_tools.py   (2)  save/list_reports             │
│  │   ├─ rag_tool.py       (1)  search_knowledge_base         │
│  │   └─ factory.py             工具注册工厂                   │
│  ├─ teams/               (5 个 SubAgent 模板)                │
│  └─ rag/                 ChromaDB 知识库 (32 篇)             │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  MySQL :3306                                                 │
│  ├─ ai_agents        智能体配置 (含 is_connected/health)      │
│  ├─ ai_tools         工具/MCP 配置                            │
│  ├─ ai_conversations 对话会话                                 │
│  ├─ ai_messages      对话消息                                 │
│  ├─ ai_tasks         定时任务                                 │
│  └─ ai_execution_logs 执行日志                                │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. 前端页面

### 2.1 智能体列表 (`index.vue`)

| 功能 | 组件 | 说明 |
|------|------|------|
| 筛选切换 | `Tabs` (animal-island) | 全部 \| 运行中 \| 未连通 \| 已暂停 |
| 智能体卡片 | `Card` (animal-island) | 13 色调色板 + 图案纹理，未连通 = `type="dashed"` |
| 模型选择 | `el-select` 内嵌卡片 | 内置 + API 检测 + 自定义 provider 模型合并去重 |
| 健康状态 | 绿/红圆点 + `el-tag` | 运行中(绿)、未连通(红)、已暂停(黄) |
| 连接测试 | `Button` | `POST /api/ai/agents/{id}/test` |
| 删除 | `Button` + `ElMessageBox` | 确认弹窗 → `POST /delete` |
| 定时巡检 | `setInterval(30min)` | `GET /api/ai/agents/health` |

### 2.2 智能体配置 (`AgentDetail.vue`)

5 步配置向导，`v-if` 按需渲染：

| 步骤 | 内容 | 关键功能 |
|:--:|------|----------|
| 1 | 基本信息 | 名称、头像（上传/Emoji）、标签、描述 |
| 2 | 模型配置 | 提供商选择（DashScope/OpenAI/Anthropic/**DeepSeek**/自定义）、**🔍 检测模型**按钮、API Key、温度/Token |
| 3 | 提示词 | 系统提示词、最大迭代、并行工具、打印消息 |
| 4 | 记忆与工具 | 记忆模式（InMemory/LongTerm）、元工具、MCP 服务器配置 |
| 5 | 高级 | TTS、内存压缩（阈值/保留/提示词/模板） |

### 2.3 对话页 (`ChatView.vue`)

| 区域 | 功能 |
|------|------|
| **左侧栏** | 对话列表（双击改名、✕ 删除）、AI 任务记录折叠面板 |
| **聊天区** | 消息气泡（Markdown + Mermaid 渲染）、空状态提示 |
| **模式栏** | 💬 闲聊模式 / 📋 测试任务创建（互斥、任务锁） |
| **输入区** | 📎 文件上传（txt/log/md/docx/xlsx/pdf）、动态 placeholder |
| **文件预览** | 文件名 + 大小 + 内容解析注入 AI 消息 |
| **任务确认弹窗** | 检测 `create_runner_task` 结果 → 展示任务卡片 → 确认/取消 |

**Markdown 渲染**：`marked` (GFM) + `mermaid` (v11) 图表支持
**文件解析**：`python-docx` / `openpyxl` / `pymupdf` (21 种格式)

---

## 3. 后端 API（17 端点）

### 3.1 智能体管理 (6)

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/ai/agents` | 列表（含 tool_count） |
| GET | `/api/ai/agents/{id}` | 详情（含 tools、is_connected、available_models） |
| POST | `/api/ai/agents/create` | 创建（api_key 自动 Fernet 加密） |
| POST | `/api/ai/agents/{id}/update` | 更新（掩码 key 保留原值） |
| POST | `/api/ai/agents/{id}/delete` | 删除 |
| POST | `/api/ai/agents/{id}/test` | 连接测试 + 模型检测 |

### 3.2 对话管理 (7)

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/ai/agents/{id}/conversations` | 对话列表 |
| POST | `/api/ai/agents/{id}/conversations/create` | 新建对话 |
| POST | `/api/ai/conversations/{id}/rename` | 重命名 |
| POST | `/api/ai/conversations/{id}/delete` | 删除（级联消息） |
| GET | `/api/ai/conversations/{id}/messages` | 消息列表 |
| POST | `/api/ai/conversations/{id}/send` | **发送消息（核心）** — Django 直接调 LLM API |
| POST | `/api/ai/conversations/{id}/save-message` | 保存消息 |

### 3.3 模型 & 健康 (3)

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/ai/models/detect` | API 模型列表检测 |
| GET | `/api/ai/agents/{id}/models` | 缓存模型列表 |
| GET | `/api/ai/agents/health` | 全体健康检查（30min 定时） |

### 3.4 文件上传 (1)

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/ai/upload-file` | 上传 + 自动解析（21 格式，20MB 上限） |

### 3.5 认证 (5)

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/ai/auth/login` | JWT 登录 |
| POST | `/api/ai/auth/register` | 注册 |
| POST | `/api/ai/auth/refresh` | Token 刷新 |
| POST | `/api/ai/auth/logout` | 登出（黑名单） |
| GET | `/api/ai/auth/me` | 当前用户 |

---

## 4. AgentScope Tool 体系（19 个）

### 4.1 元素类 (3)

| Tool | 只读 | 输入 → 输出 |
|------|:--:|------|
| `get_test_points` | ✅ | page_ids? → 测试点元素列表 + XPath |
| `search_elements` | ✅ | query, limit → 按关键词搜索 UI 元素 |
| `fetch_page_elements` | ✅ | page_id/page_label, limit → 页面全部元素 + XPath |

### 4.2 用例类 (4)

| Tool | 只读 | 输入 → 输出 |
|------|:--:|------|
| `save_test_case` | ❌ | case_id, title, steps[] → 创建/更新用例（14 种步骤） |
| `get_test_case` | ✅ | case_id → 用例详情 + 步骤列表 |
| `list_test_cases` | ✅ | case_ids? → 已启用用例列表 |
| `debug_test_case` | ✅ | case_id → 验证报告（XPath 有效性、步骤类型、设备状态） |

### 4.3 任务类 (1)

| Tool | 只读 | 输入 → 输出 |
|------|:--:|------|
| `create_runner_task` | ❌ | task_name, device_serial, case_ids → 执行引擎 PENDING 任务卡片 |

### 4.4 设备类 (3)

| Tool | 只读 | 输入 → 输出 |
|------|:--:|------|
| `get_online_devices` | ✅ | — → 在线设备列表 |
| `acquire_device` | ❌ | serial, timeout → 锁定设备 |
| `release_device` | ❌ | serial → 释放设备 |

### 4.5 执行类 (3)

| Tool | 只读 | 输入 → 输出 |
|------|:--:|------|
| `run_test` | ❌ | run_id, serial, case_ids, loop_count → 启动执行 |
| `get_run_results` | ✅ | run_id → 执行结果详情 |
| `stop_run` | ❌ | run_id → 停止执行 |

### 4.6 报告 & 知识 (3)

| Tool | 只读 | 输入 → 输出 |
|------|:--:|------|
| `save_report` | ❌ | title, data → 保存报告 |
| `list_reports` | ✅ | — → 报告列表 |
| `search_knowledge_base` | ✅ | query → ChromaDB 向量检索 |

### 4.7 工具注册流程

```
AgentScope 启动
  └─ factory.build_business_tools()
       └─ 返回 19 个 ToolBase 子类实例
            └─ AgentScope 自动读取 input_schema + description
                 └─ LLM 根据上下文自动选择调用
```

---

## 5. 数据库模型

### 5.1 `ai_agents` — 智能体配置

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| name | varchar(200) | - | 名称 |
| model_provider | varchar(50) | dashscope | dashscope/openai/anthropic/deepseek/custom |
| model_name | varchar(100) | qwen-max | 模型名称 |
| api_key | varchar(500) | '' | **Fernet 加密存储** |
| base_url | varchar(500) | '' | 自定义 API 地址 |
| system_prompt | text | '' | AI 系统提示词 |
| temperature | float | 0.7 | 0~2 |
| max_tokens | int | 4096 | 最大 Token |
| memory_mode | varchar(20) | inmemory | inmemory/longterm |
| is_connected | bool | False | **健康检测结果** |
| last_checked_at | datetime | NULL | **最后检测时间** |
| available_models | text | '' | **JSON 模型列表** |
| status | varchar(20) | active | active/paused/error |

### 5.2 `ai_tools` — 工具配置

```python
agent → ForeignKey(AIAgent, CASCADE)
name, tool_type, config_json, enabled, created_at
```

### 5.3 `ai_conversations` / `ai_messages`

```python
# 对话
agent, title, status, created_at, updated_at

# 消息 (CASCADE on conversation delete)
conversation, role, content, tool_calls, tokens, created_at
```

---

## 6. API Key 安全

```
存入: Fernet(SHA256(SECRET_KEY)).encrypt(plaintext) → base64 cipher
读取: Fernet.decrypt(cipher) → plaintext
兼容: 解密失败时返回原文（明文遗留兼容）
掩码: sk-***xxxx (API 返回时)
更新: 掩码值（含 ***）时跳过更新，保留原加密值
```

---

## 7. 任务设计模式工作流

```
用户选择「📋 测试任务创建」
  │
  ├─ AI 收到任务编排指令（5 步流程提示）
  ├─ taskLocked = true（阻塞新任务）
  │
  ▼
用户: "帮我测试 XX 功能在 YY 设备上"
  │
  ▼
AI 引导对话:
  1. 确认测试目标、设备、场景
  2. search_elements / fetch_page_elements → 获取 XPath
  3. save_test_case → 编写用例步骤
  4. debug_test_case → 验证用例
  5. create_runner_task → 创建任务卡片
  │
  ▼
前端检测 Run ID → 弹窗确认卡片
  │
  ├─ 确认 → 解锁，任务进入执行引擎
  └─ 取消 → 解锁，重新设计
```

---

## 8. 文件解析能力

| 格式 | 库 | 输出格式 |
|------|----|----------|
| `.txt` `.log` `.json` `.xml` `.csv` `.py` `.js` `.html` `.css` `.yaml` `.yml` | UTF-8 直接读取 | 原文 |
| `.md` `.markdown` | 直接读取 | Markdown 源码 |
| `.docx` | python-docx | 段落文本 |
| `.xlsx` | openpyxl | Sheet 名 + TSV 表格 |
| `.pdf` | pymupdf (fitz) | 页码 + 文本 |

- 最大 20MB，内容 > 50K 字符自动截断
- 发送时以代码块包裹注入 AI 消息

---

## 9. 前端文件清单

| 文件 | 行数 | 功能 |
|------|:--:|------|
| `index.vue` | 459 | 智能体列表 + 卡片 + Tabs + 健康检测 |
| `AgentDetail.vue` | 788 | 5 步配置向导 + 模型检测 + MCP 工具编辑 |
| `ChatView.vue` | 1325 | 聊天 + Markdown/Mermaid + 任务模式 + 文件上传 |
| `api.js` | 98 | AgentScope SSE 流式封装 |
| `routes.js` | 8 | 3 条路由（列表/配置/对话） |
| `animal-theme.css` | 91 | 动森主题 CSS 变量覆盖 |
| **合计** | **2769** | |

---

## 10. 已集成 animal-island-vue 组件

| 组件 | 使用位置 |
|------|----------|
| `Tabs` | Agent 列表模式切换、ChatView 任务模式 |
| `Card` | Agent 卡片（13 色 + dashed 边框） |
| `Button` | 全局按钮 |
| `Switch` | AgentDetail 表单开关 |
| `Collapse` | ChatView 任务记录面板 |
| `Modal` | AgentDetail 图片上传、ChatView 任务确认 |
| `Input` | AgentDetail 表单字段 |
| `Select` | Agent 模型选择器 |
