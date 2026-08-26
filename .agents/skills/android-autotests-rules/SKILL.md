---
name: android-autotests-rules
description: |
  Android-AutoTests 项目编码规则的唯一索引与常驻摘要（迁移自 .claude/rules/）。
  写 Python / Vue / Django 代码、改 API、动数据库、跨模块改动、安全自查前必查。
  Keywords: 项目规则, 编码规范, 防火墙, 模块边界, API 约定, 表前缀, 响应信封, 安全铁律, 通信通道, 红线, 启动, 排障, rules, conventions, api-conventions
  Trigger: 写/改代码、跨模块改动、新增 Django App、动 models/views/api、前端改动、安全自查、遇到报错诊断、启动/健康检查时。
---

# Android-AutoTests 项目规则索引

> 本文是 11 份规则文件的**唯一索引 + 常驻摘要**。细节按需读 `references/`。
> 原 `.claude/rules/` 已整体迁移至此；`.claude/rules/` 保留为历史副本，规则变更只改本目录。

## 常驻规则（每次写代码前必过一遍）

### 模块防火墙（三道）

```
防火墙 #1: service.py 互不 import
  ✅ 跨 App import Model（只读）+ api.py（复杂写）
  ❌ 跨 App import service / runner / consumer / state_machine（内部实现）
防火墙 #2: 读放开，写收敛
  ✅ 跨 App 读（SELECT）直接 ORM
  ❌ 跨 App 写（INSERT/UPDATE/DELETE）必须走目标模块 api.py
防火墙 #3: 外部访问只走 API
  Vue → HTTP → Django API → ORM → DB
  AgentScope → Tool → api.py → run_sync → ORM（同进程）
  Django Admin → ORM（仅管理员）
```

### 通信通道（封闭集合）

平台只有五条通道，**禁止引入新协议**（gRPC/MQTT/Kafka/RabbitMQ/GraphQL/WebRTC）：

| # | 通道 | 协议 |
|:--:|------|------|
| ① | 前端 ↔ Django | HTTP REST + JWT |
| ② | Django → 前端 | WebSocket + JWT |
| ③ | 前端 → Django (AI SSE) | SSE + JWT |
| ④ | AgentScope → Django | 进程内直接调用 |
| ⑤ | Django ↔ 设备 | ADB |

### 写操作铁律

```
前端 HTTP → Django View → api.py → ORM
AgentScope → Tool.call() → api.py → run_sync() → ORM
Django Admin → ORM（仅管理员）
❌ 任何组件直接 ORM INSERT/UPDATE/DELETE
✅ 读操作放开（同模块/跨模块都可直接 ORM 查询）
```

### 安全铁律

```
🔴 禁止硬编码密码/API Key/SECRET_KEY（用 os.environ.get()）
🔴 禁止认证绕过（JWT 无 token 必须 401；WebSocket connect 必须验 JWT）
🔴 禁止数据隔离缺失（查询按 request.user_id 过滤）
🔴 写操作 catch 禁止静默吞错（必须 ElMessage.error / logging）
🔴 API 响应 api_key 必须脱敏（sk-***xxxx），日志不输出 Key
```

### 关键约定

- API 响应统一 `{status: true, data}` / `{status: false, message}`（错误不暴露技术术语）
- JSON 字段 snake_case，前端变量 camelCase
- 数据库表前缀：`dp_` `el_` `cm_` `tr_` `rg_` `ai_` `wf_` `ev_` `di_`
- 依赖方向：上层 import 下层；`device_pool` 是唯一底层；`dashboard`/`ai_assistant` 是聚合层

## 参考文件索引

| 文件 | 内容 | 何时读 |
|------|------|--------|
| `references/architecture.md` | 架构总纲：五通道、依赖方向、AgentScope 边界、dashboard 约束、模块增减、10 条红线 | 新增/删除模块、跨模块设计前 |
| `references/api-conventions.md` | API 格式、三道防火墙、鉴权、分层交互、新 App 检查清单 | 动 API / 新增 App 前 |
| `references/database.md` | 写操作铁律、设备状态机、表前缀 | 动 models / 写库前 |
| `references/security.md` | 安全风险分类、AI 编码安全清单、敏感字段黑名单 | 安全自查、代码评审时 |
| `references/python-code.md` | Python 命名/行数/import/类型注解/OOP/文件职责/异常/响应 | 写任何 Python 前 |
| `references/frontend.md` | 前端命名/行数/样式工程/共享组件/数据加载三态/状态管理/CSS 修复模式 | 写任何 Vue 前 |
| `references/backend.md` | Django App 结构、中间件/鉴权、配置约定、异步处理 | 动后端结构前 |
| `references/conventions.md` | 跨语言索引、设备测试步骤、XPath 策略、主题、JWT | 按需 |
| `references/setup.md` | 启动/重启验证/格式化命令/端口约定/跨平台启动 | 启动、健康检查时 |
| `references/troubleshooting.md` | 报错诊断速查表 + 分模块排查流程 | 遇到报错诊断时 |
| `references/agentscope-tools.md` | AgentScope 开发入口（指向 dev_docs/agentscope.md） | 开发 AgentScope 功能前 |

## 关联技能

- 边界/防火墙自动检查 → `boundary-check` skill
- 后端关单门禁 → `django-backend-check` skill
- 前端关单门禁 → `vue-frontend-check` skill
- 代码健康/审查 → `code-health-check` / `quality-gate` skill
