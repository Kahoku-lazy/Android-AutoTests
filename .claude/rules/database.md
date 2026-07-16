# Database — Android-AutoTests

## 表结构 (6 组前缀，20 张表)

### device-pool (`dp_`) — 3 表

**`dp_devices`** — ADB 设备注册表

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int PK | 自增主键 |
| `serial` | varchar(100) unique | ADB 序列号 |
| `name` | varchar(200) | 设备别名 |
| `model` | varchar(200) | 型号 |
| `brand` | varchar(100) | 品牌 |
| `screen_w` | int | 屏幕宽度 |
| `screen_h` | int | 屏幕高度 |
| `android_version` | varchar(20) | 系统版本 |
| `connection_type` | varchar(10) | USB / WIFI |
| `status` | varchar(20) | ONLINE / BUSY / OFFLINE / DISCONNECTED |
| `locked_by` | varchar(200) | 锁定用户 |
| `locked_at` | datetime | 锁定时间 |
| `last_seen` | datetime | 最后在线时间 |
| `created_at` | datetime | 首次注册时间 |

**`dp_device_locks`** — 设备锁审计日志（从不删除）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int PK | 自增主键 |
| `device_id` | FK → dp_devices | 关联设备 |
| `user_id` | varchar(200) | 锁定用户 |
| `status` | varchar(20) | active / released / expired |
| `locked_at` | datetime | 锁定时间 |
| `released_at` | datetime | 释放时间 |
| `timeout_seconds` | int | 超时秒数 (默认 300) |
| `release_reason` | varchar(20) | manual / timeout / disconnect / force |

**`dp_device_queue`** — FIFO 等待队列

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int PK | 自增主键 |
| `device_id` | FK → dp_devices | 关联设备 |
| `user_id` | varchar(200) | 排队用户 |
| `requested_at` | datetime | 申请时间 |
| `status` | varchar(20) | waiting / assigned / cancelled / timeout |
| `assigned_at` | datetime | 分配时间 |

### element-locator (`el_`) — 3 表

**`el_pages`** — UI 页面快照

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int PK | 自增主键 |
| `device_id` | FK → dp_devices (nullable) | 关联设备 |
| `label` | varchar(500) | 页面标签 |
| `package` | varchar(500) | App 包名 |
| `activity` | varchar(500) | Activity 名 |
| `screenshot_path` | varchar(1000) | 截图文件路径 |
| `element_count` | int | 元素数量 |
| `created_at` | datetime | 创建时间 |

**`el_elements`** — UI 元素（含 XPath 候选）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int PK | 自增主键 |
| `page_id` | FK → el_pages (CASCADE) | 所属页面 |
| `class_name` | varchar(500) | 控件类名 |
| `text_val` | varchar(2000) | 文本内容 |
| `content_desc` | varchar(2000) | ContentDescription |
| `resource_id` | varchar(500) | Resource ID |
| `bounds` | varchar(200) | 坐标边界 |
| `xpath_candidates` | text | 8 种 XPath 候选 (JSON) |
| `clickable` | bool | 是否可点击 |
| `enabled` | bool | 是否可用 |
| `alias` | varchar(500) | 中文别名 |
| `tags` | varchar(500) | 标签 |
| `is_test_point` | bool | 是否标记为测试点 |
| `notes` | text | 备注 |
| `created_at` | datetime | 创建时间 |

> 唯一约束：`(page_id, resource_id, bounds)`

**`el_page_flows`** — 页面跳转流

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int PK | 自增主键 |
| `from_page_id` | FK → el_pages | 起始页面 |
| `to_page_id` | FK → el_pages | 目标页面 |
| `trigger_element_id` | FK → el_elements (nullable) | 触发元素 |
| `trigger_action` | varchar(50) | 触发动作 (默认 click) |
| `created_at` | datetime | 创建时间 |

### case-manager (`cm_`) — 2 表

**`cm_test_definitions`** — 可执行用例定义

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | varchar(200) PK | 用例 ID |
| `title` | varchar(500) | 用例标题 |
| `category` | varchar(200) | 分类 |
| `description` | text | 描述 |
| `steps` | text | 步骤描述（文本） |
| `steps_json` | text | 步骤 JSON（结构化） |
| `enabled` | bool | 是否启用 |
| `package_name` | varchar(200) | 目标 App 包名 |
| `created_at` | datetime | 创建时间 |
| `updated_at` | datetime | 更新时间 |

**`cm_test_cases`** — YAML 导出缓存

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int PK | 自增主键 |
| `name` | varchar(500) | 用例名称 |
| `description` | text | 描述 |
| `yaml_content` | text | YAML 内容 |
| `created_at` | datetime | 创建时间 |

### test-runner (`tr_`) — 3 表

**`tr_test_runs`** — 测试执行记录

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int PK | 自增主键 |
| `run_id` | varchar(200) unique | 运行 ID |
| `status` | varchar(50) | PENDING / RUNNING / PASSED / FAILED / STOPPED |
| `device_serial` | varchar(200) | 执行设备 |
| `selected_cases` | JSON | 选中的用例列表 |
| `loop_count` | int | 循环次数 |
| `summary` | JSON | 结果摘要 |
| `started_at` | varchar(100) | 开始时间 |
| `finished_at` | varchar(100) | 结束时间 |
| `csv_path` | varchar(1000) | CSV 报告路径 |
| `log_path` | varchar(1000) | 日志文件路径 |

**`tr_test_results`** — 单次迭代结果

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int PK | 自增主键 |
| `run_id` | FK → tr_test_runs (CASCADE, nullable) | 关联执行 |
| `case_id` | varchar(200) | 用例 ID |
| `iteration` | int | 迭代序号 |
| `result` | varchar(50) | PASS / FAIL / ERROR |
| `duration_ms` | float | 耗时 (毫秒) |
| `detail` | text | 详情 |
| `created_at` | datetime | 创建时间 |

> 索引：`case_id`、`result`

**`tr_test_sop`** — AI SOP 四阶段工作流上下文

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int PK | 自增主键 |
| `sop_id` | varchar(50) unique | SOP 标识 |
| `conv_id` | int | 关联对话 ID |
| `phase` | int | 当前阶段 (1-4) |
| `status` | varchar(20) | active / completed / cancelled |
| `requirement` | text | 用户需求摘要 |
| `case_design` | JSON | 用例设计方案 |
| `element_mapping` | JSON | 元素映射表 |
| `element_gaps` | JSON | 缺失元素记录 |
| `debug_notes` | JSON | 调试笔记 |
| `case_ids` | JSON | 关联的用例 ID 列表 |
| `run_id` | varchar(200) | 关联的执行 ID |
| `run_results` | JSON | 执行结果 |
| `created_at` | datetime | 创建时间 |
| `updated_at` | datetime | 更新时间 |

### report-generator (`rg_`) — 2 表

**`rg_reports`** — 报告记录

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int PK | 自增主键 |
| `run_id` | varchar(200) indexed | 关联执行 ID |
| `title` | varchar(500) | 报告标题 |
| `file_type` | varchar(20) | 文件类型 (csv/html) |
| `file_path` | varchar(1000) | 文件路径 |
| `created_at` | datetime | 创建时间 |

**`rg_report_templates`** — 报告模板

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int PK | 自增主键 |
| `name` | varchar(200) | 模板名称 |
| `config` | JSON | 模板配置 |
| `created_at` | datetime | 创建时间 |

### ai-assistant (`ai_`) — 6 表

**`ai_agents`** — 智能体配置

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int PK | 自增主键 |
| `name` | varchar(200) | 名称 |
| `avatar` | varchar(500) | 头像路径 |
| `tags` | varchar(500) | 标签 |
| `description` | text | 描述 |
| `model_provider` | varchar(50) | dashscope / openai / anthropic / custom |
| `model_name` | varchar(100) | 模型名 |
| `api_key` | varchar(500) | API 密钥（加密存储） |
| `base_url` | varchar(500) | 自定义 API 地址 |
| `system_prompt` | text | 系统提示词 |
| `temperature` | float | 温度 (0-2) |
| `max_tokens` | int | 最大输出 token |
| `max_iters` | int | 最大 ReAct 迭代次数 |
| `memory_mode` | varchar(20) | inmemory / longterm |
| `status` | varchar(20) | active / inactive |
| `agent_scope_id` | varchar(100) | AgentScope 注册 ID |
| `is_connected` | bool | 连接状态 |
| `created_at` | datetime | 创建时间 |

**`ai_tools`** — 工具/MCP/Skill 配置

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int PK | 自增主键 |
| `agent_id` | FK → ai_agents (CASCADE) | 关联智能体 |
| `name` | varchar(200) | 工具名称 |
| `tool_type` | varchar(20) | mcp / skill |
| `config_json` | text | 工具配置 (JSON) |
| `enabled` | bool | 是否启用 |
| `created_at` | datetime | 创建时间 |

**`ai_conversations`** — 对话会话

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int PK | 自增主键 |
| `agent_id` | FK → ai_agents (CASCADE) | 关联智能体 |
| `title` | varchar(500) | 对话标题 |
| `status` | varchar(20) | active / archived |
| `agent_scope_session_id` | varchar(200) | AgentScope 会话 ID |
| `created_at` | datetime | 创建时间 |

**`ai_messages`** — 对话消息

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int PK | 自增主键 |
| `conversation_id` | FK → ai_conversations (CASCADE) | 关联对话 |
| `role` | varchar(20) | user / assistant / system |
| `content` | text | 文本内容 |
| `tool_calls` | text | 工具调用记录 |
| `blocks` | text | ContentBlock 结构 (JSON) |
| `reason` | varchar(30) | 结束原因 (normal / exceed_max_iters / stopped / error) |
| `tokens` | int | 总 token |
| `input_tokens` | int | 输入 token |
| `model_name` | varchar(100) | 使用的模型 |
| `created_at` | datetime | 创建时间 |

**`ai_tasks`** — Agent 任务

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int PK | 自增主键 |
| `agent_id` | FK → ai_agents (CASCADE) | 关联智能体 |
| `title` | varchar(500) | 任务标题 |
| `description` | text | 描述 |
| `status` | varchar(20) | pending / running / completed / failed |
| `result` | text | 结果 |
| `scheduled_at` | datetime | 计划时间 |
| `started_at` | datetime | 开始时间 |
| `finished_at` | datetime | 结束时间 |
| `created_at` | datetime | 创建时间 |

**`ai_execution_logs`** — 执行日志

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int PK | 自增主键 |
| `agent_id` | FK → ai_agents (CASCADE) | 关联智能体 |
| `task_id` | FK → ai_tasks (SET_NULL, nullable) | 关联任务 |
| `level` | varchar(10) | info / warn / error |
| `message` | text | 日志消息 |
| `metadata` | text | 元数据 (JSON) |
| `created_at` | datetime | 创建时间 |

## 数据入库/出库规则

### 入库（INSERT/UPDATE）— 三条路径

```
前端 HTTP ──→ Django View ──→ api.py 函数 ──→ ORM 写入 DB
AgentScope ──→ Tool.call() ──→ api.py 函数 ──→ run_sync() ──→ ORM 写入 DB
Django Admin ──→ ORM ──→ DB（仅管理员）
```

> **核心约束**：所有写操作必须通过 `api.py` 函数，禁止直接 ORM 写入（防火墙 #2）。

### 出库（SELECT）— 两种方式

| 场景 | 方式 |
|------|------|
| 同模块内读取 | 直接 ORM 查询 |
| 跨模块读取 | 直接 ORM 查询（防火墙 #2：读放开） |

### 级联规则

| 关系 | 规则 |
|------|------|
| `el_pages` → `el_elements` | CASCADE（删页面同时删元素） |
| `el_pages` → `el_page_flows` | CASCADE（删页面同时删跳转流） |
| `ai_agents` → `ai_tools` / `ai_conversations` / `ai_tasks` / `ai_execution_logs` | CASCADE |
| `ai_conversations` → `ai_messages` | CASCADE |
| `dp_devices` → `dp_device_locks` | CASCADE |
| `dp_devices` → `dp_device_queue` | CASCADE |
| `tr_test_runs` → `tr_test_results` | CASCADE (nullable) |
| `el_elements` → `el_page_flows` (trigger) | SET_NULL |
| `el_pages` → `dp_devices` | SET_NULL（设备删除后页面保留） |

### 设备状态生命周期

```
(new) → ONLINE ⇄ BUSY → OFFLINE / DISCONNECTED → ONLINE
```

- **device-pool api.py** 同时写 `dp_devices.status` + `dp_device_locks`（双写，锁审计永不删）
- **lock_device**：检查设备 ONLINE → 创建锁记录 → 更新 status=BUSY
- **release_device**：更新锁状态 → 检查队列是否有等待者 → 自动分配或设 status=ONLINE

### AI 对话消息入库路径

```
SSE 流 → save_message (前端调用) → ai_messages 表（含 blocks JSON）
      → AgentScope 自动写 Redis (session 状态)
```

> Redis 存储 AgentScope 会话和消息总线状态（由框架自动管理）；Django DB 存储业务数据（由 save_message API 手动写入）。

## 命名约定

| 层级 | 规范 | 示例 |
|------|------|------|
| 数据库表 | `{prefix}_{snake_case}` | `dp_devices`, `cm_test_definitions` |
| Model 类 | `PascalCase` | `Device`, `TestDefinition`, `TestRunRecord` |
| 外键字段 | `{related_name}_id` | `device_id`, `run_id` |
| 前缀 | `dp_` `el_` `cm_` `tr_` `rg_` `ai_` | 对应 6 个模块 |
