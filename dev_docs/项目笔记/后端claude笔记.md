# CLAUDE.md — 后端

> 本文定位：**行为决策** — 什么时候做什么、选什么方案。每次收到后端 / Django / apps 任务第一个读。  
> 短约束摘要 → `apps/CLAUDE.md`；自测指令速查 → `apps/自测与检测指令.md`。

## 文档速查

| 我要…… | 读这个 |
|------|------|
| 判断改动边界和步骤 | 本文 → 0️⃣ 改前四步 |
| 选写在哪一层（views / api / service / serializers） | 本文 → 职责分层决策树 |
| 查红线与文件上限 | `.claude/rules/python-code.md` + `.claude/rules/backend.md` |
| 查模块防火墙 / 响应信封 | `.claude/rules/api-conventions.md` |
| 查表前缀 / 写库路径 | `.claude/rules/database.md` |
| 改完代码自测指令 | `apps/自测与检测指令.md` |
| 改完 apps 关单门禁 | `.claude/skills/django-backend-check/` |
| 查前后端字段名对照 | `dev_docs/03-设计与架构/工具-VUE_API_CONTRACT.md` |
| 边界扫描 | `python tools/gen_arch_stats.py --check-boundaries` |

---

## 编码行为规范（默认取舍）

> 口诀：**View 只分发，写库走 api，跨模块不碰内部实现，JSON snake_case，错误要上报，重构先问值不值。**

### 1. 职责边界

| 层 | 只做 | 不做 |
|----|------|------|
| `urls.py` | 路由注册、`app_name` | 业务逻辑 |
| `views.py` / ViewSet | 解析请求、鉴权上下文、调 api/service、`JsonResponse` / DRF Response | 直接 ORM 写；塞进重业务 |
| `serializers.py` | 入参/出参校验与 DTO | 写库副作用（复杂写仍收敛到 api） |
| `api.py` | 跨模块可调用的写操作（`__all__` 白名单） | 收 `request`；返回 ORM 对象；返回 JsonResponse |
| `service.py` / executor | 本模块内部编排与副作用 | 被其他 App import |
| `models.py` | 表结构、`db_table`、索引、约束 | 业务编排 |
| `consumers.py` | WS 连接与事件推送 | 绕过 api 写库 |

```text
✅ View → api.create_xxx(...) → ORM
✅ AgentScope Tool → api.create_xxx(...) → run_sync → ORM
❌ View 里 Device.objects.create(...)
❌ case_manager import test_runner.service / state_machine
❌ api.py 返回 Model 实例给跨模块调用方
```

### 2. 写操作铁律

```
前端 HTTP → Django View → api.py → ORM
AgentScope Tool → api.py → run_sync() → ORM
Django Admin → ORM（仅管理员）
跨 App 读 Model ✅；跨 App 写 ❌（必须走对方 api.py）
```

- 写操作 `except` **必须上报**（日志 + 对用户友好的 `message`），禁止空 `except: pass` / 静默吞错。
- 用户可见错误**不暴露**堆栈、SQL、内部路径等技术术语。

### 3. 协议与命名

| 层 | 规范 |
|----|------|
| Python 变量/函数 | `snake_case` |
| 类 / Model | `PascalCase` |
| HTTP JSON | `snake_case` |
| 响应信封 | `{status: true, data}` / `{status: false, message}` |
| 表名 | 前缀 `dp_` `el_` `cm_` `tr_` `rg_` `ai_` `wf_` `ev_` + `db_table` 显式指定 |
| URL | `config/urls.py` include；app 内 `app_name` + `urlpatterns` |

### 4. 类型与实现同改

- 改 `api.py` 函数签名时：调用方（views / Tool / 其他 api）、类型注解、docstring、相关单测一次改齐。
- DRF：Serializer 字段与 Model / 前端契约同步；禁止「库已改字段、Serializer 仍旧名」。

### 5. 重构克制（默认不做）

除非有明确第二场景或缺陷驱动，否则拒绝：

- 仅为「风格统一」大拆 views 却无行为变化
- 过早抽「万能 helpers.py」
- 用函数内 import 掩盖循环依赖（应先修边界）
- 跨 App 为图省事直接 import service
- 无测试保护的状态机/执行器大搬家

**允许的低成本改进**：补类型注解、补 `__all__`、补友好错误文案、超限文件附带拆分（达阶梯阈值时）。

### 6. 关单前（后端至少覆盖）

```text
[ ] python manage.py check 通过
[ ] makemigrations --check 通过（改了 Model）
[ ] ruff check / format --check 相关路径通过
[ ] 相关 pytest -m "unit or integration"（涉及接口再加 api）
[ ] 写库只经 api.py；无跨模块 service import
[ ] 响应仍是 {status, data|message}；JSON snake_case
[ ] 写操作失败有 message / 日志，无静默吞错
[ ] diff 每行能追溯到用户需求
```

---

## 0️⃣ 改前准备（动手之前必走）

收到「改后端 / 加接口 / 修 Bug」后，不直接写代码。先走完下面四步。

### 第一步：理解需求，确认修改范围

```
需求明确（「给 case_manager 增加 config_json 字段」）→ 继续
需求模糊（「优化一下执行引擎」）→ 列 3-5 个具体理解让用户选
```

不确定时主动问：改哪个 App？改读还是写？要不要迁移？契约要不要动前端？

### 第二步：定位当前位置

```bash
# 1. 看路由真相源
#    apps/{app}/urls.py  +  config/urls.py

# 2. 按调用链读
#    urls → views/serializers → api.py → models.py
#    有 WS 再读 consumers.py + gateway/routing.py

# 3. 跨模块写？只搜对方 api.py 的 __all__
rg "__all__" apps/{other}/api.py
```

**为什么要先读 urls？** 反面教材：凭印象改 view 函数名，前端仍打旧路径；或漏掉 DRF router 注册，本地 curl 通了前端 404。

### 第三步：查约束规则

**通用约束：**

| 查什么 | 去哪看 | 守什么 |
|--------|--------|--------|
| 架构 / 中间件 | `.claude/rules/backend.md` | JWT、公开路径、端口、ASGI |
| 防火墙 / 信封 | `.claude/rules/api-conventions.md` | 写收敛、三道防火墙 |
| 代码写法 | `.claude/rules/python-code.md` | 命名、行数上限、views/api 职责 |
| 表与写库 | `.claude/rules/database.md` | 表前缀、写路径 |
| 安全 | `.claude/rules/security.md` | Key 加密、日志不吐密钥 |

**模块专属约束：**

| 模块 | 特殊约束 | 踩坑后果 |
|------|---------|---------|
| `accounts` | 登录/JWT/鉴权入口；公开路径与中间件列表一致 | 全站 401 或误放行 |
| `case_manager` | 步骤/`config_json` 结构与执行器字段对齐；目录树 case_type | 保存成功但执行失败 |
| `test_runner` | 状态机勿绕过；WS 事件 type 齐全；设备锁经 device_pool api | 进度卡死、状态脏写、设备泄漏 |
| `device_pool` | 状态机 ONLINE⇄BUSY；占用/释放只走 api | 设备死锁或状态漂移 |
| `device_inspector` | 截图流频率与 consumer 不阻塞；与 locator 协作 | WS 断流、卡顿 |
| `element_locator` | dump 前缀字段、`ApiEndpoint` 契约稳定 | 前端树/定位错乱 |
| `ai_assistant` | Tool 只调各模块 api；SSE 事件类型稳定；Redis 依赖 | 幻觉写库、对话中断 |
| `dashboard` | **只读聚合，禁止写操作** | 违反模块边界 |
| `report_generator` | 下载可能是 FileResponse 非 JSON 信封 | 前端当 JSON 解析失败 |
| `workflow` | 编排状态勿被外部直接篡改 | 画布/流程数据丢失 |
| `evaluator` | 评估接口契约与 Serializer 一致 | 评分结果对不上 |

### 第四步：判边界 → 跳转执行

```
改动涉及什么？
  ├── 只改纯函数 / 校验 / 无 DB           → ① 单元逻辑
  ├── 改 Model / migration / api 写库      → ② 数据与写路径
  ├── 改 HTTP 路由 / View / Serializer     → ③ 接口契约
  ├── 改 WS Consumer / 广播事件            → ④ 实时通道
  ├── 改 AgentScope Tool / SSE             → ⑤ AI 同进程集成
  └── 跨了多个边界                         → 按 ①→⑤ 顺序做
```

---

### 新 App 检查清单

```
[ ] apps/{name}/ 具备: models / views(或 views_drf) / api.py / urls.py / apps.py
[ ] models 显式 db_table + 正确表前缀
[ ] api.py 有 __all__；写操作参数为简单类型
[ ] config/settings.py INSTALLED_APPS 已注册
[ ] config/urls.py include 已注册
[ ] 若有 WS：gateway/routing.py 已注册
[ ] 前端：router.js + AppSidebar.vue 各 1 行（若暴露页面）
[ ] python manage.py makemigrations && migrate
[ ] python manage.py check 通过
```

---

## 职责分层决策树

写代码时按此顺序选择落点，**不可跳级乱塞**：

| 优先级 | 落点 | 适用场景 |
|:--:|------|------|
| 1 | 纯函数 / 模块内 util | 无 I/O 的转换、校验 |
| 2 | `api.py` | 任何 INSERT/UPDATE/DELETE；跨模块要复用的写 |
| 3 | `service.py` / executor | 本模块多步编排、设备/外部 I/O |
| 4 | `views` / ViewSet | HTTP 适配：解析、权限、调用 api、封信封 |
| 5 | `serializers` | DRF 入出参形状与校验 |
| 6 | `consumers` | WS 推送；写库仍回调 api |

**升级信号**：view 超过 ~300 行 → 抽 api/service；api 被 2+ App 需要 → 保持在提供方 api 并扩 `__all__`；出现循环 import → 边界画错，下沉共享或只经 api。

---

## ① 纯逻辑（零 DB / 零 HTTP）

### 修改铁律

1. 函数单一职责；显式参数，避免闭包偷捕。
2. 必须有类型注解；可单测。
3. 不在这里偷偷写 ORM。

### ① 改动验证

```
pytest -m unit
# 或
pytest tests/<module>/test_<file>.py -k <name>
```

---

## ② 数据与写路径（Model / migration / api）

### 修改铁律

1. 改字段 → `makemigrations` → 审查 operations → `migrate`。
2. 写库只进 `api.py`；`__all__` 同步导出。
3. `api` **不收 request**、**不返回 Model**、**不返回 JsonResponse**。
4. 跨 App 写对方数据 → 调对方 `api.py`，禁止本模块 ORM 写外表。

### ② 改动验证

```bash
python manage.py makemigrations --check
python manage.py check
pytest -m "unit or integration"
python tools/gen_arch_stats.py --check-boundaries
```

---

## ③ 接口契约（HTTP / DRF）

### 调用链

```
前端 api → /api/... → urls → views/ViewSet → Serializer → api.py → ORM
                                              ↓
                                    {status, data|message}
```

### 铁律

1. 路径以各 App `urls.py` 为真相源；改路径必须同步前端契约。
2. 业务 view 使用 JWT 体系（`@csrf_exempt` 等既有约定）；身份用 `request.user_id`。
3. 错误带合适 HTTP 状态码：400/401/403/404/409/500。
4. 字段 `snake_case`；与 `VUE_API_CONTRACT` / 前端 api 层对齐。

### ③ 改动验证

| 改动 | 验证 |
|------|------|
| 新增/改路由 | `curl` 或 `pytest -m api` 打真实路径 |
| 改 Serializer 字段 | 对照前端字段；跑相关 api 测试 |
| 改鉴权 | 无 token / 坏 token / 正常 token 三条路径 |
| 改响应形状 | 确认仍是 `{status, data\|message}` |

### 常见断裂点

| 问题 | 表现 | 原因 |
|------|------|------|
| 只改 Model 未改 Serializer | 前端缺字段 / 校验失败 | 契约不同步 |
| View 直接 ORM 写 | 边界扫描失败；Tool 复用不上 | 违反写收敛 |
| message 塞堆栈 | 用户看到技术细节 | 错误处理不当 |
| URL 未 include | 404 | 漏 `config/urls.py` |

---

## ④ WebSocket / 实时通道

### 注册

- Consumer 写在对应 App `consumers.py`
- **必须**在 `gateway/routing.py` 注册（中央路由）

当前已知：`ws/screenshot`、`ws/test-run/<run_id>`、`ws/case-editing/<case_id>` …

### 铁律

1. 推送事件 `type` 与前端 switch 一致，新增 type 必须双边同步。
2. Consumer 内写库走 api，不直接散落 ORM 写。
3. 截图流等高频通道避免阻塞事件循环。

### ④ 改动验证

| 改动 | 验证 |
|------|------|
| 新 WS 路由 | 注册后连上 101，能收到帧/事件 |
| 改 test-run 事件 | 跑一条任务，六类（或现行）事件都有处理 |
| 改截图流 | 页面预览不断流、不明显卡顿 |

---

## ⑤ AgentScope / AI 同进程集成

```
前端 SSE → Django AI views → AgentScope（进程内）→ Tool → 各模块 api.py → ORM
```

### 铁律

1. Tool **只调**目标模块 `api.py`，不 import service/runner 内部。
2. Redis 不可用时 AI 可能降级；改配置先看 `.claude/rules/backend.md`。
3. SSE 事件类型变更要同步前端笔记 §③。

### ⑤ 改动验证

| 改动 | 验证 |
|------|------|
| 新 Tool | 权限、参数校验、只走 api；手工或用例跑通 |
| 改 SSE | 流式回复 / 停止保留 / 错误可重试 |
| 写库 Tool | `--check-boundaries` + 集成测 |

---

## 文件行数阶梯（超限处理）

| 文件 | 上限 |
|------|:---:|
| `urls.py` | 200 |
| `views.py` | 300 |
| `api.py` / `service.py` | 400 |
| executor / adapter | 500 |
| `models.py` | 不限 |

达到上限 → 下个 PR 评估；超 1.5 倍 → 禁止纯堆砌，附拆分计划；超 2 倍 → 只允许拆分。

自查：`find apps -name "*.py" -exec wc -l {} \; | sort -rn | head -20`

---

## 最终验证（所有后端改动必走）

```
[ ] python manage.py check
[ ] python manage.py makemigrations --check   # 若动 Model
[ ] ruff check apps/ config/ gateway/ shared/ models/
[ ] ruff format --check apps/ config/ gateway/ shared/ models/
[ ] pytest -m "unit or integration"          # 相关范围即可
[ ] 涉及 HTTP → pytest -m api 或 curl 往返
[ ] 涉及跨模块 → gen_arch_stats.py --check-boundaries
[ ] 自评 3 问：
      1. 删这个 App，其他 App 是否只经 api/Model 读受影响？
      2. 写操作是否都能被 Tool 与 View 复用同一 api？
      3. diff 里每一行都能追溯到用户需求？
```

完整命令说明 → `apps/自测与检测指令.md`。
