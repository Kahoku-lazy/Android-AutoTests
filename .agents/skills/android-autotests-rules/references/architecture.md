# 架构总纲

> 架构层面的硬约束。AI 编码时必须遵守，代码能读到的信息不在此重复。
> 编码规范见 `python-code.md` `frontend.md` `api-conventions.md`。

---

## 一、通信通道（封闭集合）

平台组件间通信收敛为 4 条内部通道，禁止引入新协议，防止旁路绕过鉴权与能力泄露。新增跨组件通信只能复用已有通道。

### 通道总表

| # | 通道 | 协议 | 鉴权 |
|:--:|------|------|------|
| ① | 前端 ↔ Django | HTTP REST | JWT（Bearer） |
| ② | Django → 前端 | WebSocket | JWT（query token） |
| ③ | AgentScope → Django | 进程内直接调用 | 同进程，无需鉴权 |
| ④ | Django ↔ 设备 | UiEngine 协议（引擎中转） | — |

```
❌ 禁止引入：gRPC · MQTT · Kafka · RabbitMQ · GraphQL · WebRTC
```

> SSE 通道（前端→AI 流式对话）已随「主对话移除」（ARCH-08 v3.4）删除，**禁止恢复**。
>
> **不属于内部组件通信通道**（基础设施依赖 / 外部出站调用）：
> - Redis：JWT 黑名单、Django Channels 层、AgentScope 存储。
> - 外部 LLM API：Django → DeepSeek / DashScope / OpenAI 等（HTTPS 出站）。

### 逐通道规则

> 每条只写「链路（必经路径）· 能做 / 不能做 · 校验」三要素；实现细节从代码读，不在此重复。

#### ① 前端 ↔ Django — HTTP REST + JWT

- **链路**：组件 → 模块 `api.ts` → `shared/api-client.ts`（唯一 HTTP 出口）→ `/api/...` DRF。
- **能做**：一切业务 JSON 数据交互（读 / 写 / 上传）；文件下载走 FileResponse（URL 下载，非 JSON）。
- **不能做**：绕过唯一出口（裸 `fetch`/`axios`/`XMLHttpRequest`、直连后端端口）；后端返回 Django Template；业务端点不验 JWT 放行。
- **校验**：
  1. 前端出口（自动）：`cd frontend && npm run lint && npm run depcruise`
     - `npm run lint`（ESLint）：`no-restricted-imports`（禁 `import axios/ky/got/superagent`）、`no-restricted-globals`（禁 `fetch`/`XMLHttpRequest`）、`no-restricted-syntax`（禁 `sendBeacon`）。
     - `npm run depcruise`（dependency-cruiser）：只有 `shared/api-client.ts` + `api-auth-interceptors.ts` 能依赖 axios。
  2. 后端 JWT 覆盖（核对真相源）：业务路由须挂 `/api/`（各 App `urls.py`）；非白名单 `/api/` 必须验 JWT（`gateway/middleware.py` 的 `PUBLIC_PREFIXES`）。

#### ② Django → 前端 — WebSocket + JWT

- **链路**：Consumer（在 `gateway/routing.py` 注册）→ 前端 `ws-url.ts` + `useTaskWebSocket` / `useCaseEditingSocket`。
- **能做**：推送执行进度、编辑锁通知。
- **不能做**：新增第 3 个 WS 生产点；恢复 WS 截图流（已快照化 REST）；Consumer 不在 `routing.py` 注册。
- **校验**：`gateway/routing.py` 恒 2 个路由；事件 type 与前端一致。

#### ③ AgentScope → Django — 进程内直接调用

- **链路**：`agent_scope` 工具（`TOOLS` 注册表）→ 各 App `api.py` → ORM。
- **能做**：调各 App `api.py` 白名单函数。
- **不能做**：直连数据库、直连设备；在 `agent_scope/` 下新增 `adapters/` 或 `rag/`。
- **校验**：grep `agent_scope/` 无 `adapters`/`rag`；工具清单 `gen_arch_stats.py`。

#### ④ Django ↔ 设备 — 引擎中转（UiEngine 协议）

- **链路**：上层业务 → `device_pool`（api.py / DeviceSession）→ `engines/`（`UiEngine` 协议实现）→ 设备。**引擎内部经 ADB / Airtest / u2 控制设备，Django 不关心、不直触**。
- **能做**：截图、层级 dump、坐标操作、App 生命周期、设备信息、shell。
- **不能做**：上层直触引擎裸句柄（`.airtest`/`.u2`）、import 引擎库 / 具体实现、直接 ADB 控制设备——**只许调 `UiEngine` 协议**。
- **校验**：`gen_arch_stats.py --check-boundaries`（engine_leak 三类）。

---

## 二、依赖方向

```
✅ 上层 import 下层（ai_assistant → device_pool）
✅ 同层 import api.py 或 Model（test_runner → case_manager.api）
❌ 下层 import 上层（device_pool → ai_assistant）
❌ 同层 import 内部实现（test_runner → case_manager.views）
```

`device_pool` 是唯一底层：禁止 import 任何其他 App。
`dashboard` 和 `ai_assistant` 是聚合层：允许 import 任意下层。
其余 App 是中层：只能 import 底层 + 同层 api.py。

---

## 三、AgentScope 边界

AgentScope 已从独立服务迁移为 Django 进程内模块（`apps/ai_assistant/agent_scope/`），不再有独立 `agentscope_service/` 目录。

```
❌ 禁止 AgentScope 直连数据库
❌ 禁止 AgentScope 直连设备
✅ 所有平台数据通过 Django ORM / api.py 获取（同进程直接调用）
```

---

## 四、dashboard 约束

`dashboard` 是纯聚合层，无自有数据表：

```
❌ 禁止 ORM 写操作（INSERT/UPDATE/DELETE）
✅ 只允许跨模块只读 ORM 查询
```

---

## 五、模块增减

### 新增 App 前检查

必须同时满足：

```
[ ] 有独立的数据主权（新表前缀不在现有 8 组前缀中）
[ ] 有独立的业务逻辑（不是现有模块的 CRUD 子集）
[ ] 不是纯聚合（聚合放 dashboard/views.py）
[ ] 不是纯配置（配置放现有 App 的 models.py）
```

新增必须同步改 4 个文件：

```
config/settings.py    → INSTALLED_APPS
config/urls.py        → include('apps.{name}.urls')
frontend/src/router.js → 新路由
frontend/.../AppSidebar.vue → 新菜单项
```

### 删除模块

必须同步清理：

```
apps/{name}/ + frontend/src/modules/{name}/（整个目录）
config/settings.py → 移除 INSTALLED_APPS
config/urls.py → 移除 include
前端 router.js + AppSidebar.vue → 移除条目
跨模块 import → 移除对已删模块的引用
```

---

## 六、红线

```
1.  前端直连数据库
2.  后端返回 Django Template
3.  跨模块 import 内部实现（views/service/runner/executor/state_machine）
4.  跨模块直接 ORM 写（必须走目标 api.py）
5.  device_pool import 上层模块
6.  dashboard 做 ORM 写
7.  引入四条内部通道之外的协议
8.  新增 App 不检查 §五 门槛
9.  AgentScope 直连数据库或设备
10. apps/ai_assistant/agent_scope/ 下新增 adapters/ 或 rag/
11. 上层（apps/ · gateway/）直接 import 引擎库或访问引擎裸句柄（见 §七）
```

---

## 七、引擎边界（L1c engines/）

`engines/` 是**唯一**允许触碰第三方设备引擎库（Airtest / uiautomator2）的层。
上层只经 `UiEngine` 协议（`engines/base.py`）消费设备能力，经 `engines/registry.py` 工厂获取引擎实例。
**引擎能力不得泄露上层**——裸句柄、具体实现类、第三方库都不允许在 L2/L3 层出现。

```
✅ 上层：import engines.base（协议）/ engines.registry（工厂），只调协议方法
❌ 上层（apps/ · gateway/）禁止：
   1. import airtest / uiautomator2（第三方引擎库直接 import）
   2. import engines.android.*（具体引擎实现，应走 registry 工厂）
   3. 访问/持有引擎裸句柄（engine.airtest / engine.u2 / pool.ad / pool.u2d / DeviceConnection.airtest/.u2）
```

**校验**：`python tools/gen_arch_stats.py --check-boundaries`（扫描 `engine_lib` / `engine_impl` / `raw_handle` 三类泄漏，现有违规登记于 `tools/boundary-whitelist.json`，新增违规拦截；`--verbose` 打印全部已知技术债明细）。
