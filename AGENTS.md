# AGENTS.md — Android-AutoTests

## 项目概述

AI 驱动的 Android UI 自动化测试平台。前后端分离：Vue 3 + Vite 前端，Django 纯 API 后端，AgentScope 2.0 AI 引擎。通过 uiautomator2 + ADB 连接 Android 设备，提供：UI 层级检查、元素定位（8 种 XPath 策略）、14 种步骤的用例编排、数据驱动压力测试、报告生成、AI 智能助手。

## 启动方式

```bash
cd Android-AutoTests

# 安装依赖
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 数据库初始化（首次运行）
python manage.py migrate
python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_superuser('admin','admin@local','admin123') if not User.objects.filter(username='admin').exists() else None"

# 知识库初始化（AI 助手 RAG，首次运行）
python agentscope_service/rag/init_kb.py

# 一键启动（Django + AgentScope + Vite）
python run.py start

# 管理
python run.py stop       # 停止
python run.py restart    # 重启
python run.py status     # 状态
python run.py logs       # 日志

# 离线工具（独立使用，不需要服务器）
python dump_ui.py          # dump UI 层级 → ui_data.json + screenshot.png
python generate_html.py    # 生成自包含 phone_ui.html 检查器
```

> **AgentScope AI 依赖 Redis**。Redis 不可用时 AgentScope 无法启动，AI 对话自动降级到 Django 阻塞模式。

## 架构

```
┌──────────────────────────────────────────────────────────────────┐
│  Vue 前端 :5173 (Vite + Element Plus + animal-island-vue)        │
│  src/modules/{7模块}/                                             │
│    ├── index.vue · routes.js · api.js                             │
│    ├── store.js · composables/ · components/                      │
│                                                                   │
│  Vite proxy: /api → :8765, /ws → :8765                           │
│              /agentscope → :8000, /agentscope-stream → :8000      │
├─────────────┬────────────────────────────────────────────────────┤
│             │ HTTP REST + WebSocket (JWT Bearer)                  │
│             ▼                                                     │
│ ┌──────────────────────────┐  ┌──────────────────────────────┐  │
│ │ Django :8765              │  │ AgentScope :8000              │  │
│ │ Daphne + Channels         │  │ FastAPI + Uvicorn             │  │
│ │                           │  │                               │  │
│ │ gateway/                  │  │ agentscope_service/           │  │
│ │   JWT 中间件 + WS 路由     │  │   14 自定义 Tool              │  │
│ │                           │  │   5 Worker 模板 (Agent Team)  │  │
│ │ apps/ (6个)               │  │   ChromaDB 知识库 (32篇)      │  │
│ │   element_locator · dp    │  │                               │  │
│ │   case_manager · tr       │  │                               │  │
│ │   report_generator · ai   │  │                               │  │
│ │                           │  │                               │  │
│ │ shared/auth/  JWT         │  │                               │  │
│ └──────────┬───────────────┘  └──────────────┬─────────────────┘  │
│            │  Django ORM                     │  Redis             │
│            ▼                                  ▼                    │
│ ┌──────────────────┐              ┌──────────────────┐           │
│ │ SQLite / MySQL   │              │ Redis :6379      │           │
│ └──────────────────┘              │ Storage+MsgBus   │           │
│                                   └──────────────────┘           │
│            │                                                      │
│            │ uiautomator2 → ADB                                   │
│            ▼                                                      │
│       Android 设备                                                 │
└──────────────────────────────────────────────────────────────────┘
```

## 项目结构

```
├── run.py                     # 一键启停 Django + AgentScope + Vite
├── run_agentscope.py          # AgentScope 独立启动
├── manage.py                  # Django CLI
├── requirements.txt           # Python 依赖 (agentscope, fastapi, uvicorn, pyjwt, chromadb...)
│
├── config/                    # Django 项目配置
│   ├── settings.py            # DB · Channels · CORS · Redis · AgentScope · JWT
│   ├── urls.py                # include('apps.{name}.urls') × 6 + admin
│   ├── asgi.py                # Daphne 入口 (HTTP + WS)
│   └── agentscope_config.py   # AgentScope 服务配置
│
├── gateway/                   # 网关层
│   ├── middleware.py           # JWTAuthenticationMiddleware
│   └── routing.py              # WebSocket 中央路由
│
├── shared/                    # 共享服务
│   └── auth/
│       └── jwt_auth.py        # JWT 签发 · 验证 · 黑名单 (Django + AgentScope 共享)
│
├── apps/                      # Django 业务模块 (6 个)
│   ├── device_pool/           # ✅ · 5 端点 · dp_devices/locks/queue
│   ├── element_locator/       # ✅ · 11 端点 · el_pages/elements/flows
│   ├── case_manager/          # ✅ · 8 端点 · cm_test_definitions/cases
│   ├── test_runner/           # ✅ · 4 端点 · tr_test_runs/results
│   ├── report_generator/      # ✅ · 2 端点 · rg_reports/templates
│   └── ai_assistant/          # ✅ · 13 端点 · ai_agents/tools/conversations/messages/tasks/execution_logs
│
├── agentscope_service/        # AgentScope AI 服务
│   ├── app.py                 # FastAPI create_app 入口
│   ├── auth.py                # JWT 依赖注入
│   ├── agent_factory.py       # Django AIAgent → AgentScope Agent
│   ├── tools/                 # 14 个自定义 Tool
│   │   ├── element_tools.py   #   get_test_points, search_elements
│   │   ├── case_tools.py      #   save_test_case, get_test_case, list_test_cases
│   │   ├── device_tools.py    #   get_online_devices, acquire_device, release_device
│   │   ├── runner_tools.py    #   run_test, get_run_results, stop_run
│   │   ├── report_tools.py    #   save_report, list_reports
│   │   ├── rag_tool.py        #   search_knowledge_base
│   │   └── factory.py         #   工具注册工厂
│   ├── teams/                 # 5 个 SubAgent 模板 + Leader prompt
│   └── rag/                   # ChromaDB 文档存储 + 加载器 + 初始化脚本
│
├── models/                    # Python dataclass (跨模块共享)
│   ├── step_types.py          # StepType 枚举 (14 种) + TestStep
│   └── test_models.py         # TestCaseDef · TestResult · TestRun
│
├── frontend/                  # Vue 3 + Vite 独立工程
│   ├── package.json
│   ├── vite.config.js         # Element Plus 按需引入 · manualChunks 分包 · proxy
│   └── src/
│       ├── main.js            # Vue 入口 (Element Plus + animal-island-vue)
│       ├── App.vue            # 根组件 (Cursor + Footer + 侧边栏 + blob)
│       ├── router.js          # SPA 路由 + JWT beforeEach 守卫
│       ├── style.css          # 全局 CSS 变量 · 毛玻璃 · 字体
│       ├── views/
│       │   └── LoginView.vue  # 平台统一登录页 (动森主题)
│       ├── shared/
│       │   ├── api-client.js  # Axios (JWT 拦截 · 401 刷新 · AgentScope 客户端)
│       │   ├── event-bus.js   # mitt 事件总线
│       │   ├── animations.js  # blob 视差 + 导航动画
│       │   ├── components/
│       │   │   └── AppSidebar.vue  # 导航 (7 模块) + 用户 + 退出
│       │   └── icons/
│       │       └── index.js   # 24 个自定义 SVG 图标 (h() 渲染函数)
│       └── modules/           # 7 个前端业务模块
│           ├── dashboard/          # 仪表盘
│           ├── device-pool/        # 设备管理
│           ├── element-locator/    # 元素定位
│           ├── element-manager/    # 元素管理
│           ├── case-manager/       # 测试用例
│           ├── test-runner/         # 执行引擎
│           ├── report-generator/   # 测试报告
│           └── ai-assistant/       # AI 助手 (animal-island-vue 动森主题)
│               ├── index.vue       #   智能体卡片网格
│               ├── AgentDetail.vue #   5 步配置向导
│               ├── ChatView.vue    #   SSE 流式对话
│               ├── api.js          #   AgentScope SSE 封装
│               └── animal-theme.css #  动森 CSS 变量覆盖
│
├── dev_docs/         # 项目文档（Stage-Gate 主目录平铺，只认新路径）
│   ├── 立项验证/ · 02-PRD需求/ · 03-设计与架构/
│   ├── 04-任务拆分/ · 05-开发与测试/ · 06-发布与复盘/
│   ├── 00-管理员/ · 00-智能体/
│   └── index.html              # 文档索引入口
│
├── data/                      # SQLite + avatars/ + screenshots/ + chromadb/
├── logs/                      # backend / agentscope / frontend 日志
├── exports/                   # YAML 导出
│
├── dump_ui.py                 # 离线 dump 工具
├── generate_html.py           # 离线 HTML 生成 (phone_ui.html)
└── migrate_sqlite_to_mysql.py # SQLite → MySQL 数据迁移
```

## 模块通信规则（三道防火墙）

```
防火墙 #1: service.py 互不 import
  ✅ 跨 App import Model (只读) + api.py (复杂写)
  ❌ 跨 App import service / 内部实现

防火墙 #2: 读放开，写收敛
  ✅ 跨 App 读 (SELECT): 直接 ORM
  ❌ 跨 App 写 (INSERT/UPDATE/DELETE): 必须走 api 函数

防火墙 #3: 外部访问只走 API
  Vue → HTTP → Django API → ORM → DB
  AgentScope → Tool → Django ORM/API (同进程，不走 HTTP)
  Django Admin → ORM → DB (管理员专用)
```

```python
# ✅ 允许：跨 App import Model（只读）
from apps.device_pool.models import Device
device = Device.objects.get(serial="...")

# ✅ 允许：跨 App import api.py（复杂写操作）
from apps.device_pool.api import acquire_device
acquire_device(serial="...", user_id="...", timeout=300)

# ❌ 禁止：跨 App import service / 内部实现
from apps.device_pool.service import allocate_device

# ❌ 禁止：跨 App 直接 ORM 写操作
Device.objects.update(status="ONLINE")  # 在别的 App 代码里
```

## 数据库 (6 组前缀，18 张表)

| 模块 | 表 | 说明 |
|------|-----|------|
| device-pool (`dp_`) | `dp_devices` `dp_device_locks` `dp_device_queue` | 设备 + 锁 + 排队 |
| element-locator (`el_`) | `el_elements` `el_pages` `el_page_flows` | 元素 + 页面 + 跳转 |
| case-manager (`cm_`) | `cm_test_definitions` `cm_test_cases` | 用例定义 + YAML 缓存 |
| test-runner (`tr_`) | `tr_test_runs` `tr_test_results` | 执行记录 + 结果 |
| report-generator (`rg_`) | `rg_reports` `rg_report_templates` | 报告 + 模板 |
| ai-assistant (`ai_`) | `ai_agents` `ai_tools` `ai_conversations` `ai_messages` `ai_tasks` `ai_execution_logs` | 智能体 + 工具 + 对话 + 消息 + 任务 + 日志 |

## API 端点 (37 REST + 2 WebSocket)

| 前缀 | 模块 | 端点数 |
|------|------|:--:|
| `/api/elements/*` | element-locator | 11 |
| `/api/devices/*` | device-pool | 5 |
| `/api/cases/*` | case-manager | 8 |
| `/api/runner/*` | test-runner | 4 |
| `/api/reports/*` | report-generator | 2 |
| `/api/ai/*` | ai-assistant | 18 (含 5 auth + 8 agent + 5 chat) |
| `/agentscope/*` | AgentScope FastAPI | 动态 (chat/sessions/agent/credential...) |
| `/ws/screenshot` | element-locator | 2fps 截图流 |
| `/ws/test-run/{id}` | test-runner | 6 种消息类型 |

> 统一响应格式：`{"ok": true, "data": {...}}` 或 `{"ok": false, "error": "..."}`

## 新增 App 时的框架注册（4 个文件各 1 行）

| 文件 | 操作 |
|------|------|
| `config/settings.py` | `INSTALLED_APPS` 加 1 行 |
| `config/urls.py` | `include('apps.{name}.urls')` |
| `frontend/src/router.js` | `import` 模块路由汇总 |
| `frontend/src/shared/components/AppSidebar.vue` | `navItems` 加菜单项 |

> AgentScope Tool 增加：在 `agentscope_service/tools/{domain}_tools.py` 新增 ToolBase 子类 → 在 `factory.py` 注册。

## AgentScope 自定义 Tool 清单 (14 个)

| Tool | 模块 | 只读 | 说明 |
|------|------|:--:|------|
| `get_test_points` | element-locator | ✅ | 获取测试点元素 |
| `search_elements` | element-locator | ✅ | 搜索 UI 元素 |
| `save_test_case` | case-manager | ❌ | 创建/更新用例 (含 14 种步骤) |
| `get_test_case` | case-manager | ✅ | 获取用例详情 |
| `list_test_cases` | case-manager | ✅ | 列出已启用用例 |
| `get_online_devices` | device-pool | ✅ | 在线设备列表 |
| `acquire_device` | device-pool | ❌ | 锁定设备 |
| `release_device` | device-pool | ❌ | 释放设备 |
| `run_test` | test-runner | ❌ | 执行测试 (支持循环) |
| `get_run_results` | test-runner | ✅ | 查询执行结果 |
| `stop_run` | test-runner | ❌ | 停止执行 |
| `save_report` | report-generator | ❌ | 保存报告 |
| `list_reports` | report-generator | ✅ | 列出报告 |
| `search_knowledge_base` | ChromaDB | ✅ | 知识库向量检索 |

> Tool 文件在 `agentscope_service/tools/`，直接调用 Django ORM/API（同进程，不走 HTTP）。

## 配置

| 参数 | 默认值 | 环境变量 |
|------|--------|---------|
| `DEVICE_SERIAL` | `RF8N21MSW7A` | `DEVICE_SERIAL` |
| `SCREENSHOT_INTERVAL` | `0.5`s | `SCREENSHOT_INTERVAL` |
| `DB_ENGINE` | `sqlite` | `DB_ENGINE` (mysql 切换) |
| `REDIS_URL` | `redis://localhost:6379/0` | `REDIS_URL` |
| `AGENTSCOPE_PORT` | `8000` | `AGENTSCOPE_PORT` |
| `JWT_ACCESS_TTL` | `3600` (1h) | `JWT_ACCESS_TTL` |
| Django Admin | `/admin/` | admin / admin123 |

## 注意事项

- **AgentScope 依赖 Redis**：Redis 不可用时 AgentScope 无法启动，AI 对话自动降级到 Django 阻塞模式
- **设备依赖**：所有 u2 操作需要 ADB 设备连接，无设备时 API 返回友好提示
- **阻塞操作**：uiautomator2 调用是阻塞的 — Django 同步视图在 Daphne 工作线程中运行
- **async 视图**：仅 `POST /api/runner/run` 使用 `async def`，通过 `asyncio.create_task()` 后台执行
- **Channels**：开发环境优先 Redis（`channels_redis`），不可用时回退 InMemoryChannelLayer
- **CORS**：开发环境 `CORS_ALLOW_ALL_ORIGINS = True`
- **前端**：Vite proxy 转发 `/api`/`/ws` 到 `:8765`，`/agentscope` 到 `:8000`。Element Plus 按需引入（unplugin-vue-components）
- **JWT 鉴权**：Django + AgentScope 共享 `SECRET_KEY`。`LoginView.vue` 是平台唯一登录入口，`beforeEach` 守卫保护全部路由
- **AI 模块主题隔离**：AI 助手使用 animal-island-vue（暖木色/大圆角），业务模块保持 Element Plus 蓝白风格。动森 CSS 变量在 `animal-theme.css`
- **XPath**：`gen_xpath_candidates()` 按匹配数升序排列，优先选 count=1
- **命名**：后端 `snake_case`，前端 `kebab-case`，API URL `kebab-case`，JSON 字段 `snake_case`，Vue 组件 `PascalCase.vue`
- **14 种步骤**：`click` `click_indexed` `wait` `wait_disappear` `wait_either` `wait_toast` `verify_text` `poll_text` `sleep` `kill_app` `start_app` `restart_app` `retry_click` `log`
