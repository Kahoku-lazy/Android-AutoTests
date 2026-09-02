---
name: android-autotests-rules
description: |
  Android-AutoTests 项目编码规则的唯一索引与常驻摘要。
  写 Python / Vue / Django 代码、改 API、动数据库、跨模块改动、安全自查前必查。
  Keywords: 项目规则, 编码规范, 防火墙, 模块边界, API 约定, 表前缀, 响应信封, 安全铁律, 通信通道, 红线, 启动, 排障, rules, conventions, api-conventions
  Trigger: 写/改代码、跨模块改动、新增 Django App、动 models/views/api、前端改动、安全自查、遇到报错诊断、启动/健康检查时。
---

# Android-AutoTests 项目规则索引

> 本目录是项目规则的唯一现行落点，规则变更只改本目录。

## 通用规则速查（8 类）

### 1. 全局架构约束

  - 详情查阅 `references/architecture.md`
  - 🔴 **引擎边界（L1c engines/）**：`engines/` 是唯一可触碰第三方引擎库（airtest/uiautomator2）的层；上层（apps/gateway）禁直接 import 引擎库、禁 import `engines.android.*` 具体实现、禁访问裸句柄（`.airtest`/`.u2`），只经 `engines.base.UiEngine` 协议 + `engines.registry` 工厂消费设备能力。校验：`python tools/gen_arch_stats.py --check-boundaries`

### 2. 前端 UI 设计规则

- 全局统一 **Doodle Craft 主题**；前端 UI 开发与维护 **必须使用** `doodle-craft` skill
- 前端开发必须遵循`references/frontend.md` 编写规则

### 3. 后端开发规则

-- 详情查阅 `references/python-code.md`
- 表前缀：`dp_` `el_` `cm_` `tr_` `rg_` `ai_` `wf_` `ev_` `di_`；设备状态机 `(new)→ONLINE⇄BUSY→OFFLINE/DISCONNECTED→ONLINE`

### 4. 代码安全规则

- 🔴 禁止硬编码密码 / API Key / SECRET_KEY（用 `os.environ.get()`）
- 🔴 禁止认证绕过（JWT 无 token 必须 401；WebSocket `connect()` 必须验 JWT）
- 🔴 禁止数据隔离缺失（列表/查询按 `request.user_id` 过滤）
- 🔴 写操作 catch 禁止静默吞错（前端 ElMessage.error / 后端 logging）
- 🔴 API 响应 api_key 必须脱敏（`sk-***xxxx`），日志不输出 Key
- API Key 生命周期：加密写 → 脱敏读 → 后端解密用 → 禁导出；解密失败禁止 fallback 返回明文
- 错误响应不暴露堆栈 / 文件路径 / SQL；敏感字段黑名单（password / api_key / token / SECRET_KEY…）

> 细节 → `references/security.md`（风险分级 / AI 编码安全检查清单 / 敏感字段黑名单）


### 5. 接口协议编写规范

- 通信通道封闭集合（四条内部通道 + 禁止新协议 + Redis/外部 LLM 边界 + SSE 已移除）→ 唯一真相源 `references/architecture.md` §一，勿在其他文件复制
- 响应信封：`{status: true, data}` / `{status: false, message}`（错误不暴露技术术语）
- 三道防火墙：① service 互不 import（可跨 App import Model+api.py，禁内部实现）② 读放开写收敛（写必须走目标 api.py）③ 外部访问只走 API
- 写操作铁律：前端→View→api.py→ORM；AgentScope→Tool→api.py→ORM；禁任何组件直接 ORM 写
- 鉴权：Bearer JWT（公开路径除外）；所有业务视图 `@csrf_exempt`
- JSON 字段 snake_case，前端变量 camelCase；新增 App 必走检查清单

> 细节 → `references/api-conventions.md`（响应格式/防火墙/鉴权/分层交互）· `references/architecture.md`（通道）

### 6. AgentScope 开发参考资料

- AgentScope 已并入 Django 进程内模块 `apps/ai_assistant/agent_scope/`，无独立服务 / 端口
- 边界：禁止 AgentScope 直连数据库 / 直连设备；数据一律经 Django ORM / api.py（同进程直接调用）
- 依赖 Redis（JWT 黑名单 / Django Channels 层 / AgentScope 存储；不可用时降级）
- 红线：禁止在 `agent_scope/` 下新增 `adapters/` 或 `rag/`


## 关联技能

- 项目边界统一检查（模块边界/引擎边界/通信通道边界）→ `boundary-check` skill
- 后端关单门禁 → `django-backend-check` skill
- 前端关单门禁 → `vue-frontend-check` skill
- 代码健康/审查 → `code-health-check` / `quality-gate` skill
