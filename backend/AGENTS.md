# Backend AGENTS.md — AI 约束

> **适用范围**：整个 `backend/` —— `apps/`（12 个业务 app）、`gateway/`（JWT 中间件、路由、ASGI 装配）、
> `shared/`（公共能力）、`config/`（settings / urls / asgi）、`models/`。
>
> **AGENTS 层级**：一级约束 —— 根 `AGENTS.md` 优先于本文件；本文件优先于
> `backend/apps/AGENTS.md`（模块文档索引）。模块级口径在 `.agents/docs/apps/{app}/`，
> 由该索引导航，进入模块前先读。

**口诀**：View 只分发，写库走 api，跨模块不碰内部实现。  
**完成定义**：`manage.py check` + ruff 通过 ≠ 完成；相关单测/集成测与契约要对齐。

---

## 1. 职责与红线

1. 聚焦后端全局的**分层架构**设计与 **API 约定** —— 不止 `apps/`：`gateway/` 的鉴权与路由、
   `shared/` 的公共能力同受本节约束。


### 1.1 分层与模块边界

1. **内部层纪律** View 只分发，写库走 api

2. **写库路径**：View / Tool → `api.py` → ORM；跨 App 读 Model ✅，跨 App 写必须走对方 `api.py`。


### 1.2 硬性约束

1. **严禁** 跨 App 内部实现 import


### 1.3 契约规则

- 响应信封 `{status, data}` / `{status, message}`；HTTP JSON **snake_case**（前端 camelCase 转换在前端侧）。
- **信封特例**：无。报告接口（`/api/reports/*`）已于 2026-10-21 收敛为全局 `{status, data}`；旧 csv/md 文件下载端点已随 rework-test-report-inventory 退役。助手对话栏日志的 ticket 读取保持 `FileResponse` 附件语义（`assistant-log-ticket` 规格）。
- 契约对照：前端 api 层、本 App Serializer；改路径/字段必须双边同步。


## 2. 协议要点

**HTTP / DRF**：`urls.py` 为路径真相源 → View/ViewSet → Serializer → `api.py`。  
- 身份：`request.user_id` —— 由 `backend/gateway/middleware.py` 的 `JWTAuthenticationMiddleware` 从 `Authorization: Bearer` 的 `sub` 注入。  
- **公开路径以代码为真相源**：`backend/gateway/middleware.py` 的 `_is_public()`（`PUBLIC_PREFIXES`），本文件不另立唯一清单。当前列举：`/api/auth/login`、`/api/auth/register`、`/api/auth/refresh`、`/admin/`、`/static/`、`/media/`、`/api/schema/`、`/api/swagger/`。注意 `/api/auth/*` **不是通配**：`logout`、`me` 不在其列，仍需 JWT。  
- **三条显式旁路**（同样免 JWT，但不在 `PUBLIC_PREFIXES`）：`RETIRED_AUTH_PATHS`（已退役的 5 条 `/api/ai/auth/*`，直接放行）、`_is_log_ticket()`（助手日志一次性 ticket 的 GET）、`DRAIN_PATH`（`/api/system/drain/`，仅回环地址）。  
- 现状边界：中间件只校验 `/api/` 前缀，非 `/api/` 路径直接放行。  
- 错误带 HTTP 状态码（400/401/403/404/409/500）；停用账号另带 `code=account_disabled`。  
- 契约对照：前端 api、本 App Serializer。

**WS**：Consumer 必须在 `backend/gateway/routing.py` 注册。**当前 0 个生产点** —— `websocket_urlpatterns` 为空列表，知识助手实时语音与文字问答已随 `retire-engines-agents` 整体下线，任务进度与列表走 HTTP 轮询；保留空清单是为让 `backend/config/asgi.py` 装配保持稳定。新增 WS 前先走 OpenSpec 变更。

**AI**：Tool 只调各模块 `api.py`（同进程直调，无 SSE）。平台无外部 KV 依赖（Redis 已退役；吊销记录落库，channel layer 用内存实现）。

---

## 3. 关单前最短清单

```
[ ] python manage.py check
[ ] makemigrations --check（若动 Model）
[ ] ruff check + ruff format --check（相关路径）
[ ] python -m pytest -c tests/pytest.ini -m "unit or integration"（涉及接口再加 api）
[ ] 写库只经 api；无跨模块内部 import
[ ] 信封与 snake_case；写失败有 message/日志（模块特例见其模块文档）
[ ] 涉及跨模块 → python utils/gen_arch_stats.py --check-boundaries
[ ] 自评 3 问：① 删这个 App，其他 App 是否只经 api/Model 读受影响？② 写操作是否都能被 Tool 与 View 复用同一 api？③ diff 每行可追溯到需求？
```

App 级附加项（delta）→ 模块文档，入口是 [backend/apps/AGENTS.md](apps/AGENTS.md) 的模块索引。完整自测命令 → [`.agents/docs/apps/self_test_and_checks.md`](../.agents/docs/apps/self_test_and_checks.md)。
