# 平台架构设计 — Android-AutoTests

> 版本 v1.2 · 2026-10-29 · 基线：`Kahoku` 主干  
> **平台开发目标：** 一切皆插件；实现 **AI Model + Harness**，让用户可通过本平台自由创建 Agent，规划并完成任务。  
> **与 AGENTS 的关系：** 总思路与强制阅读落点见根 [`AGENTS.md`](../../AGENTS.md)；engines 落地红线见 [`engines/AGENTS.md`](../../engines/AGENTS.md)。本文是架构说明书：给 AI 与人对齐「为什么这样分」和「现状如何接线」。

---

## 1. 系统定位与边界

### 1.1 一句话定位

Android 自动化测试与智能体平台：**前端只展示，后端只做通道与记账，`engines/` 承载平台全部可执行能力**；核心产品形态是可配置的 **Agent 角色**。

### 1.2 技术栈

1. 后端，纯 API：Django 4.2 + DRF + Channels  
2. 前端，纯 SPA：Vue 3.4 + Vite + Element Plus  
3. AGENT 框架：AgentScope 2.0  
4. 其它：uiautomator2/ADB（设备）· MySQL/SQLite + Redis  

### 1.3 请求链路

前端模块 `api.ts` → `djangoClient`(`/api`) → Vite 代理 → `JWTAuthenticationMiddleware` → DRF View → `EnvelopeJSONRenderer`（`{status,data}`）→ ORM。

### 1.4 约定

1. 表前缀：`dp_` `cm_` `ai_` `task_` `rg_` `wf_` `sl_` 等（以各 App Model 为准）  
2. 响应信封：`{status,data}`  
3. `APPEND_SLASH = False`：缺尾斜杠确定 404，避免 301 丢 `Authorization`

---

## 2. 平台核心：Agent = Model + Harness

**结论先行：** 平台能力不是散落在各个 Django App 里的业务函数，而是 **Model + Harness 组合成的 Agent 角色**。用户（与 AI 实现时）应围绕「创建/配置角色、装配 Harness、下发任务、计量展示」推进，而不是把自动化逻辑写进 View。

### 2.1 三层分工

| 层 | 位置 | 职责 | 不该做的事 |
| --- | --- | --- | --- |
| 展示 | `frontend/` | 任务、花费、能力、运行状态可视化 | 不直连设备/模型，不承载 SOP 逻辑 |
| 通道与记账 | `backend/`（`apps` + gateway） | 鉴权、任务下发、会话/WS 接入；把花费、能力与任务写入数据库 | 不实现设备控制/OCR/串口采集内核；不旁路 engines 绑工具 |
| 能力核心 | `engines/` | Agent 运行时 + Harness + device/uart_log/vision 支撑 | 不 `import apps.*` / `django.*`；不写业务库 |

依赖方向：**backend →（注入）→ engines**。

### 2.2 Model、Harness、角色

- **Model**：推理与生成（DeepSeek、Dashscope / Omni 等），由角色配置选用。  
- **Harness**（集中在 `engines/agents/`）：角色跑起来所需外围能力  
  - 工具：`tools/tool_*.py` + **唯一分配入口** `tools_config.py`  
  - 技能：`skills/`  
  - 知识库：`rag/`（MCP 等见 `mcp_config/`）  
  - 记忆与上下文：会话/历史与当轮上下文（messaging、语音 session/pipeline 等；RAG 只注入当轮，不进长期历史）  
  - 提示词：`prompts/` + **唯一配置入口** `prompt_config.py`  
- **角色**：`role/`，继承 `base.BaseRole`，把选定 Model 与 Harness 装配成可下发、可计量的 Agent。  
- **工作流**：`workflow/` 管 SOP 步骤与单次运行；**禁止**在此创建角色或旁路绑定工具/提示词。

### 2.3 Harness 的控制与数据底座

| 包 | 给 Harness 提供什么 |
| --- | --- |
| `engines/device` | 设备动作（对外入口 `action`） |
| `engines/uart_log` | 串口日志采集与处理 |
| `engines/vision` | 页面 OCR，供引擎侧工具调用 |

上述能力经 `tool_*.py` 暴露给角色，**禁止**上层直接 import `airtest` / `uiautomator2` 绕过引擎。

### 2.4 花费、任务与展示闭环

1. 后端下发任务 / 建立会话 → 注入配置与密钥（解密后交给 engines）  
2. engines 执行 Agent（SOP / 语音等）→ 产生事件与用量（messaging / billing、`model_usage` 等）  
3. 后端写入 DB（任务事件、用量、费用汇总）  
4. 前端展示时间线、仪表盘与报告  

**一切皆插件（目标态）：** 新能力优先以 Harness 插件（工具/技能/知识/MCP）或可替换 engines 子包进入，而不是在某个 App 的 View 里堆协议细节。现状仍以代码目录与配置入口约束为主；插件市场级热插拔不在本文承诺范围。

### 2.5 AI 实现时的优先顺序

1. 改展示/API/表结构 → 读本文 §3–§8 + 对应 App  
2. 改 Agent / 工具 / 提示词 / RAG / 语音 → 根 `AGENTS.md` §平台架构 + `engines/**/AGENTS.md` + style rules  
3. 不要把「本该是 tool/skill」的逻辑写进 DRF View 或前端

---

## 3. 运行时拓扑

```
浏览器 :5173 ──HTTP──→ Vite（/api、/media、/ws 代理）
                              │
                              ▼
                    Daphne :8766（ASGI）
                    backend/config/asgi.py: ProtocolTypeRouter
                       ├─ http      → Django（中间件 → URLconf → DRF）
                       └─ websocket → /ws/knowledge-assistant/
                              │
        ┌─────────────────────┼──────────────────────────┐
        ▼                     ▼                          ▼
   MySQL / SQLite          Redis :6379              engines（同进程）
   （业务数据）        （JWT 吊销 / Channels）    AgentScope + device/uart/vision
                                                          │
                                              Android 设备 / 串口日志
```

### 3.1 进程与入口

| 进程 | 端口 | 入口 | 说明 |
|------|------|------|------|
| Redis | 6379 | `redis-server` | JWT 吊销、Channels layer；`run.py stop` **不**停 Redis |
| Daphne | 8766 | `run_daphne.py` → `backend.config.asgi:application` | 开发态 autoreload 双进程；生产态单进程 |
| Vite | 5173 | `npx vite --host` | 代理 `/api`、`/media`、`/ws` |

- 统一运维：`python run.py start|stop|restart|status|logs|check`  
- 启动副作用受门控：孤儿任务恢复、串口监听恢复仅在 ASGI 服务进程（`DJANGO_ASGI_SERVER=1` 或 argv 含 `daphne`/`runserver`）；`migrate`/`shell`/`pytest` 不触发  
- `run.py stop backend` 会清理 MySQL `Sleep>5` 孤儿连接  

### 3.2 中间件链（`backend/config/settings.py`）

```
Cors → Security → GZip → Session → Common → JWTAuthenticationMiddleware
     → CsrfViewMiddleware → Authentication → Message → XFrameOptions
```

- `JWTAuthenticationMiddleware`（`backend/gateway/middleware.py`）：`/api/*` 前置 JWT，注入 `request.user_id`；公开前缀含登录注册刷新、`/admin/`、`/static/`、`/media/`、schema/swagger  
- JWT 有效时置 `_dont_enforce_csrf_checks`；后台 session 面仍受 CSRF  
- DRF：`JWTAuthentication` + `IsAuthenticated` + `EnvelopeJSONRenderer`；`UNAUTHENTICATED_USER=None`  

### 3.3 Channels

仅生产路由 `/ws/knowledge-assistant/`（知识库助手，`?mode=voice|text`）。握手 `?token=` 调 `verify_token`，失败 4401；非法 `mode` 4400。通道只承载语音音频/转写/打断/播放进度与文字提问；**任务进度仍走 HTTP 轮询**。其它模块不得复用该通道做任务/设备/写操作。

---

## 4. 分层与依赖规则

```
前端（Vue 模块）
   │ 唯一 HTTP 出口 shared/api-client.ts
   ▼
接口层：gateway 中间件 → urls → View/ViewSet → Serializer
   ▼
应用层：backend/apps/*/api.py（唯一写库口）→ ORM
   ▼
引擎层：engines/agents（角色/Harness/SOP）· device · uart_log · vision
   ▼
外部：Android、串口、模型 API、Redis、MySQL
```

| # | 规则 | 强制手段 |
|---|------|---------|
| 1 | View 只分发；写库必须经本 App `api.py` | `utils/gen_arch_stats.py --check-boundaries` |
| 2 | 跨 App **禁止** import 内部实现（读 Model 允许） | 同上 + review |
| 3 | 跨 App 写只能调对方 `api.py` | 同上 |
| 4 | 上层不得 import `airtest` / `uiautomator2`，设备只经引擎 | boundary-check + `engines/device/action.py` |
| 5 | 前端只有一个 axios / HTTP 出口 | `frontend/.dependency-cruiser.cjs` |
| 6 | `/api/` 无强制尾斜杠、`{status,data}`、snake_case | pytest 契约 + `EnvelopeJSONRenderer` |
| 7 | agents 工具/提示词必须经 `tools_config` / `prompt_config` | `engines/**/AGENTS.md` + style-check 技能 |

信封特例：无。报告文件下载保持 `FileResponse` 附件语义。

---

## 5. engines 能力地图（落地索引）

| 路径 | 职责 | 详细约束 |
|------|------|----------|
| `engines/AGENTS.md` | engines 必读入口、红线、何时读 rules/跑检查 | 本文不重复全文 |
| `engines/agents/` | Agent 运行时与 Harness | `engines/agents/AGENTS.md` |
| `engines/agents/rag/` | 本地知识检索 | `engines/agents/rag/AGENTS.md` |
| `engines/agents/realtime_vocie/` | 实时语音引擎（目录名为历史拼写） | `engines/agents/realtime_vocie/AGENTS.md` |
| `engines/device/` | 设备引擎，`action` 对外 | 尚无独立 AGENTS；遵守上层红线 |
| `engines/uart_log/` | 串口采集 | 同上 |
| `engines/vision/` | OCR | 同上 |

风格正文：`.agents/rules/engines-code-style.md`。机械化检查：`.agents/skills/engines-agents-style-check/`。

---

## 6. 后端：模块、端点与数据

### 6.1 模块总览

> 端点数量随迭代变化；接口真值以 `openspec/openapi.yaml` 与 `openspec/specs/` 为准。下表侧重**职责**，便于 AI 选型。

| App | API 前缀（典型） | 职责 |
|-----|------------------|------|
| `accounts` | `/api/auth/` | JWT 双令牌 + Redis 吊销 |
| `dashboard` | `/api/dashboard/` 等 | KPI、趋势、用量费用、活动时间线（聚合） |
| `device_pool` | `/api/devices/` | 设备扫描/连接/占用/心跳 |
| `case_manager` | `/api/cases/` | 用例项目/目录/文件/步骤 |
| `task_list` | `/api/tasks/` | 任务提交/控制/事件/报告入口 |
| `ai_assistant` | `/api/ai/` | 智能体配置、模型线路、密钥 |
| `knowledge_assistant` | `/api/knowledge-assistant/` + WS | 知识库助手接入（通道）；引擎在 `engines` |
| `report_generator` | `/api/reports/` | 报告列表/详情/下载 |
| `serial_log` | `/api/serial-log/` | 串口端口开关与日志相关 API |
| `workflow` | `/api/workflow/` | 页面流原型/目录/文档 |
| `bug_manager` | （按 urls） | BUG 单管理 |
| `usage_ledger` | （按 urls） | 用量记账相关 |

### 6.2 数据模型要点

| 分组 | 关键设计 |
|------|----------|
| `dp_` | 设备 `ONLINE/BUSY`；锁只追加；同设备单活跃锁 |
| `cm_` | 项目/目录/文件唯一约束；用例步骤 `sort_order` |
| `ai_` | 智能体与线路；`route_configs` 内密钥 Fernet 加密 |
| `task_` | 事件 `UNIQUE(task,seq)`；缩略图去重；小时用量表 |
| `rg_` | 报告文件落盘 + 元信息 |
| `wf_` | 画布 JSON；目录树与用例管理同构 |
| `sl_` | 端口开关；端口/SKU/波特率以配置为真相源 |

模型配置：`ai_agents.route_configs` 存模型名/provider/base_url 与加密 `api_key`；读取脱敏，`reveal-key` 一次性揭示。

### 6.3 鉴权与身份

- access TTL 1h、refresh TTL 7d；同登录共享 `sid`  
- 吊销：`jwt:blacklist:{jti}`、`jwt:session_revoked:{sid}`；读侧 fail-open，写侧 fail-closed  
- AI 智能体写操作仅超管；读按 owner 或共享规则过滤；`backend/shared/users.py::is_superuser` 为跨 App 唯一实现  

---

## 7. 前端架构

| 模块 | 路由（典型） | 后端 |
|------|--------------|------|
| dashboard | `/dashboard` | dashboard API |
| device-pool | `/devices` | `/api/devices/*` |
| workflow | `/workflow`… | `/api/workflow/*` |
| serial-log | `/serial-log` | `/api/serial-log/*` |
| ai-assistant | `/ai-assistant`… | `/api/ai/*` |
| task-list | `/tasks`… | `/api/tasks/*` |
| case-manager | `/cases`… | `/api/cases/*` |
| report-generator | `/reports` | `/api/reports/*` |
| knowledge-assistant | `/knowledge-assistant` | HTTP + `/ws/knowledge-assistant/` |

- 侧栏：主区 / AI 功能 / 数据 / AI 任务  
- 请求：模块 `api.ts` → `shared/api-client.ts`；401 单飞刷新  
- 状态：Pinia 主要在 workflow；token 在 localStorage  
- 设计令牌：`shared/styles/tokens.css`  
- 实时性：任务轮询；唯一 WS 为知识库语音  

---

## 8. 关键数据流

### 8.1 设备接入与占用

```
/scan → DeviceDetector(adb devices) → dp_devices
/lock → dp_device_locks(active)（唯一约束挡并发）
/heartbeat → 超时 released(timeout)
/disconnect → 删设备行 + 锁转 disconnect
```

### 8.2 用例 → 任务装配

```
cm_* 用例树 → POST /api/tasks/submit/
  → api.create_task → 物化配置 → dispatch_device(serial)
```

### 8.3 任务执行与回看（Agent 闭环）

```
daemon: task_runner
  → 解密角色/模型配置（通道）
  → engines：SOP / Agent（Model + Harness）
  → 事件与用量回传 → 入库 task_events / media / usage
  → finalize_task（状态 + 费用）
  → 前端任务详情 / 报告 / dashboard
```

### 8.4 证据闭环

```
executor 动作 → 设备/串口日志 → 关键词命中
  → verifier 判决 → 事件入库 → 失败原因回灌 executor
```

---

## 9. 可观测与运维

| 面 | 实现 |
|----|------|
| 后端 | `logs/backend.log` |
| 智能体 | `logs/agents/agent_events.log` |
| 设备 | `logs/device.log` |
| 串口 | `logs/serial.log` + `logs/serial_logs/{SKU}_{port}.log` |
| 轮转 | 通常 10MB×3；串口原文更大后归档 |
| 健康 | `python run.py status` |
| 自愈 | 启动将遗留 `running` 置 `failed`；按开关恢复串口监听 |

框架日志默认走控制台，不写独立 `django.log`。

---

## 10. 质量治理

| 手段 | 用途 |
|------|------|
| `python run.py check` | 本地门禁（与 CI 同批阻塞项） |
| `ci-phase1.yml` | 推送后质量闸门 |
| OpenSpec + `openspec/openapi.yaml` | 能力/接口契约 |
| boundary-check | App/引擎依赖防火墙 |
| `engines-agents-style` 技能/门禁 | agents 可自动化风格子集（非阻塞告警） |
| 根 `AGENTS.md` Git 约定 | 单主干 Kahoku、禁止强推、禁止 `git add -A` |

---

## 11. 文档与 AI 阅读指引

| 场景 | 先读 |
|------|------|
| 理解平台总思路（Model + Harness） | 根 `AGENTS.md`「平台架构定位」+ **本文 §2** |
| 新建 Agent 角色 | [GUIDE-创建Agent清单.md](GUIDE-创建Agent清单.md) |
| Harness 硬约束（OpenSpec） | [../../openspec/specs/agent-harness/spec.md](../../openspec/specs/agent-harness/spec.md) |
| 改 engines / Agent / Harness | `engines/AGENTS.md` → 子 AGENTS → `.agents/rules/engines-code-style.md` |
| 改 API / 表 / 鉴权 / 拓扑 | **本文 §3–§6、§8** + 对应 App |
| 改前端模块与路由 | **本文 §7** + 模块目录 |
| 接口字段真值 | `openspec/specs/`、`openspec/openapi.yaml` |
| 临时文件 | 必须进 `temps/`；设计稿在 `dev_docs/` |

---

## 12. 已知限制与技术债

1. **无通用实时推送**：任务进度靠轮询。  
2. **设备连接复用不足**：工具调用侧连接开销尚未量化。  
3. **前端信封拆包不统一**：部分模块类型/错误处理不一致。  
4. **pytest marker / CI 深度**：收集门禁不等于运行期全量回归。  
5. **文档真值**：能力规格与 OpenAPI 是接口契约；README/本文/AGENTS 靠约定同步。  
6. **单 SKU 日志默认形态**：多设备需在 `DEVICE_LOG_SOURCES` 显式登记。  
7. **「一切皆插件」仍是目标态**：当前以目录 + 配置入口约束 Harness，而非热插拔插件市场。  
8. **`device` / `uart_log` / `vision` 尚无独立 AGENTS**：改这些包时以 `engines/AGENTS.md` 为准。

---