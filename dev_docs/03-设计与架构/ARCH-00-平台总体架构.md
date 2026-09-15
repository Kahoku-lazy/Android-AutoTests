# ARCH-00 — 平台总体架构

> **版本**：v3.3 · **日期**：2026-09-14 · **状态**：现行（取代 v2.1 三层口径；v3.2：设计-* 系列与迁移 Checklist 归档；v3.3：设备域与 test_runner 两域同步 HEAD——L2 会话层已扁平化、引擎坐标与默认值修正、执行引擎下线）
>
> ⚠️ 本文对应 **HEAD 代码**（七步重构与 AI 助手 DRF 迁移均已提交）；设备域与 test_runner 两域已于 v3.3 对齐，遗留差异见 §1.6 偏差登记。

## 文档内容简述

本文档是 Android-AutoTests 平台的**架构总纲**，覆盖平台全貌而非单一模块：

- **分层架构**：L0 第三方 → L1 领域基础设施（算法/模型/引擎）→ L3 业务 App → L4 前端的职责与依赖方向；原 L2「设备交互中台」已于 2026-09-03 扁平化，层号空置（§一、§二）
- **通信通道**：五条通道的协议、鉴权与边界（§1.4）
- **模块架构**：11 个后端 App + 8 个前端模块的依赖关系与防火墙规则（§三）
- **关键机制**：写收敛 / 引擎注册表 / 设备业务锁租用 / AI Tool 编排（§四；执行状态机已随 test_runner 下线）
- **落地信息**：代码目录地图、设计决策、部署形态（§五、§六、§七）
- **统一定义与权威统计**：步骤类型、设备/任务状态、表 / 端点 / Tool 实测清单（§八、附录A）

## 文档职责边界（ARCH vs PRD）

- **ARCH（架构）只描述**：分层、依赖方向、数据流、API 端点概览、边界/防火墙、数据模型。
- **组件用抽象角色命名**（如「统计卡片」「截图展示」「步骤编排器」），不写 `.vue` 文件名、不写数量。
- **具体组件清单 / 规格 / 验收 → 只进 PRD**。功能变更只改 PRD，架构变更才改 ARCH。

## 你能从文档获取什么信息

- **全局架构认知**：各层如何分层（L2 空置）、11 个后端 App 与 8 个前端模块如何协作、五条通道的数据如何流动
- **模块边界与依赖规则**：谁能 import 谁、写操作如何收敛到 api.py、哪些是防火墙红线——指导安全地新增或修改模块
- **权威统计基准**：11 个 App（活跃 10 + test_runner 仅卸表迁移）、**33 张表（8 组前缀）**、**116 条路径端点**（+ DRF 生成路由另计）、**12 个 Tool（3 类）**、37 种步骤枚举（注册表 29）、0 个 WS 生产点——作为「文档是否落后代码」的核对依据。口径定义与逐 App 数字见附录 A
- **技术落地方式**：部署形态（Daphne + in-process AgentScope + Redis）与关键设计决策的取舍理由

## 关联文档

- **需求规格**：[`需求大纲`](../02-PRD需求/需求大纲.md)（项目定位 · 用户故事 · 模块职责）
- **子模块架构**：[`ARCH-01-仪表盘`](ARCH-01-仪表盘.md) ～ [`ARCH-09-工作流工作台`](ARCH-09-工作流工作台.md)
- **目标架构详档**：设计-* 系列（五层目标总纲 · L0~L3 逐层详档 · 引擎可替换方案 · 重构落地实测）与迁移 Checklist **已于 2026-08-21 归档** → [`../_archive/`](../_archive/)（内容已吸收进本文与 `openspec/specs/`；剩余待办见 §1.6 #11/#12）
- **正式契约（OpenSpec）**：`openspec/specs/engine-protocol/spec.md`（现行）· `openspec/specs/device-session/spec.md`（对应协议已于 2026-09-03 扁平化，spec 已于 2026-09-15 退役）
- **迁移纪律**：原 [`迁移实施注意事项-Checklist`](../_archive/迁移实施注意事项-Checklist.md) 已闭环归档（2026-08-21）；剩余 2 项待办见 §1.6 #11/#12

---

## 一、平台架构概览

### 1.1 架构定位（分层）

平台按计算职责分层，依赖方向**严格单向向下**：`L4 → 网关 → L3 → L1 → L0`（原 L2 设备交互中台已扁平化，见下）。

> 演进脉络：v2.1 的三层口径（前端 / 后端 / AI 引擎）经 2026-08-20 七步重构（OpenSpec 变更集）演化为分层架构——设备交互协议与引擎实现下沉 `engines/`、纯算法下沉 `algorithms/`、枚举与领域模型收敛 `models/`。其中「设备交互中台」一层在 2026-09-03 归档变更 `flatten-device-session` 中被**扁平化删除**（去掉 `session.py` 中间层，上层直调引擎工厂，设备互斥交由 `DeviceLock` 业务锁），故 L2 层号空置。

| 层 | 名称 | 一句话职责 |
|----|------|-----------|
| **L4** | 前端 | 渲染、交互、实时流消费（8 业务模块 + shared 共享层） |
| **L3** | 业务 App 编排层 | 请求解析、业务编排、信封封装（11 个 Django App + gateway/shared；其中 test_runner 已下线，仅保留卸表迁移） |
| ~~**L2**~~ | ~~设备交互中台~~（已空置） | 原 `DeviceSession` 会话租用层已于 2026-09-03 扁平化删除：上层直调引擎工厂（`open_engine` / `close_engine`），设备互斥由 `DeviceLock` 业务锁承担 |
| **L1c** | 引擎层 | 操作原语物理实现、连接生命周期、能力声明（UiEngine 协议 + 注册表） |
| **L1b** | 领域模型 | 枚举与领域类型的**唯一真相源** |
| **L1a** | 算法层 | 无状态纯函数（XPath 候选、层级解析、OCR） |
| **L0** | 第三方与外部目标 | u2 / Airtest / cnocr / Playwright / requests + Android 设备 / 浏览器 / 被测 API |

### 1.2 架构全景图

> 与已归档的目标总纲（`../_archive/设计-目标架构-设备交互协议与引擎分层.md`）§一 **总览图同构**；补充「数据与存储」节点与 algorithms 纯库依赖。端口/表数以附录A为准。

```mermaid
flowchart TB
    subgraph L4["L4 · 前端（Vue 3 :5173 · 8 模块 + shared 共享层）"]
        F1["dashboard · device-pool · device-inspector"]
        F2["element-locator · case-manager"]
        F3["report-generator · ai-assistant · workflow"]
    end

    subgraph GW["网关"]
        JWT["gateway/middleware.py<br/>JWT 中间件"]
        WS["gateway/routing.py<br/>WS 路由（0 生产点）"]
    end

    subgraph L3["L3 · 业务 App（编排层 · 写收敛 api.py · 零引擎/零算法内联）"]
        DI["device_inspector<br/>快照业务 · di_"]
        AI["ai_assistant<br/>Tool 编排 · AgentScope 进程内 · ai_"]
        EL["element_locator · case_manager<br/>el_ · cm_"]
        DP["device_pool<br/>设备状态 / 业务锁 · dp_ 2 表"]
        OTH["dashboard · workflow · report<br/>evaluator · accounts"]
    end

    subgraph L1["L1 · 领域基础设施（顶级包 · 零 App 依赖）"]
        ENG["engines/device/<br/>UiEngine 协议 + registry（fail-fast）<br/>u2 ·（未来插槽）"]
        ALGO["algorithms/<br/>xpath · hierarchy · vision/ocr"]
        MODELS["models/<br/>step_types · test_models · 枚举真相源"]
    end

    subgraph L0["L0 · 第三方与外部目标"]
        LIBS["uiautomator2 · Airtest · cnocr<br/>Playwright · requests"]
        EXT["📱 Android 设备 · 🌐 浏览器 · 🔗 被测 API"]
    end

    subgraph STORE["数据与存储"]
        DB[("🗄 数据库<br/>MySQL 默认 / SQLite 可切（DB_ENGINE）<br/>33 张业务表 · 8 组前缀")]
        REDIS[("Redis :6379<br/>JWT 黑名单 + Channels")]
        CHROMA[("ChromaDB<br/>data/chromadb 知识库")]
    end

    L4 -->|"HTTP / WS / SSE（JWT）"| GW
    GW --> L3
    L3 -->|"api.py 白名单 / 引擎工厂 open_engine"| ENG
    L3 -.->|"纯函数调用"| ALGO
    ENG -->|"设备库唯一接触点"| LIBS
    ALGO -.->|"纯库（cnocr / PIL）"| LIBS
    LIBS --> EXT
    L3 -->|"Django ORM"| DB
    L3 -->|"Channels"| REDIS
    AI --> CHROMA

    style L4 fill:#e3f2fd,stroke:#2196f3
    style GW fill:#fff3e0,stroke:#ff9800
    style L3 fill:#e8f5e9,stroke:#4caf50
    style ENG fill:#fdf3d7,stroke:#f5c31c
    style ALGO fill:#f7e8d8,stroke:#e5cba8
    style MODELS fill:#f7e8d8,stroke:#e5cba8
    style L0 fill:#f5f5f5,stroke:#999
    style STORE fill:#f5f5f5,stroke:#999
```

### 1.3 分层包图与防火墙

> 箭头 = import 方向。实线 = 合法依赖；虚线 = 特殊边（前端零后端 import、纯库依赖）。

```mermaid
flowchart TD
    subgraph L4["L4 前端 frontend/src/"]
        FE["8 业务模块 + shared（api-client · WS · SSE · composables）"]
    end

    subgraph L3["L3 业务 App apps/（11 个；test_runner 仅卸表迁移）"]
        DP["device_pool<br/>设备状态 / 业务锁 · dp_ 2 表"]
        AI3["ai_assistant<br/>12 Tool 聚合调用"]
        OTH["其余 8 App"]
    end

    subgraph L1["L1 领域基础设施"]
        ENG["engines/device/<br/>UiEngine 协议 + 实现"]
        ALGO["algorithms/<br/>纯函数"]
        MOD["models/<br/>枚举 + 领域类型"]
    end

    subgraph L0["L0 第三方"]
        EXT["u2 · Airtest · cnocr · Playwright · requests"]
    end

    FE -.->|"仅 HTTP / WS / SSE（零后端 import）"| L3
    OTH -->|"api.py / models（只读）"| DP
    AI3 -->|"Tool → 各 App api.py"| OTH
    DP -->|"引擎工厂：open_engine / close_engine"| ENG
    ENG --> ALGO
    ENG --> MOD
    ALGO --> MOD
    ALGO --> EXT
    ENG --> EXT

    style L4 fill:#e3f2fd,stroke:#2196f3
    style L3 fill:#e8f5e9,stroke:#4caf50
    style ENG fill:#fce4ec,stroke:#e91e63
    style ALGO fill:#fce4ec,stroke:#e91e63
    style MOD fill:#e8eaf6,stroke:#3f51b5
    style L0 fill:#f5f5f5,stroke:#999
```

**防火墙规则**：

```
L4 前端      ──❌ import──→ 后端任何模块（只经 HTTP / WS / SSE）
L4 前端      ──❌ 数据库直连 · 文件系统 I/O · AI 推理 · ADB 通信

L3 视图层    ──✅ import──→ 本 App api.py / models
L3 视图层    ──❌ import──→ 其他 App 内部实现（service / runner / consumer / state_machine / views_helpers）
L3 api 层    ──✅ import──→ 本 App models + 其他 App api.py / models（只读）
L3 api 层    ──❌ import──→ 其他 App views / 内部实现
L3 业务 App  ──✅ import──→ engines.device.registry（引擎工厂 open_engine/close_engine）· device_pool.api（业务锁/占用）· algorithms 纯函数 · models 枚举
L3 业务 App  ──❌ import──→ engines.device.android.*（引擎实现）与裸句柄（.u2 / .airtest）

L1c engines  ──✅ import──→ 第三方库 + models.* + algorithms.*（纯函数，D-1 裁决）
L1c engines  ──❌ import──→ apps.* / django.*
L1a 算法     ──✅ import──→ 第三方纯库 + models.*（类型，D-2 裁决）
L1a 算法     ──❌ import──→ apps.* / engines.* / django.*

数据层       ──✅ 被各层只读查询
数据层       ──❌ 写操作必须走 api.py（写收敛；跨 App 写走目标 App api.py）

dashboard    ──✅ 跨 App 只读 ORM 聚合
dashboard    ──❌ 任何写操作（无自有表）
```

### 1.4 五条通信通道

```mermaid
flowchart LR
    subgraph Frontend["L4 前端 :5173"]
        Vue["Vue 3 SPA"]
    end

    subgraph Django["L3 后端 Django :8766"]
        API["REST API（DRF + 裸 view 并存）"]
        WS["WebSocket（0 生产点）"]
        AS["AgentScope in-process"]
    end

    subgraph Data["数据与设备"]
        DB["MySQL / SQLite"]
        Dev["Android"]
    end

    Frontend -->|"① HTTP REST + JWT<br/>所有 /api/* 请求"| API
    Frontend -->|"② WebSocket + JWT<br/>（当前 0 生产点）"| WS
    Frontend -->|"③ SSE + JWT<br/>AI 流式对话"| AS
    AS -->|"④ Python import<br/>同进程调 api.py/ORM"| API
    Django -->|"⑤ ADB（经 engines/）<br/>Airtest + u2 设备控制"| Dev
    API --> DB
    AS --> DB

    style Frontend fill:#e3f2fd,stroke:#2196f3
    style Django fill:#e8f5e9,stroke:#4caf50
    style Data fill:#fff3e0,stroke:#ff9800
```

| # | 通道 | 方向 | 协议 | 鉴权方式 | 用途 |
|:--:|------|------|------|------|------|
| ① | 前端 → Django | 双向 | HTTP REST | JWT Bearer Header | 业务 CRUD（11 App） |
| ② | Django → 前端 | 单向推送 | WebSocket | JWT query string | 当前 0 生产点（`gateway/routing.py` 为空表：截图流快照化、执行进度随 test_runner 下线、编辑锁随文档用例重构下线） |
| ③ | 前端 → AI | 单向流 | SSE | JWT（共享 SECRET_KEY） | AI 流式对话（单请求 + asyncio.Queue） |
| ④ | AgentScope → Django | 单向调用 | Python import | 上下文注入 | Tool 执行业务逻辑（零网络开销） |
| ⑤ | Django → 设备 | 双向 | ADB | — | 截屏 / dump / 手势（仅经 engines 层） |

> v1.7 起设备检查器**无实时截图流**：截图/层级改为快照式抓取（REST → `di_snapshots`），原 ScreenshotConsumer 已删除；此后执行进度 WS 随 test_runner 下线、编辑锁随文档用例重构下线，`gateway/routing.py` 的 `websocket_urlpatterns` 现为**空表**（0 生产点）。

**平台主链路（数据流）**：

```mermaid
flowchart TB
    subgraph UserEntry["用户入口"]
        Login["登录（accounts）"]
        Dash["仪表盘"]
    end

    subgraph ManualChain["通道 A：手动操作链路"]
        direction LR
        DP_A["① 设备管理<br/>连接设备"]
        DI_A["② 设备检查器<br/>快照 Dump/截图"]
        EL_A["③ 元素定位<br/>保存 XPath"]
        CM_A["④ 用例管理<br/>编排步骤"]
        TR_A["⑤ 执行引擎<br/>运行测试"]
        RG_A["⑥ 测试报告<br/>查看结果"]
        DP_A --> DI_A --> EL_A --> CM_A --> TR_A --> RG_A
    end

    subgraph AIChain["通道 B：AI 智能操作链路"]
        direction LR
        AI_Chat["AI 对话<br/>自然语言输入"]
        AI_ReAct["ReAct 推理<br/>Tool 编排（26 个）"]
        AI_Result["结果返回<br/>SSE 流式输出"]
        AI_Chat --> AI_ReAct --> AI_Result
    end

    subgraph WFChain["通道 C：可视化编排链路"]
        direction LR
        WF_Res["资源库<br/>目录/文档（page_flow）"]
        WF_VueFlow["VueFlow 画布<br/>页面流节点图"]
        WF_Save["JSON 落库<br/>wf_ 两表"]
        WF_Res --> WF_VueFlow --> WF_Save
    end

    Login --> Dash
    Dash --> ManualChain
    Dash --> AIChain
    Dash --> WFChain

    AI_ReAct -.->|"Tool 调用"| DP_A
    AI_ReAct -.->|"Tool 调用"| DI_A
    AI_ReAct -.->|"Tool 调用"| EL_A
    AI_ReAct -.->|"Tool 调用"| CM_A
    AI_ReAct -.->|"Tool 调用"| TR_A
    AI_ReAct -.->|"Tool 调用"| RG_A

    style UserEntry fill:#889df0,color:#fff
    style ManualChain fill:#e8f5e9,color:#2e7d32
    style AIChain fill:#fce4ec,color:#c62828
    style WFChain fill:#fff3e0,color:#e65100
```

### 1.5 API 实现与统一管理（DRF + api.py）

后端 HTTP 层由 **DRF 与裸 Django View 两种范式并存**，通过四个统一机制收敛为一致的 API 风格：

| 统一机制 | 实现 | 作用 |
|---|---|---|
| 统一信封 | `EnvelopeJSONRenderer`（DRF）/ 手写 `JsonResponse`（裸 view） | 响应统一 `{status, data}` / `{status, message}` |
| 统一鉴权 | `JWTAuthenticationMiddleware`（裸 view）+ DRF `JWTAuthentication` | 都委托 `jwt_auth.verify_token()`，注入 `request.user_id` |
| 写操作收敛 | 各 App `api.py`（`__all__` 白名单） | 所有 INSERT/UPDATE/DELETE 走 api.py，视图层/serializer 禁直写 ORM |
| 统一路由 | 各 App `urls.py` → `config/urls.py` include | 统一前缀 `/api/{app}/` |

```mermaid
flowchart TB
    subgraph GW["API 网关 · config/urls.py"]
        ROOT["/api/ 根 · dashboard"]
        APPS["/api/{app}/ × 10<br/>inspector · elements · devices · cases · workflow<br/>reports · auth · ai · evaluator"]
        DOC["/api/schema · /api/swagger · /api/docs"]
    end
    subgraph WSR["WebSocket · gateway/routing.py"]
        W0["websocket_urlpatterns = []（0 生产点，禁止新增）"]
    end
    ROOT --> DB1["dashboard 只读聚合"]
    APPS --> DB2["11 App 业务端点"]
```

**范式分布（2026-09-14 复核）**：

| 范式 | App |
|---|---|
| DRF ViewSet / Serializer | case_manager · element_locator · evaluator · workflow（`views_drf.py`/`views_api.py`） |
| DRF ViewSet 迁移中 | ai_assistant（Batch 1-3 已迁 DefaultRouter：agents/conversations/toolbox ViewSet + 知识库/上传 APIView；豁免 SSE 与工具网关） |
| DRF APIView / 函数视图 | accounts · dashboard（APIView）· device_pool（`@api_view` + service 写收敛） |
| 裸 Django View | device_inspector · report_generator |

**DRF 统一配置**（`settings.REST_FRAMEWORK`）：信封渲染 `EnvelopeJSONRenderer` · 鉴权 `JWTAuthentication` · 权限 `IsAuthenticated` · OpenAPI 文档 drf_spectacular。

**统一响应信封**（所有端点，含 DRF 与裸 view；**例外**：report_generator / workflow legacy 为平铺 `{status, ...}` 信封，⚠️ 登记见 §1.6 #9）：

```json
{ "status": true,  "data": { } }          // 2xx 成功
{ "status": false, "message": "..." }      // 4xx/5xx 失败（不暴露技术术语）
```

> 字段契约（snake_case）、逐端点字段与错误文案以各模块 PRD §5 为准。

### 1.6 同步方式与契约偏差登记

| 交互类型 | 数据同步方式 |
|------|------|
| 仪表盘 / 列表类 | 静态一次性加载 + 手动刷新（无轮询） |
| 执行进度 | 执行引擎已下线（原为 WebSocket 推送 10 种下行消息 + `seq` + 心跳，随 test_runner 一并移除） |
| 设备检查器 | 快照式：REST capture → `di_snapshots` → 回看（无实时流） |
| AI 对话 | SSE 逐 token（Redis/AgentScope 不可用降级阻塞 POST） |
| 任务状态 | 执行引擎已下线，平台无任务状态流转（原为后端权威 `state` 下发 + 前端 `running` 镜像） |

**契约偏差 / 违规登记（2026-09-14 复核：设备域与 test_runner 条目已标记消除状态）**：

| # | 项 | 现象 | 状态 |
|---|---|---|---|
| 1 | ~~`test_runner.state_machine.recover_orphans()`~~ | 曾跨 App 直写 `device_pool.Device`（status/occupied_by/occupied_at `.save()`） | ✅ 已消除（`1c4c47cf` 删除执行链与 `state_machine.py`；`tr_` 表由迁移 `0020_delete_test_runner_models` 卸载） |
| 2 | ~~`device_pool.views/service`、`executors/ui/connect·recovery`~~ | 曾直 import `engines` 实现（旧路径），并以 `DEVICE_SESSION_ENABLED` 切换会话化路径 | ✅ 已消除（归档变更 `flatten-device-session`，2026-09-03：删除 `session.py` 与开关，上层统一经 `engines.device.registry` 工厂 + `DeviceLock` 业务锁） |
| 3 | `U2Engine.connect()`（`engines/device/android/u2.py:137`） | 签名多 `on_log`、返回 `self`；暴露 `airtest/u2/device_info` 兼容属性 | ⚠️ 待 L1c 详档裁定 |
| 4 | `STEP_TYPE_META`(29) / `UI_LABELS`(28) | 两套标签并存；`screenshot` 键无对应枚举成员 | ⚠️ 待收敛 |
| 5 | ~~`tr_test_runs.status`~~ | 曾有大小写混存，`0019_backfill_lowercase_run_status` 回填未执行 | ✅ 已作废（表随 test_runner 下线由迁移 0020 卸载） |
| 6 | 编号对照表 / README / 需求大纲 | 列 `dp_device_queue`（代码不存在）、漏 `di_snapshots`；README 写「17 Tool」实为 **12**；需求大纲 §5.9 仍提已下线的 Blockly（PRD-09 v5.2） | ⚠️ 文档待同步 |
| 7 | `gen_arch_stats.py` | 步骤类型计 **45**，而 `models/step_types.py` 实测 `StepType` **37** 成员、`STEP_TYPE_META` **29** 条、`UI_LABELS` **28** 条（2026-09-14 复核） | ⚠️ 残留待修；其余已修（2026-08-21：指向 ARCH-00、re_path/多行 path/空串路径计数、di_/ev_ 前缀识别、cm_ 分表 models_*.py） |
| 8 | 契约出入 4 处 | `display_info()` 补入、`swipe` 坐标制、`start_app` 落 Airtest、`press_key` 新增原语 | ⚠️ L1c 详档权威裁定 |
| 9 | 平铺信封 2 处 | report_generator / workflow legacy 响应平铺 `{status, ...}`（非 `{status, data}`），前端已按各端点结构适配 | ⚠️ 已登记（ARCH-07/09 + PRD-07/09 §5 章首），与 §1.5 统一信封例外 |
| 10 | 子 ARCH 五层口径 | ARCH-01~09 曾用旧三层口径与 L2/L3 图标签（与本文 L0~L4 层义冲突，迁移 Checklist §一 已预警） | ✅ 已回填（2026-08-21，v3.1 配套；各子文档版本号同步递增） |
| 11 | ~~e2e 真机 + 双设备并行专测~~ | 原计划在 DeviceSession 落地后执行（沙箱无真机） | ✅ 已随执行引擎下线而失效（test_runner 已下线；设备域真机验收待新的执行链出现后再立） |
| 12 | P2 灰度切换 | 新旧引擎同用例集对比、serial 白名单全量放开未执行 | ⏸ 延后（§4.3 硬约束：第二个引擎出现前禁止新增引擎；自迁移 Checklist §五 移交，2026-08-21） |

---

## 二、分层架构逐层说明（L2 已空置）

| 层 | 代码位置 | 关键组件 / 协议 | 依赖方向（✅ 允许 / ❌ 禁止） |
|----|---------|----------------|------------------------------|
| **L0 第三方与外部目标** | 外部库 + 📱设备 / 🌐浏览器 / 🔗被测 API | uiautomator2（感知）、Airtest（操作）、cnocr/Pillow（OCR）、Playwright（浏览器）、requests（被测 API） | ❌ u2/Airtest 只能被 `engines/device` 触碰（apps/ 内实测 **0 命中**）；Playwright 仅 `tests/e2e`（pytest-playwright，产品代码零消费）；requests 仅 `ai_assistant` / `evaluator` 的外部 HTTP 调用；cnocr 仅 `algorithms/` |
| **L1a 算法层** | `algorithms/`：`xpath.py` · `hierarchy.py` · `vision/ocr.py` | `gen_xpath_candidates`（8 类 XPath 候选 + O(1) 索引）、`parse_hierarchy_xml`（截断检测修复）、`recognize`（cnocr 惰性单例） | ✅ 第三方纯库 + `models.*`（仅类型，D-2）；❌ `apps.*` / `engines.*` / `django.*`（实测零命中） |
| **L1b 领域模型** | `models/`：`step_types.py` · `test_models.py` · `constants.py` · `ui_nodes.py` | `StepType`（37 枚举）、`TestRunStatus`（5 小写）、`TaskOutcome` / `TaskCardStatus`、`Node` dataclass、`STEP_TYPE_META`（29 注册表） | ✅ 仅标准库；❌ 一切外部模块（零 Django import） |
| **L1c 引擎层** | `engines/device/`：`base.py` · `registry.py` · `connection.py` · `android/u2.py` | `UiEngine` Protocol：生命周期 4（connect/disconnect/is_alive/reconnect）+ 感知 3（screenshot/dump_hierarchy/app_current）+ 操作原语 8（click/long_click/swipe/input_text/press_key/shell/start_app/stop_app）+ `capabilities` 门控（xpath_locate/toast_wait/ocr）；`ENGINE_REGISTRY = {"u2": ...}` + `DEFAULT_ENGINE = "u2"` + `get_device_engine()` fail-fast（未知引擎抛 `ConfigurationError`，无静默回退）；`U2Engine` 双栈实现 + `probe_u2` / `fetch_device_info`；引擎**无状态、短连接**（`open_engine` 每次新建并连接，调用方用完 `close_engine`） | ✅ 第三方 + `models.*` + `algorithms.*`（纯函数，D-1 裁决）；❌ `apps.*` / `django.*`（实测零命中） |
| ~~**L2 设备交互中台**~~ | —（层已空置，无代码落点） | 2026-09-03 归档变更 `flatten-device-session` 删除了 `apps/device_pool/session.py`：把「惰性连接 + per-serial 锁」塞进引擎的诉求被否决（引擎保持无状态、短连接），「租用」与既有业务锁重复 → 收敛到 `DeviceLock`，上层改直调 `engines.device.registry` 工厂 | ❌ 禁止重建此层（不得新增设备交互中间层） |
| **L3 业务 App** | `apps/` 11 App（test_runner 已下线，仅卸表迁移）+ `gateway/`（middleware/routing）+ `shared/`（auth/renderers/users） | 请求解析 → `api.py` 写收敛 → ORM；`ai_assistant.tools`（`TOOLS` + `TOOL_META`）12 Tool 编排（执行引擎已下线，平台内无任务状态流转） | ✅ 本 App + 他 App `api.py`/models（只读）+ `engines.device.registry`（引擎工厂）+ `algorithms`/`models`；❌ engines 引擎实现直触 / 裸句柄、他 App 内部实现 |
| **L4 前端** | `frontend/src/`：`modules/`（8）+ `shared/` + `views/`（登录壳） | Vue 3 + Vite；`shared/`：api-client · JWT 拦截器 · WS/SSE 消费 · composables · patterns 组件 · design tokens；测试 `frontend/tests/`（vitest） | ✅ 仅 HTTP/WS/SSE；❌ 后端模块 / 数据库 / 文件 I/O / AI 推理 / ADB |

---

## 三、平台模块架构

### 3.1 模块依赖关系图

> 箭头方向 = import 方向。实线 = 跨 App 读 api.py/Model（合法），点线 = dashboard 只读聚合。

```mermaid
flowchart TD
    subgraph FRONTEND["L4 前端 (Vue 3 + Vite · 8 模块)"]
        F_DP["设备管理"]
        F_DI["设备检查器"]
        F_EL["元素定位"]
        F_CM["用例管理"]
        F_RG["测试报告"]
        F_AI["AI 助手"]
        F_OTH["仪表盘 · 工作流工作台"]
    end

    subgraph BACKEND["L3 后端 (Django :8766 · 11 App)"]
        B_ACC["accounts 认证（无自有表）"]
        B_DI["device_inspector<br/>di_ · 快照化"]
        B_DP["device_pool<br/>dp_ · 设备状态 / 业务锁"]
        B_EL["element_locator<br/>el_"]
        B_CM["case_manager<br/>cm_"]
        B_RG["report_generator<br/>rg_ · 只读（列表为空）"]
        B_WF["workflow<br/>wf_"]
        B_EV["evaluator<br/>ev_"]
        B_AI["ai_assistant<br/>ai_ + tools.py 工具层"]
        B_DASH["dashboard 无表 · 纯只读聚合"]
    end

    subgraph MID["L1"]
        ENG["engines/ · algorithms/ · models/"]
    end

    F_DP -->|"HTTP"| B_DP
    F_DI -->|"HTTP"| B_DI
    F_EL -->|"HTTP / WS"| B_EL
    F_CM -->|"HTTP / WS"| B_CM
    F_RG -->|"HTTP"| B_RG
    F_AI -->|"HTTP / SSE"| B_AI

    B_DI -->|"api.device / models"| B_DP
    B_CM -->|"api.simple_yaml_dump / models"| B_EL
    B_EV -->|"api / models"| B_AI
    B_AI -->|"api（经 tools.py 工具层）"| B_DP
    B_AI -->|"api / models"| B_EL
    B_AI -->|"api"| B_CM
    B_AI -->|"api（只读）"| B_WF
    B_DP -->|"engines.device.registry 工厂"| ENG
    B_DI -->|"api"| B_EL

    B_DASH -.->|"只读聚合"| B_DP
    B_DASH -.->|"只读聚合"| B_EL
    B_DASH -.->|"只读聚合"| B_CM
    B_DASH -.->|"只读聚合"| B_AI
    B_DASH -.->|"只读聚合"| B_WF

    style FRONTEND fill:#e3f2fd,stroke:#2196f3
    style BACKEND fill:#e8f5e9,stroke:#4caf50
    style MID fill:#a78bfa,stroke:#7c3aed
    style B_DASH fill:#f7cd67,stroke:#3a7a10
    style B_DP fill:#6fba2c,color:#fff
    style B_AI fill:#f7a8c4,color:#3a7a10
```

### 3.2 后端 App 速览（活跃 10 个；test_runner 已下线，仅保留卸表迁移）

> **口径**：表 = 各 App `models*.py` 中 `db_table` 字面声明数；端点 = 各 App `urls.py` 中 `path()` / `re_path()` 静态条目数（`tools/gen_arch_stats.py:59-75`）——**DRF `DefaultRouter` 展开的 ViewSet 路由不计**，故路由化的 App 静态条目少（`case_manager` 只有 `*router.urls` + `move/` → 1；`workflow` 13；`ai_assistant` 25，含 Batch 1-3 新增的 APIView）。AI Tool 列按 `apps/ai_assistant/tools.py::TOOL_META` 的 `module` 归属，不按函数所在文件。完整契约以各模块 ARCH + 同号 PRD §5 为准。
> 数字实测时间：2026-09-14（`python tools/gen_arch_stats.py --json`）；ai_assistant DRF 迁移仍在推进，其端点数字会变。

| App | 层 | 表 | 端点 | 范式 | 一句话职责 | AI Tool |
|-----|----|:--:|:--:|------|------|:--:|
| `accounts` | L3 | 0（用 `auth_user`） | 5 | DRF APIView | 平台唯一登录入口，JWT 签发/刷新/黑名单 | — |
| `dashboard` | L3 | 0（纯聚合） | 4 | DRF APIView | 首页只读聚合：统计卡片/趋势图/活动时间线 | — |
| `device_pool` | L3 | `dp_`×2 | 10 | `@api_view` | 设备发现/注册/心跳/锁（原 L2 会话层已扁平化，业务锁即租用） | 9 |
| `device_inspector` | L3 | `di_`×1（快照） | 7 | 裸 view | 快照式页面抓取（Dump/OCR）→ `di_snapshots` → 导入元素定位 | 1 |
| `element_locator` | L3 | `el_`×10 | 31 | 混合 | 元素资产仓库：页面树/元素 CRUD/跳转流（Web/API 域同构） | — |
| `case_manager` | L3 | `cm_`×4 | 1 | 混合 | 用例编排中枢：目录树/步骤编排/YAML 导入导出（路由已 DRF 化，router 展开的端点不计入静态条目） | — |
| `report_generator` | L3 | `rg_`×2 | 6 | 裸 view | 只读报告：列表/详情/下载（执行引擎已下线，列表为空；LOG_DIR 残留文件仍可下载） | — |
| `ai_assistant` | L3 | `ai_`×7 | 25 | **DRF 已迁（Batch 1-3 收官；SSE/工具网关豁免）** | AI 中枢：进程内 AgentScope + 12 Tool + SSE + HITL + 共享工具箱 | 宿主 12 |
| `workflow` | L3 | `wf_`×3 | 13 | 混合 | 页面流可视化编排：VueFlow 节点图（5 类节点）→ JSON 落库 `wf_`（Blockly 已下线，PRD-09 v5.2） | 2 |
| `evaluator` | L3 | `ev_`×4 | 14 | 混合 | LLM 评测：题库/评测运行/人工打分 | — |

### 3.3 前端模块清单（8 个 + shared）

| 模块 | 定位 | 主要交互（抽象角色） |
|------|------|---------------------|
| `dashboard` | 首页聚合 | 统计卡片 · 趋势图 · 任务面板 · 活动时间线 |
| `device-pool` | 设备管理 | 设备卡片 · 锁状态 · 连接表单 · 排队列表 |
| `device-inspector` | 快照检查器 | 抓取表单 · 截图展示 · 元素/OCR 表格 · 快照列表 |
| `element-locator` | 元素资产 | 页面树 · 候选面板 · 元素表 · Web/API 分组树 |
| `case-manager` | 用例编排 | 目录树 · 步骤编排器 · 用例编辑器 |
| `report-generator` | 报告查看 | 报告列表 · KPI/趋势 · 详情页 |
| `ai-assistant` | AI 对话 | 对话窗口 · 智能体看板 · 工具箱 · 知识库 · 评测页 |
| `workflow` | 页面流编排 | 目录树 · 节点图画布 · 文件浏览器 |
| `shared/`（共享层） | 平台公共能力 | api-client · JWT 拦截 · WS/SSE · composables · patterns 组件 · design tokens |

---

## 四、关键机制

### 4.1 写操作收敛（api.py）

所有 INSERT/UPDATE/DELETE 必须经**本 App `api.py`**（`__all__` 白名单导出）；跨 App 写走**目标 App 的 `api.py`**。视图层/serializer/consumers 禁止直写 ORM。AI Tool 与工作流同步同样只经 api.py。

### 4.2 执行引擎与任务状态机（已下线）

原 `test_runner/state_machine.py` 曾是 `tr_` 表状态的**唯一流转入口**（迁移表 `idle→queued→running→done`、`select_for_update` 事务原子、非法迁移抛 `InvalidTransition`、REST 下发权威 `state`）。该模块随 `1c4c47cf` 七步重构删除，`tr_*` 4 表由迁移 `0020_delete_test_runner_models` 卸载，`apps/test_runner/AGENTS.md` 明确**禁止恢复** views / urls / WS / 执行器。

现状：平台**无执行引擎、无任务状态流转**；`models/test_models.py` 的 `TestRunStatus` / `TaskCardStatus` / `TaskOutcome` 枚举定义保留（见 §8.3），但已无消费方（`apps/` 内零引用）。登记见 §1.6 #1/#5。

### 4.3 引擎注册表与可替换（DEVICE_ENGINE）

`engines/device/registry.py`：`ENGINE_REGISTRY` 白名单（当前仅 `"u2"` → `engines.device.android.u2.U2Engine`）+ `DEFAULT_ENGINE = "u2"` + `get_device_engine(name)` 惰性 import；未注册/构建失败抛 `ConfigurationError`（fail-fast，无静默回退）。换引擎 = 只改 `settings.DEVICE_ENGINE`（默认 `"u2"`，见 §七）。

引擎**无状态、短连接**：`open_engine(serial, addr)` 每次新建引擎并连接，调用方用完 `close_engine(engine)` 断开；实例锁 / 进程内缓存 / connect 幂等曾在 `flatten-device-session` 中尝试，已按「无收益」全部回退（同设备互斥由业务锁保证）。

新增引擎须通过 `openspec/specs/engine-protocol/spec.md` 的契约测试（连接/感知/操作/能力声明四组，零真机依赖）方可注册；注意其测试基类 `EngineContractTestBase` **尚未在代码中落地**（全仓 0 命中，§1.6 未登记），新增引擎时需一并建立。

> 硬约束（源自已归档的目标架构总纲 §八）：第二个引擎出现之前，禁止新增任何引擎实现（防止过度设计）。

### 4.4 设备消费与业务租用（原 L2 已扁平化）

**设备交互没有中间层。** 上层直接经引擎工厂取引擎（短连接，用完即断）：

- 工厂：`engines.device.registry.open_engine(serial, addr)` / `close_engine(engine)`；
- 消费方：`apps/device_pool/views.py`（连接验证）、`apps/device_inspector/{service,api}.py`（快照抓取）、`apps/ai_assistant/tools.py`（设备动作 Tool）。

**「租用」= 业务锁，不是物理会话。** `apps/device_pool/api.py` 的白名单 `acquire_device(serial, user_id, timeout)` / `release_device(serial, reason)` 操作 `dp_device_locks`（`DeviceLock`，`lock_type=process`，兜底 TTL 30 分钟由心跳回收）；同设备互斥由该业务锁保证，引擎侧不再加锁（`flatten-device-session` 决策 D2/D4）。

> 历史：2026-08-20 `introduce-device-session` 曾落地 `DeviceSession.lease()`（`LeaseMode` TRANSIENT/EXCLUSIVE、per-serial 锁、`LeaseConflict`→409）与 `DEVICE_SESSION_ENABLED` 开关；2026-09-03 `flatten-device-session` 判定该中间层与业务锁职责重复、且「惰性连接 + 锁」塞进引擎不成立，遂**删除 `session.py` 与该开关**，调用链由 `上层 → pool → session → engine` 扁平为 `上层 → engine`；`pool.py` 只保留「当前激活设备」指针（23 行）。

### 4.5 AI 工具编排与 SSE

`apps/ai_assistant/tools.py` 是工具**单一真相源**：`TOOLS`（**12 个**工具）+ `TOOL_META`（`(分类, module, action)`，**3 类**）+ `TOOL_CATEGORIES` + `AUTO_ALLOW_TOOLS`（6 个免 HITL）；`(module, action) → handler` 进程内直调，handler 内部只 import 各 App `api.py`/models；框架包装与装配在 `engines.ai.agentscope.tool_wrapper`（`build_toolkit` ← `model.py:300`）。SSE 单请求 async view + `asyncio.Queue`，AgentScope `reply_stream` 逐 token 输出；HITL 确认线程安全；能力开关决定 Toolkit 组装；MCP/Skill 统一由共享工具箱（`ai_shared_tools`）导入，智能体禁止自配置。Tool 清单见附录 A.3。

### 4.6 枚举真相源（models/）

`models/` 是枚举与领域类型的**唯一真相源**：`StepType`（37）、`TestRunStatus`（5 小写）、`TaskOutcome`、`TaskCardStatus`、`DeviceStatus`（2 态）、`Node` 等。App 禁止重定义枚举、禁止字符串硬编码；前端经 `GET /cases/step-types` 拉取 `STEP_TYPE_META`（29 项注册表）。任务状态枚举（`TestRunStatus` / `TaskOutcome` / `TaskCardStatus`）定义保留，但随执行引擎下线已无消费方（§4.2）；原 `0019_backfill_lowercase_run_status` 回填随 `tr_` 表卸载作废（§1.6 #5）。

---

## 五、文件地图

### 5.1 架构文档索引

```
dev_docs/03-设计与架构/
├── ARCH-00-平台总体架构.md              ← 本文档（总纲）
├── ARCH-01~09（9 份子模块架构）          ← 仪表盘/设备管理/设备检查器/元素定位/用例管理/执行引擎/测试报告/AI助手/工作流工作台
├── ../_archive/（dev_docs 级归档区）      ← 设计-* 目标架构系列 + 迁移 Checklist（2026-08-21 归档：内容已吸收进本文与 openspec/specs/）
├── 技术栈参考.md
└── README.md                             ← 目录索引

openspec/specs/                           ← 正式契约
└── engine-protocol/spec.md
```

### 5.2 代码文件地图

```
Android-AutoTests/
├── frontend/src/                ← L4：modules/(8 模块) · shared/ · views/(登录壳)
├── apps/                        ← L3：11 个 Django App + gateway 网关
│   ├── accounts/ dashboard/ device_pool/ device_inspector/
│   ├── element_locator/ case_manager/（test_runner/ 仅卸表迁移）
│   └── report_generator/ ai_assistant/ evaluator/ workflow/
├── engines/device/              ← L1c：base.py(协议) · registry.py(工厂) · connection.py · android/u2.py
├── algorithms/                  ← L1a：xpath.py · hierarchy.py · vision/ocr.py
├── models/                      ← L1b：step_types.py · test_models.py · constants.py · ui_nodes.py
├── gateway/                     ← middleware.py(JWT) · routing.py(WS 0 生产点) · normalize_slash.py
├── shared/                      ← auth/(jwt_auth·drf_auth·require_auth) · renderers.py · users.py
├── config/                      ← settings.py(开关) · urls.py(路由挂载) · asgi.py
├── tools/gen_arch_stats.py      ← 架构统计/边界检查
└── openspec/                    ← changes/archive(18) · specs/(2 份契约)
```

---

## 六、关键设计决策

| 决策 | 理由 |
|------|------|
| **分层 + 单向依赖（L2 已扁平化）** | 引擎 / 算法 / 枚举各归其层，App 层不直触第三方设备库；设备交互不设中间层，避免与业务锁职责重复 |
| **引擎可替换（DEVICE_ENGINE + fail-fast）** | 换引擎只改配置；未注册引擎启动即报错；新引擎须过 `engine-protocol` 契约（测试基类尚未落地，见 §4.3） |
| **设备租用 = 业务锁，不建会话中间层** | 同设备互斥由 `DeviceLock` 保证；引擎保持无状态、短连接；避免会话层与业务锁两套互斥（2026-09-03 扁平化） |
| **算法纯函数下沉（原处 re-export 兼容）** | XPath/层级/OCR 零框架依赖，可独立测试；D-1/D-2 裁决 engines↔algorithms↔models 边界 |
| **枚举真相源唯一（models/）** | App 禁重定义、禁字符串硬编码；任务状态枚举随执行引擎下线已无消费方 |
| ~~状态权威后端下发~~ | 原为执行进度设计（前端只镜像 running）；执行引擎下线后该机制随之失效（§4.2） |
| **前端永远不直连数据库** | 所有数据来自 API/WS/SSE，链路可控、可审计 |
| **AgentScope 同进程调 Django** | Tool 直接 import api.py，不走 HTTP，零网络开销 |
| **DRF 双范式收敛** | 信封/JWT/写收敛/统一路由四机制统一风格；旧端点稳定运行，逐步迁移（ai_assistant Batch 1-3） |
| **SSE + 阻塞 POST 兜底** | AgentScope/Redis 不可用时自动降级为同步模式 |
| **检查器快照化** | 截图/层级抓完即走，无持续占用；快照落 `di_snapshots` 可回看 |
| **Redis 黑名单 + Channels** | 服务重启不丢失；Redis 不可用降级 InMemory/放行验证 |
| **锁审计日志永不删除** | 通过 status 追踪生命周期，支持审计回溯 |
| ~~执行前保存用例快照~~ | 原为执行任务保存 `selected_cases`；执行引擎下线后该机制随之失效 |
| **OpenSpec 规格化** | 引擎协议以 spec.md 为正式契约，变更走 change 流程（会话协议 spec 待退役） |

---

## 七、部署架构

```
开发环境 (macOS / Windows)
─────────────────────────────

  Vue Dev Server    :5173    Vite HMR + proxy
  Django Daphne     :8766    ASGI HTTP + WebSocket（纯 ASGI，无 wsgi.py）
  AgentScope        in-process（运行于 Django 进程内，无独立端口）
  Redis             :6379    JWT 黑名单 + Channels（不可用降级 InMemory）
  数据库            MySQL 默认 / SQLite 可切（settings.DB_ENGINE）

  关键开关（环境变量）：
    DB_ENGINE              mysql（默认）/ sqlite
    DEVICE_ENGINE          u2（默认）——引擎白名单键（engines/device/registry.py）
    DJANGO_ALLOWED_HOSTS   "*"（DEBUG=True 默认）/ "127.0.0.1,localhost"（DEBUG=False 默认）——逗号分隔
    CORS_ALLOW_ALL_ORIGINS True（DEBUG=True 默认）/ False（DEBUG=False 默认）
    CORS_ALLOWED_ORIGINS   空（默认）——生产关闭 allow-all 后的来源白名单，逗号分隔
    SECURE_HSTS_SECONDS    0（默认 = 关闭）——HSTS 有效期；确认全站 HTTPS 后再设置
    SECURE_SSL_REDIRECT    False（默认）——仅「Django 直接终止 TLS」时开启；反代已终止 TLS 时开启会 301 循环
    SECURE_PROXY_SSL_HEADER 未启用（默认）——反代场景信任 X-Forwarded-Proto
    SESSION_COOKIE_SECURE / CSRF_COOKIE_SECURE  DEBUG=False 默认 True（本地自动 False）

  CSRF：`CsrfViewMiddleware` 排在 `JWTAuthenticationMiddleware` 之后 —— 有效 JWT 的请求由中间件置
  `request._dont_enforce_csrf_checks` 豁免（浏览器无法跨站携带自定义 Authorization 头），
  后台 `/admin/` 等 session 面正常受保护。

  一键启动: python run.py start
  一键停止: python run.py stop
  状态检查: python run.py status

  运维例外（不属 D0 装配语义）：python run.py stop 会清理 MySQL 孤儿 Sleep 连接
  （information_schema.PROCESSLIST 查询 + KILL）—— best-effort 运维动作，不承载业务读写。
```

---

## 八、平台统一定义

### 8.1 步骤类型（`models/step_types.py::StepType`，唯一真相源）

**37 种枚举** = 8 基础 UI + 8 deprecated 旧名 + 9 `adb_` 新名 + 4 API + 8 Web：

| 分类 | 枚举值 |
|------|------|
| 基础 UI（8） | `CLICK` · `LONG_CLICK` · `SWIPE` · `WAIT` · `WAIT_DISAPPEAR` · `SLEEP` · `VERIFY_TEXT` · `POLL_TEXT` |
| deprecated 旧名（8） | `START_APP` · `KILL_APP` · `PERF_ELEMENT_TIME` · `WAIT_TOAST` · `IF_ELEMENT_APPEAR` · `IF_ELEMENT_DISAPPEAR` · `LOOP_N` · `LOOP_ELEMENTS` |
| adb_ 新名（9） | `ADB_START_APP` · `ADB_KILL_APP` · `ADB_WAIT_TOAST` · `ADB_PERF_ELEMENT_TIME` · `ADB_IF_APPEAR` · `ADB_IF_DISAPPEAR` · `ADB_LOOP_N` · `ADB_LOOP_ELEMENTS` · `ADB_POLL_TEXT` |
| API（4） | `API_REQUEST` · `API_ASSERT` · `API_SLEEP` · `API_LOG` |
| Web（8） | `WEB_NAVIGATE` · `WEB_CLICK` · `WEB_FILL` · `WEB_TYPE` · `WEB_WAIT` · `WEB_ASSERT` · `WEB_SCREENSHOT` · `WEB_STEP` |

> 前端编排器注册表 `STEP_TYPE_META` 为 **29 项**（不含 8 个 deprecated），供用例管理步骤编排器拉取。工作流工作台的 Blockly 积木已于 PRD-09 v5.2 下线（步骤编排归用例管理），现仅保留 VueFlow 页面流。

### 8.2 设备状态（`apps/device_pool/models.py`）

**2 种状态**：`ONLINE` · `BUSY`。设备离线或断开即删除记录，不存在 `OFFLINE`/`DISCONNECTED` 持久状态。锁审计日志永不删除，通过 `status`（active/released/expired）追踪生命周期。

### 8.3 任务状态（`models/test_models.py`，枚举保留但已无消费方）

| 枚举 | 值 | 用途 |
|------|----|------|
| `TestRunStatus` | `pending` · `running` · `completed` · `stopped` · `failed`（小写） | 单次执行状态（唯一真相源） |
| `TaskCardStatus` | `idle` · `queued` · `running` · `done` | 任务卡片状态机 |
| `TaskOutcome` | `completed` · `stopped` · `interrupted` · `error` | 终态细分 |

> 执行引擎已下线（§4.2）：本节枚举仍由 `models/test_models.py` 提供，但 `apps/` 内已无引用方。

### 8.4 WebSocket 通道（`gateway/routing.py`，0 生产点）

`websocket_urlpatterns` 现为**空表**（`gateway/routing.py:9`），**禁止新增生产点**（通道收敛唯一真相源）。历史端点：

| 端点 | Consumer | 状态 |
|------|----------|------|
| `ws/test-run/{run_id}` | `TestRunConsumer`（test_runner） | ✅ 已移除（执行引擎下线） |
| `ws/case-editing/{case_id}` | `CaseEditingConsumer`（case_manager） | ✅ 已移除（文档用例重构后下线） |
| `ws/screenshot/…` | `ScreenshotConsumer`（device_inspector） | ✅ 已移除（v1.7 快照化） |

---

## 附录A：架构事实统计（2026-09-14 代码实测）

> **口径**（读自 `tools/gen_arch_stats.py`）：表 = 各 App `models*.py` 中 `db_table` 字面声明数（`:59-66`）；端点 = 各 App `urls.py` 中 `path()` / `re_path()` 静态条目数（`:68-75`，DRF `DefaultRouter` 展开的 ViewSet 路由不计）；Tool = `apps/ai_assistant/tools.py::TOOLS` 条目数（`:94-127`）。
>
> 实测基准：**33 张表 · 8 组前缀 · 116 条路径端点 · 12 个 Tool（3 类）· 8 个前端模块 · 0 个 WS 生产点**（2026-09-14，`python tools/gen_arch_stats.py --json`）。本附录已按该基准逐 App 回填。

### A.1 Django App 清单（活跃 10 个；test_runner 已下线，仅保留卸表迁移）

| App | 表 | 端点 | 层 | Tool |
|-----|:--:|:--:|----|:--:|
| `accounts` | 0 | 5 | L3 | — |
| `ai_assistant` | 7 | 25 | L3 | 宿主 12 |
| `case_manager` | 4 | 1 | L3 | — |
| `dashboard` | 0 | 4 | L3 | — |
| `device_inspector` | 1 | 7 | L3 | 1 |
| `device_pool` | 2 | 10 | L3 | 9 |
| `element_locator` | 10 | 31 | L3 | — |
| `evaluator` | 4 | 14 | L3 | — |
| `report_generator` | 2 | 6 | L3 | — |
| `workflow` | 3 | 13 | L3 | 2 |
| **合计** | **33** | **116** | — | **12** |

> 子文档端点口径（**同源不同口径，无冲突**）：各子 ARCH 记「逻辑端点」（含 DRF router 展开、legacy 与 router 并存计数），本文记「`urls.py` 静态条目」，故数字天然不同。本文当前值：元素定位 **31** · 用例管理 **1** · AI 助手 **25** · 工作流 **13**。子 ARCH 的历史对照值（ARCH-04 记 35 legacy / ARCH-05 记 31 条 path / ARCH-08 记 41 REST 方法 / ARCH-09 记 12 legacy）**待各子文档复测时同步**；ARCH-01 的 4 逻辑端点（含 `/devices/stats/`、`/cases/stats/`）与本文一致。

### A.2 数据库表清单（33 张 · 8 组前缀）

| 前缀 | App | 表名 |
|------|-----|------|
| `ai_` | ai_assistant | `ai_agents` · `ai_shared_tools` · `ai_platform_tools` · `ai_conversations` · `ai_messages` · `ai_tasks` · `ai_execution_logs` |
| `cm_` | case_manager | `cm_case_projects` · `cm_case_directories` · `cm_case_files` · `cm_test_definitions` |
| `di_` | device_inspector | `di_snapshots`（v1.7 快照化：dump/OCR 解析 JSON + 截图路径 + 统计） |
| `dp_` | device_pool | `dp_devices` · `dp_device_locks` |
| `el_` | element_locator | `el_locator_projects` · `el_locator_directories` · `el_pages` · `el_elements` · `el_page_flows` · `el_web_groups` · `el_web_elements` · `el_api_groups` · `el_api_endpoints` · `el_web_page_flows` |
| `ev_` | evaluator | `ev_question_banks` · `ev_questions` · `ev_runs` · `ev_results` |
| `rg_` | report_generator | `rg_reports` · `rg_report_templates` |
| `wf_` | workflow | `wf_prototypes` · `wf_directories` · `wf_documents` |

### A.3 AgentScope Tool 清单（12 个 · 3 类；真相源 `apps/ai_assistant/tools.py`）

| 分类（数量） | Tool（函数名） | `module.action` | 只读 |
|------|------|------|:--:|
| 设备管理（9） | `get_online_devices` | `devices.list_online` | ✅ |
| | `list_devices` | `devices.list_all` | ✅ |
| | `acquire_device` | `devices.acquire` | ❌ |
| | `release_device` | `devices.release` | ❌ |
| | `list_apps` | `devices.list_apps` | ✅ |
| | `device_action` | `devices.action` | ❌ |
| | `click_ratio` | `devices.click_ratio` | ❌ |
| | `drag_ratio` | `devices.drag_ratio` | ❌ |
| | `xpath_action` | `devices.xpath_action` | ❌ |
| 设备检查器（1） | `screenshot_page` | `inspector.screenshot` | ✅ |
| 工作流（2） | `list_page_flows` | `workflow.list_page_flows` | ✅ |
| | `get_page_flow` | `workflow.get_page_flow` | ✅ |

> `AUTO_ALLOW_TOOLS` 含 6 个**免 HITL 自动放行**工具：`acquire_device` · `release_device` · `device_action` · `click_ratio` · `drag_ratio` · `xpath_action`。

### A.4 前端模块清单（8 个）

| 模块 | 代码位置 |
|------|---------|
| `ai-assistant` · `case-manager` · `dashboard` · `device-inspector` · `device-pool` | `frontend/src/modules/` |
| `element-locator` · `report-generator` · `workflow` | 同上 |
| `shared/`（api-client · 拦截器 · WS/SSE · composables · patterns · tokens） | `frontend/src/shared/` |

### A.5 跨模块 import 实测（2026-08-20 实测；2026-09-14 移除 test_runner 相关边）

| 被依赖 App | 依赖来源（合法边） |
|------|------|
| `device_pool` | `device_inspector`（api.device/models）· `ai_assistant`（tools.py 工具层）· `dashboard`（models 只读） |
| `element_locator` | `case_manager`（api.simple_yaml_dump/models）· `device_inspector`（api.import_snapshot_page）· `ai_assistant`（tools.py 工具层）· `dashboard`（models 只读） |
| `case_manager` | `ai_assistant`（tools.py 工具层）· `dashboard`（models 只读） |
| `ai_assistant` | `evaluator`（api/models）· `dashboard`（api/models） |
| `workflow` | `ai_assistant`（api 只读）· `dashboard`（models 只读） |

**残留**：**无**。原两条残留（`state_machine.recover_orphans` 跨 App 直写、`device_pool.views/service` 与 `executors/ui` 直 import 引擎实现）已分别随 test_runner 下线与 `flatten-device-session` 消失（见 §1.6 #1/#2）；引擎消费统一经 `engines.device.registry` 工厂。

### A.6 工具校验结论

| 检查 | 结果 |
|------|------|
| `gen_arch_stats.py --check-boundaries` | ✅ 零违规（2026-09-14 复核：白名单为空、无已登记残留；原 A.5 的 `recover_orphans` 直写已随 test_runner 下线消失，不复存在所谓工具盲区） |
| `gen_arch_stats.py --check-md` | ⚠️ 运行通过（exit 0）但**目前只能提示「需要初始化 ARCH_STATS 区域」**——本文没有 `<!-- ARCH_STATS -->` 自动区域，故「表 / 端点与 A.1 一致」尚未被机器校验（2026-09-14 复核）。步骤类型 45 残留见 §1.6 #7 |
| `apps/` 内 u2/Airtest import | ✅ 0 命中（红线达标） |
| `engines/` `algorithms/` 零 apps/django import | ✅ 实测达标 |

---

## 变更记录

| 版本 | 日期 | 变更摘要 |
|------|------|----------|
| v3.4 | 2026-09-14 | **计数同步（对齐代码实测）**：表 35→**33**（8 组前缀）· 路径端点 143→**116** · Tool 26（7 组）→**12（3 类）**；A.2 补齐 `cm_case_files` / `el_locator_projects`·`el_locator_directories` / `wf_prototypes`；A.3 由「组」改写为「12 个工具 × `module.action` × 只读」明细；§4.5 工具真相源由已消失的 `agent_scope/tool_registry.py` 改为 `apps/ai_assistant/tools.py`（`TOOLS`+`TOOL_META`+`build_toolkit`）；§3.2/A.1 逐 App 回填并写明「端点 = `urls.py` 静态条目，router 展开不计」；§1.6 #6（README「17 Tool」实为 12）/#7（工具计 45 vs 枚举 37/注册表 29，仍待修）；A.6 更正 `--check-md` 实际能力（尚无自动区域） |
| v3.3 | 2026-09-14 | **设备域 + test_runner 域同步 HEAD**：按归档变更 `flatten-device-session` 删除 L2 设备交互中台描述（§1.1 层表、§1.2/§1.3/§3.1 图、§二 逐层表、§4.4、§5.2 目录树、§六 决策、§七 开关），改为「上层直调引擎工厂 + `DeviceLock` 业务租用」；引擎坐标修正（`engines/device/registry.py` · `android/u2.py` · `U2Engine` · `DEFAULT_ENGINE="u2"` · `DEVICE_ENGINE` 默认 `u2`），删「进程内缓存/线程安全」，标注契约测试基类 `EngineContractTestBase` 未落地；test_runner 下线同步（§1.5 范式与信封、§1.6 #1/#2/#5/#9/#11、§3.2/A.1 删行、§3.3/A.4 模块 9→8、§4.2 状态机、§8.3/§8.4、§A.2 `tr_` 行、§A.3 runner 组、§A.5 边、§A.6）；WS 生产点 2→0、前端模块 9→8；附录 A 加口径注（实测 33 表/116 端点/12 Tool） |
| v3.2 | 2026-08-21 | **设计-* 系列与迁移 Checklist 归档**：9 份目标架构/详档/实测文档 + Checklist 移入 `dev_docs/_archive/`（内容已吸收进本文与 `openspec/specs/`）；§1.6 新增 #11（e2e 真机+双设备专测待办）/ #12（P2 灰度切换延后，硬约束）；关联文档、§1.2 图注、§4.3 硬约束出处、§4.4 引用改指归档目录；§5.1 目录树修正（含原「设计-L0~L4 7 份」笔误） |
| v3.1 | 2026-08-21 | **子 ARCH 五层回填配套**：§1.5 信封例外（test_runner/report_generator/workflow legacy 平铺，登记 #9）；§1.6 增补 #9/#10、#2 补 executor-session-toggle 真机验证、#7 工具修复回写；§二 L0 触达口径修正（Playwright/requests 允许 test_runner API/Web 执行器）、L2 落地状态；§3.2/A.1 统计对齐修复后工具（dashboard 4、case_manager 31、test_runner 13+1 WS、ai_assistant 15，合计 143 + DRF 另计）+ 子文档端点口径对照注；§4.3 补硬约束（第二引擎前禁止新增引擎）；§4.4 DeviceSession 落地状态与开关真机验证；A.6 工具校验结论更新；关联文档补迁移 Checklist |
| v3.0 | 2026-08-20 | **五层架构现行化**：三层口径（前端/后端/AI）整体改为 L0~L4 五层（§一/§二）；§1.2 全景图与目标总纲 §一总览图同构（补充数据与存储节点）；新增 engines/algorithms/models/DeviceSession 分层说明与五层防火墙；WS 通道 3→2（检查器快照化移除 ScreenshotConsumer）；模块速览对齐工作区（di_snapshots、dp_ 2 表、范式列；**Blockly 下线修正**——workflow 仅 VueFlow 页面流）；统计对齐代码实测（35 表 9 前缀、26 Tool 7 组、37 枚举/29 注册表、138 路径端点 + DRF 另计）；新增 §1.6 契约偏差登记（8 项 ⚠️）；决策表并入五层决策与 OpenSpec 规格化；关联文档补目标架构详档与 OpenSpec specs |
| v2.1 | 2026-08-19 | 统计与口径回填：端点 167→163（路径条目口径）；表清单 dp_ 3→2；步骤类型 45→37 枚举；§3.2 通道 A 链路补设备检查器；模块速览校正元素定位/测试报告/设备检查器职责 |
| v2.0 | 2026-08-13 | 由 `架构大纲.md`（v1.4）全量校正后合并 `Mermaid-00` 三张图：App 9→11、表 31→35、端点 162→167、Tool 24/38→14、步骤 28→45、端口 :8765→:8766、AgentScope :8000→in-process |
| v1.x | 2026-07-16 ~ 07-28 | 见原 `架构大纲.md` 变更记录 |
