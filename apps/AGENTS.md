# Backend AGENTS.md — AI 约束

> 工作于 `apps/` / Django 后端时必须遵守。编写细则与决策树见 `.agents/skills/android-autotests-rules/references/*`（backend/python-code/api-conventions/database/security）；自测命令见 `apps/自测与检测指令.md`；关单自检用 skill `django-backend-check`。
> 版本：v1.1 · 最后更新：2026-08-21 · **同步约定**：全局事项（后端 WS 事件表、响应信封与特例、分层纪律、表前缀、契约总表）变更时，必须同步 `.agents/skills/android-autotests-rules/references/api-conventions.md`（+ 相关 rules）与 skill `django-backend-check`（checklist/calibration 对应口径），并镜像登记 `frontend/AGENTS.md`（信封特例 / WS 事件表为双边契约；通道 SSOT 见 `architecture.md` §一）；**App 专属约束**（红线/契约特例/协议/关单附加项）唯一落点为 `apps/{app}/AGENTS.md`，变更只改对应 App 文件。v1.0：对齐前端 CLAUDE 体系（三分类 §1 + 契约总表 + 信封特例登记 + 通道收敛），App 专属约束下沉 11 份 App 级文件；修正过期 WS 清单（`ws/screenshot` 已删除，截图流已快照化 REST、禁止恢复）。v1.1：吸收已归档 `dev_docs/_archive/后端claude笔记.md`（职责分层决策树→`python-code.md` §6、新 App 清单与防火墙反例→`api-conventions.md`、断裂点表→skill checklist、自评 3 问→§3、反面教材→§0.2），引用改指 rules/自测指令/skill。

**口诀**：View 只分发，写库走 api，跨模块不碰内部实现，JSON snake_case，错误要上报，重构先问值不值。  
**完成定义**：`manage.py check` + ruff 通过 ≠ 完成；相关单测/集成测与契约要对齐。

---

## 0. 动手前

1. 需求模糊 → 列 3～5 种理解让用户选，禁止默默挑一种执行。
2. 先读调用链：**urls → views/serializers → api.py → models**；有 WS 再读 `consumers` + `gateway/routing.py`。跨模块写先搜对方 api 白名单：`rg "__all__" apps/{other}/api.py`。**为什么先读 urls**：凭印象改 view 函数名前端仍打旧路径、漏 DRF router 注册则本地通而前端 404——路径以 urls.py 为真相源。
3. 查：`.agents/skills/android-autotests-rules/references/backend.md`（架构/中间件/端口/公开路径）、`api-conventions.md`（防火墙/信封/新 App 清单）、`python-code.md`（写法/行数上限/职责分层决策树）、`database.md`（表前缀/写路径）、`security.md`（Key 加密）；契约字段对照 → `dev_docs/03-设计与架构/工具-VUE_API_CONTRACT.md`；边界扫描 → `python tools/gen_arch_stats.py --check-boundaries`；**本 App 专属约束 → `apps/{app}/AGENTS.md`**。
4. 判边界：纯逻辑→①；Model/api 写库→②；HTTP/DRF→③；WS→④；AI Tool→⑤；跨界按序做。新 App 按 `api-conventions.md`「新 App 检查清单」落地。

---

## 1. 职责与红线

> 按执行时机分三类：**编写规范**（怎么写）· **分层与模块边界**（不许碰什么）· **契约规则**（接口必须长什么样）。

### 1.1 编写规范

> 命名/行数上限/类型注解/迁移纪律等代码编写规范统一收录于 **`.agents/skills/android-autotests-rules/references/python-code.md`**（架构与配置 → `backend.md`，表与写库 → `database.md`，安全 → `security.md`）；行为决策（改前四步 → 本文件 §0；职责分层决策树 → `python-code.md` §6）。本文件只保留分层边界与契约约束。

### 1.2 分层与模块边界

**内部层纪律**（口诀：View 只分发，写库走 api）：

| 层 | 只做 | 严禁 |
|----|------|------|
| `urls.py` | 路由 / `app_name` | 业务逻辑 |
| `views` / ViewSet | 解析、鉴权上下文、调 api、封信封 | 直接 ORM 写；重业务堆砌 |
| `serializers` | 入出参校验与 DTO | 复杂写副作用（写仍进 api） |
| `api.py` | 跨模块写操作（`__all__`） | 收 `request`；返回 Model/JsonResponse |
| `service` / executor | 本模块编排 | 被其他 App import |
| `models` | 表结构 / `db_table` / 索引 | 业务编排 |
| `consumers` | WS 推送 | 绕过 api 散落写库 |

- **写库路径**：View / Tool → `api.py` → ORM；跨 App 读 Model ✅，跨 App 写必须走对方 `api.py`。
- 改 api 签名：调用方、注解、docstring、单测同改；Serializer 与 Model/前端契约同改。

**L4 总体禁止（适用于任何后端代码）**：

| 禁止 | 说明 |
|------|------|
| 跨 App 内部实现 import | 禁 import `service` / `runner` / `consumer` / `state_machine`（防火墙 #1） |
| View / Consumer / Tool 直接 ORM 写 | INSERT/UPDATE/DELETE 必须走 api.py（读放开，写收敛） |
| api.py 收 request / 返回 ORM | api 参数为简单类型，返回值可 JSON 化 |
| 静默吞错 | 写操作 except 必须日志 + 对用户友好 `message` |
| 技术术语给用户 | 错误文案不暴露堆栈/SQL/内部路径/Key |

**通道收敛（全项目硬约束，唯一真相源 → `architecture.md` §一）**：

- 通道封闭集合（四条内部通道 + 禁止新协议 + SSE 已移除 + Redis/外部 LLM 边界）以 `architecture.md` §一 为准，本文不复制。
- WS 生产点唯一真相源 = `gateway/routing.py`（当前 2 个，**禁止新增**）；截图流已快照化，禁止恢复 WS 截图流。
- 所有 Consumer 必须在 `gateway/routing.py` 注册。

**App 边界索引（App 专属边界/契约/协议/关单项的唯一落点 → 各 `apps/{app}/AGENTS.md`）**：

| App | 落点 | 一句话提示 |
|------|------|-----------|
| accounts | `apps/accounts/AGENTS.md` | 全站鉴权入口，公开路径与中间件一致 |
| dashboard | `apps/dashboard/AGENTS.md` | 全平台唯一只读聚合区 |
| device_pool | `apps/device_pool/AGENTS.md` | 设备生命周期 + 状态机，30s 心跳 |
| device_inspector | `apps/device_inspector/AGENTS.md` | 快照抓取回看（REST），无 WS |
| element_locator | `apps/element_locator/AGENTS.md` | 三域资产 CRUD |
| case_manager | `apps/case_manager/AGENTS.md` | 用例定义编排 + 编辑锁 WS |
| test_runner | `apps/test_runner/AGENTS.md` | 执行状态机 + 进度 WS（10 事件） |
| report_generator | `apps/report_generator/AGENTS.md` | 报告只读 + FileResponse 下载 |
| workflow | `apps/workflow/AGENTS.md` | 编排文档 CRUD（legacy 平铺信封） |
| ai_assistant | `apps/ai_assistant/AGENTS.md` | 任务发布 + Tool 网关 |
| evaluator | `apps/evaluator/AGENTS.md` | 评估题库/运行/框架适配（前端 ai-assistant 寄宿） |

- 表前缀：`dp_` `el_` `cm_` `tr_` `rg_` `ai_` `wf_` `ev_` `di_`；`db_table` 显式指定。
- 文件上限：`urls` 200 / `views` 300 / `api|service` 400 / executor 500；超阶梯必须拆分而非继续堆。

**默认拒绝的重构**：无行为变化的大搬家；用函数内 import 掩盖循环依赖；过早万能 `helpers.py`；无测试保护的状态机/执行器迁移。**允许的低成本改进**：补类型注解、补 `__all__`、补友好错误文案、超限文件达阶梯阈值时附带拆分。

### 1.3 契约规则

- 响应信封 `{status, data}` / `{status, message}`；HTTP JSON **snake_case**（前端 camelCase 转换在前端侧）。
- **信封特例（legacy 平铺，已登记 ARCH-06/07/09 与前端 `AGENTS.md` §1.3，禁止新增，未收敛前禁止改造成信封式）**：
  - test_runner `/runner/*`：平铺 `{status, runs|tasks|active, ...}`；`GET /tasks` 列表字段为 **camelCase**（全平台唯一）。
  - report_generator `/reports/*`：平铺 + `FileResponse` 下载。
  - workflow legacy 路径（非 router 路径）：平铺 `{status, directory|document|documents|...}`。
- 契约对照：前端 api 层、`dev_docs/03-设计与架构/工具-VUE_API_CONTRACT.md`、本 App Serializer；改路径/字段必须双边同步。

**前后端契约总表（后端 App ↔ 前端模块 ↔ 通道）**：

| 后端 App | 前端模块 | 通道 |
|---------|---------|------|
| accounts | views/LoginView | HTTP |
| dashboard | dashboard | HTTP |
| device_pool | device-pool + device-inspector（设备列表） | HTTP |
| device_inspector | device-inspector | HTTP（无 WS） |
| element_locator | element-locator + case-manager/workflow（素材） | HTTP |
| case_manager | case-manager + test_runner（只读用例） | HTTP + **WS**（编辑锁） |
| test_runner | test-runner | HTTP + **WS**（进度） |
| report_generator | report-generator | HTTP（下载走 FileResponse） |
| workflow | workflow | HTTP |
| ai_assistant | ai-assistant + 各业务 App（经 Tool） | HTTP |
| evaluator | ai-assistant（寄宿） | HTTP |

---

## 2. 协议要点

**HTTP / DRF**：`urls.py` 为路径真相源 → View/ViewSet → Serializer → `api.py`。  
- 身份：`request.user_id`（JWTAuthenticationMiddleware 注入）；公开路径 `/api/ai/auth/*` `/admin/` `/static/`（与 `backend.md` 列表一致）。  
- 错误带 HTTP 状态码（400/401/403/404/409/500）。  
- 契约对照：前端 api、`dev_docs/03-设计与架构/工具-VUE_API_CONTRACT.md`、本 App Serializer。

**WS**：Consumer 必须在 `gateway/routing.py` 注册；事件 `type` 与前端一致；写库仍走 api。仅 2 生产点（§1.2 通道收敛）；事件表见 `apps/test_runner/AGENTS.md`（10 种）与 `apps/case_manager/AGENTS.md`（`case_updated`）。

**AI**：Tool 只调各模块 `api.py`（同进程直调，无 SSE）；依赖 Redis（见 `backend.md`）。

---

## 3. 关单前最短清单

```
[ ] python manage.py check
[ ] makemigrations --check（若动 Model）
[ ] ruff check + ruff format --check（相关路径）
[ ] pytest -m "unit or integration"（涉及接口再加 api）
[ ] 写库只经 api；无跨模块内部 import
[ ] 信封与 snake_case；写失败有 message/日志（App 特例见其 AGENTS.md）
[ ] 涉及跨模块 → gen_arch_stats.py --check-boundaries
[ ] 自评 3 问：① 删这个 App，其他 App 是否只经 api/Model 读受影响？② 写操作是否都能被 Tool 与 View 复用同一 api？③ diff 每行可追溯到需求？
```

App 级附加项（delta）→ 各 `apps/{app}/AGENTS.md` 关单段。详细门禁 → skill `django-backend-check`。完整自测命令 → `apps/自测与检测指令.md`。
