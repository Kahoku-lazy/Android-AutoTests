# 平台架构设计 — Android-AutoTests

> 版本 v1.0 · 2026-10-21 · 基线：`Kahoku` 主干
> 平台开发目标： 一切皆插件；实现 AI Model + Harness 模式，让用户可以通过这个平台自由创建 Agent 规划与完成任务。

---

## 1. 系统定位与边界

### 技术栈

1. 后端，纯 API: Django 4.2 + DRF + Channels
2. 前端，纯 SPA：Vue 3.4 + Vite + Element Plus
3. AGENT 框架：AgentScope 2.0
4. 其它: uiautomator2/ADB（设备）· MySQL/SQLite + Redis

### 请求链路

 **请求链路**：前端模块 `api.ts` → `djangoClient`(/api) → Vite 代理 → `JWTAuthenticationMiddleware` → DRF View → `EnvelopeJSONRenderer`（`{status,data}`）→ ORM。

### 约定

1. 表前缀 `dp_ di_ el_ cm_ tr_ rg_ ai_ task_ ev_ wf_` 
2. 响应信封 `{status,data}`

---

## 2. 运行时拓扑

```
浏览器 :5173 ──HTTP──▶ Vite dev server（/api、/media 代理）
                              │
                              ▼
                    Daphne :8766（ASGI，单进程）
                    config/asgi.py: ProtocolTypeRouter
                       ├─ http      → Django（中间件链 → URLconf → DRF）
                       └─ websocket → URLRouter(websocket_urlpatterns)   ← 当前为空
                              │
        ┌─────────────────────┼──────────────────────────┐
        ▼                     ▼                          ▼
   MySQL / SQLite        Redis :6379              AgentScope（同进程）
   （业务数据）      （JWT 吊销 / Channels layer）   SOP: executor ↔ verifier
                                                          │
                                                   engines/device → adb
                                                          │
                                              Android 设备 / 串口日志 :7005
```

### 2.1 进程与入口

| 进程 | 端口 | 入口 | 说明 |
|------|------|------|------|
| Redis | 6379 | `redis-server` | JWT 吊销键、Channels layer；`run.py stop` **不**停 Redis |
| Daphne | 8766 | `run_daphne.py` → `config.asgi:application` | 开发态 autoreload 双进程（父进程只监控），生产态单进程 |
| Vite | 5173 | `npx vite --host` | 代理 `/api`、`/media`；`/ws` 代理是遗留配置 |

- 统一运维入口：`python run.py start|stop|restart|status|logs|check`（`run.py`）。
- 启动副作用**受门控**：孤儿任务恢复、串口端口监听恢复只在 ASGI 服务进程的 daemon 线程里执行，条件是 `DJANGO_ASGI_SERVER=1` 或 argv 含 `daphne`/`runserver`（`apps/ai_assistant/apps.py`、`apps/serial_log/apps.py`）；`migrate`/`shell`/`pytest` 不触发。
- `run.py stop backend` 会先清理 MySQL `Sleep>5` 的孤儿连接（强制杀 Daphne 的副作用）。

### 2.2 中间件链（`config/settings.py`）

```
Cors → Security → GZip → Session → Common → JWTAuthenticationMiddleware
     → CsrfViewMiddleware → Authentication → Message → XFrameOptions
```

- `JWTAuthenticationMiddleware`（`gateway/middleware.py`）：对 `/api/*` 做前置 JWT 校验，注入 `request.user_id`；公开前缀仅 `/api/auth/{login,register,refresh}`、`/admin/`、`/static/`、`/media/`、`/api/schema/`、`/api/swagger/`。
- JWT 有效时置 `request._dont_enforce_csrf_checks = True`（浏览器无法跨站携带自定义 `Authorization` 头），后台 session 面仍受 CSRF 保护。
- `APPEND_SLASH = False`：缺尾斜杠得到确定的 404，避免 301 丢 `Authorization` 头。
- DRF：认证类 `shared.auth.drf_auth.JWTAuthentication`；权限 `IsAuthenticated`；渲染器 `shared.renderers.EnvelopeJSONRenderer`；schema `drf_spectacular`；`UNAUTHENTICATED_USER=None`。

### 2.3 Channels

`config/asgi.py` 保留 WebSocket 协议入口，`gateway/routing.py` 的 `websocket_urlpatterns` 为**空表**；`CHANNEL_LAYERS` 优先 Redis、异常降级 InMemory。当前无任何 WS 生产点，属"预留而非在用"。

---

## 3. 分层与依赖规则

```
前端（Vue 模块）
   │ 唯一 HTTP 出口 shared/api-client.ts
   ▼
接口层：gateway 中间件 → config/urls.py → apps/*/urls.py → View/ViewSet → Serializer
   ▼
应用层：apps/*/api.py（唯一写库口）→ ORM
   ▼
引擎层：engines/agents（SOP、工具、事件）· engines/device（adb）· engines/uart_log · engines/vision
   ▼
外部：Android 设备、串口日志 TCP、模型 API（DeepSeek / 百炼）、Redis、MySQL
```

| # | 规则 | 强制手段 |
|---|------|---------|
| 1 | View 只分发；写库必须经本 App `api.py` | `utils/gen_arch_stats.py --check-boundaries`（防火墙 #2） |
| 2 | 跨 App **禁止** import 内部实现（读 Model 允许） | 同上（防火墙 #1）+ code review |
| 3 | 跨 App 写只能调对方 `api.py` | 同上；AI 工具只调 `api.py` |
| 4 | 上层不得 import `airtest` / `uiautomator2`，设备操作只经引擎 | `boundary-check` + `engines/device/action.py` 抽象 |
| 5 | 前端只有一个 axios 实例 / HTTP 出口 | `frontend/.dependency-cruiser.cjs` 规则 `no-axios-except-client` |
| 6 | `/api/` 尾斜杠、`{status,data}` 信封、snake_case | `pytest` 契约对拍 + `shared/renderers.py` |

**唯一信封特例**：`apps/report_generator` 的 `/api/reports/*` 为 legacy 平铺 JSON（含 `FileResponse` 下载），按既有决策保留、不新增同类。

---

## 4. 后端：模块、端点与数据

### 4.1 模块总览

| App | API 前缀 | 端点（估算） | 表 | 职责 |
|-----|----------|:---:|----|------|
| `accounts` | `/api/auth/` | 5 | 复用 `auth_user` | JWT 双令牌 + Redis 吊销（`jti` 黑名单、`sid` 整组作废） |
| `dashboard` | `/api/` | 4 | 无（聚合） | KPI、执行趋势、任务结果、模型用量与费用、活动时间线 |
| `device_pool` | `/api/devices/` | 10 | `dp_`×2 | 扫描/连接/断开/激活/心跳 + 占用锁审计 |
| `case_manager` | `/api/cases/` | 11 | `cm_`×5 | 项目→目录→文件→用例→步骤 五层树；移动/批量删/导入导出 |
| `task_list` | `/api/tasks/` | 9 | `task_`×5 | 任务提交/重跑/取消/清空、事件入库、用量与费用、任务流程报告 |
| `ai_assistant` | `/api/ai/` | 7 | `ai_`×1 | 智能体配置、模型线路、一次性揭示密钥 |
| `report_generator` | `/api/reports/` | 5 | `rg_`×2 | 报告列表/用例分解/文件下载（legacy 平铺信封） |
| `serial_log` | `/api/serial-log/` | 4 | `sl_`×1 | 端口监听开关、当前日志只读、关键词对照表 |
| `workflow` | `/api/workflow/` | 10 | `wf_`×3 | 页面流原型、目录、JSON 文档、导入导出 |

> 端点口径：**唯一业务路径**（同一路径多方法计 1），不含 Router 根、`schema`/`swagger` 与 DRF format 变体。当前 **65 条**；OpenAPI 基线 `openspec/openapi.yaml` 收录 **66 条**（含 `/api/schema/` 自述）、**86 个 operations**，由 `openapi-schema` 门禁校验。

### 4.2 数据模型（19 张表 / 7 组前缀）

| 分组 | 表 | 关键设计 |
|------|----|---------|
| `dp_` | `dp_devices`、`dp_device_locks` | 设备仅 `ONLINE/BUSY` 两态，离线即删行；锁只追加不删，`UNIQUE(device) WHERE status='active'` 保证同设备单活跃锁 |
| `cm_` | `cm_case_projects`、`cm_case_directories`、`cm_case_files`、`cm_test_definitions`、`cm_case_steps` | 项目/目录/文件三层有唯一约束（同项目、同父目录下名称唯一）；用例与步骤按 `sort_order` 排序，步骤顺序由服务端按提交顺序重排 |
| `ai_` | `ai_agents` | 智能体配置与模型线路；`route_configs` 内密钥 Fernet 加密 |
| `task_` | `task_tasks`、`task_attachments`、`task_events`、`task_media`、`task_usage_hourly` | 事件表 `UNIQUE(task,seq)` + 三索引；图片只存 720 缩略图（`UNIQUE(task,sha256)`）；小时用量表 `UNIQUE(date,hour,model,role,agent)` |
| `rg_` | `rg_reports`、`rg_report_templates` | 报告文件落盘 + 元信息入库 |
| `wf_` | `wf_prototypes`、`wf_directories`、`wf_documents` | 文档以 JSON 存画布，目录树与用例管理同构 |
| `sl_` | `sl_log_ports` | 只存"开关"，端口/SKU/波特率以 `DEVICE_LOG_*` 配置为真相源 |

**模型配置与密钥**：`ai_agents.route_configs["device_control"].{executor,verifier}` 存模型名/provider/base_url 与 Fernet 加密的 `api_key`；读取时脱敏，`reveal-key` 一次性揭示（`key_revealed` 标记）。

### 4.3 鉴权与身份

- 令牌：access TTL 1h、refresh TTL 7d（`JWT_ACCESS_TTL`/`JWT_REFRESH_TTL`），一次登录共享 `sid`。
- 吊销：`jwt:blacklist:{jti}` 与 `jwt:session_revoked:{sid}`；**读侧 fail-open**（Redis 不可用放行并记 error），**写侧 fail-closed**（抛 `BlacklistUnavailableError`）。
- 权限：AI 智能体写操作仅超管；读操作按 owner 或"超管拥有的共享智能体"过滤；`shared/users.py::is_superuser` 是跨 App 唯一实现。

---

## 7. 前端架构

| 模块 | 路由 | 后端前缀 |
|------|------|---------|
| dashboard | `/dashboard` | `/api/dashboard/*` |
| device-pool | `/devices` | `/api/devices/*` |
| workflow | `/workflow`、`/workflow/prototypes/:id` | `/api/workflow/*` |
| serial-log | `/serial-log` | `/api/serial-log/*` |
| ai-assistant | `/ai-assistant`、`/ai-assistant/agents`、`/agent/:id` | `/api/ai/*` |
| task-list | `/tasks`、`/tasks/:id` | `/api/tasks/*` |
| case-manager | `/cases`、`/cases/projects/:id`、`/files/:fileId`、`/cases/:id/edit` 等 | `/api/cases/*` |
| report-generator | `/reports`、`/reports/cases/:type`、`/reports/:runId` | `/api/reports/*` |

- 侧栏三组：主区（仪表盘 / AI 助手）、数据（设备 / 页面流 / 串口日志）、AI 任务（任务清单 / 用例 / 报告）。
- 请求：模块 `api.ts` → `shared/api-client.ts`（baseURL `/api`，2min 超时）；拦截器注 token、401 触发单飞刷新、公开端点不刷新（`shared/api-auth-interceptors.ts`）。
- 状态：Pinia 仅 `workflow`（`workflowStore`、`libraryStore`）；token 直存 localStorage，无 auth store。
- 设计系统：`shared/styles/tokens.css` 是令牌唯一真相源；L0 视口 → L1 侧栏/主区 → L2 页头/页面根 → L3 容器 → L4 数据面 → L5 覆盖层；模块只拥有自己页面的 L2–L5。
- 实时性：无 WebSocket / SSE；任务进度靠页面轮询任务详情接口。

---

## 8. 关键数据流

### 8.1 设备接入与占用

```
/scan → DeviceDetector(adb devices) → dp_devices 落库
/lock → dp_device_locks(active)  ── 唯一约束挡并发
/heartbeat → 巡逻 → 超时则 released(timeout)
/disconnect → 删设备行 + 锁转 disconnect
```

### 8.2 用例 → 任务装配

```
cm_case_projects → directories → files → test_definitions → case_steps
      │ 选中用例/文件
      ▼
POST /api/tasks/submit/（含 device_serial / case_title / 附件）
      ▼
api.create_task → materialize_config_file（物化 YAML）→ dispatch_device(serial)
```

### 8.3 任务执行与回看

```
daemon thread: task_runner.run_task_async
  → engine_adapter.sop_role_models（解密密钥）
  → run_platform_sop → SOPEngine（executor ↔ verifier）
  → 事件批量入库 task_events / media / usage
  → finalize_task（状态 + 费用汇总）
                        │
                        ▼
      GET /api/tasks/{id}/            → 任务详情时间线
      GET /api/tasks/{id}/report/     → 任务流程报告（legacy 平铺）
      GET /api/dashboard/*            → 趋势与用量聚合
```

### 8.4 证据闭环

```
executor 动作 → 设备打日志 → TCP 采集落文件 → KeywordIndex 命中
      → verifier 判决（passed/message）→ 事件入库 → 失败原因回灌 executor
```

---

## 9. 可观测与运维

| 面 | 实现 |
|----|------|
| 后端日志 | `logs/backend.log`（业务 `backend_log` + daphne stdout 捕获） |
| 智能体日志 | `logs/agents/agent_events.log`（事件时间线与运行汇总同一份） |
| 设备日志 | `logs/device.log`（引擎动作与错误） |
| 串口日志 | `logs/serial.log`（采集通道本身）+ `logs/serial_logs/{SKU}_{port}.log`（原文） |
| 轮转 | 统一 10MB×3；串口原文单文件 50MB 后改名归档 |
| 健康检查 | `python run.py status`（Redis 探端口，前后端探 HTTP） |
| 自愈 | 启动时把上次进程遗留的 `running` 任务置 `failed`；按开关恢复串口监听 |

> 框架日志只走控制台（`config/settings.py` 的 `LOGGING` 仅 console handler），不写 `django.log`。

---

## 10. 质量治理

---

## 12. 已知限制与技术债

1. **无实时推送**：任务进度靠轮询，长任务的前端体验与请求量都受此限制。
2. **设备无连接复用**：每次工具调用新建 adb 连接，高并发下的开销与稳定性尚未量化。
3. **`report_generator` 的 legacy 平铺信封**：全平台唯一特例，且数据来自 `task_tasks` 聚合而非独立执行链。
4. **前端信封拆包不统一**：有的模块返回 `DjangoResponse` 类型，有的直接返回 `AxiosResponse`，`status:false` 走 HTTP 200。
5. **pytest marker 残留**：`pytest.ini` 仍声明 `device_inspector` / `element_locator`，缺 `dashboard` / `serial_log`。
6. **CI 只保证"测试可导入"**：`pytest --collect-only` 门禁不跑用例，后端运行期回归仍无 CI 守护。
7. **文档真值**：能力规格（92 份）是可信契约；独立接口文档已下线，接口以 `openspec/specs/` 与 `openspec/openapi.yaml` 为准，README / 本文与代码同步靠约定而非工具强制。
8. **单 SKU 日志形态**：默认 `H6810 / 7005` 单端口；多设备需在 `DEVICE_LOG_SOURCES` 显式登记。

---