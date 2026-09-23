# Backend AGENTS.md — AI 约束

> **AGENTS 层级**：一级约束 —— 根 `AGENTS.md` 优先于本文件；本文件优先于 `apps/{app}/AGENTS.md`。

**口诀**：View 只分发，写库走 api，跨模块不碰内部实现，JSON snake_case，错误要上报，重构先问值不值。  
**完成定义**：`manage.py check` + ruff 通过 ≠ 完成；相关单测/集成测与契约要对齐。

---

## 1. 职责与红线

1. 聚焦后端的**分层架构**设计与 **API约定**


### 1.1 分层与模块边界

1. **内部层纪律** View 只分发，写库走 api

2. **写库路径**：View / Tool → `api.py` → ORM；跨 App 读 Model ✅，跨 App 写必须走对方 `api.py`。


### 1.2 硬性约束

1. **严禁** 跨 App 内部实现 import


### 1.3 契约规则

- 响应信封 `{status, data}` / `{status, message}`；HTTP JSON **snake_case**（前端 camelCase 转换在前端侧）。
- **信封特例（legacy 平铺，禁止新增，未收敛前禁止改造成信封式）**：
  - report_generator `/reports/*`：平铺 + `FileResponse` 下载。
- 契约对照：前端 api 层、本 App Serializer；改路径/字段必须双边同步。


## 2. 协议要点

**HTTP / DRF**：`urls.py` 为路径真相源 → View/ViewSet → Serializer → `api.py`。  
- 身份：`request.user_id`（JWTAuthenticationMiddleware 注入）；公开路径 `/api/ai/auth/*` `/admin/` `/static/`（真相源：`gateway/middleware.py` 的 `_is_public()`）。  
- 错误带 HTTP 状态码（400/401/403/404/409/500）。  
- 契约对照：前端 api、本 App Serializer。

**WS**：Consumer 必须在 `gateway/routing.py` 注册；事件 `type` 与前端一致；写库仍走 api。仅 1 生产点（§1.2 通道收敛）；事件表见 `apps/case_manager/AGENTS.md`（`case_updated`）。

**AI**：Tool 只调各模块 `api.py`（同进程直调，无 SSE）；依赖 Redis（见 `config/env.py` / `config/settings.py`）。

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

App 级附加项（delta）→ 各 `apps/{app}/AGENTS.md` 关单段。完整自测命令 → `apps/自测与检测指令.md`。
