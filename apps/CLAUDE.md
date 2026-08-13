# Backend CLAUDE.md — AI 约束

> 工作于 `apps/` / Django 后端时必须遵守。细则与反例见 `dev_docs/项目笔记/后端claude笔记.md`；自测命令见 `apps/自测与检测指令.md`；关单自检用 skill `django-backend-check`。

**口诀**：View 只分发，写库走 api，跨模块不碰内部实现，JSON snake_case，错误要上报，重构先问值不值。  
**完成定义**：`manage.py check` + ruff 通过 ≠ 完成；相关单测/集成测与契约要对齐。

---

## 0. 动手前

1. 需求模糊 → 列 3～5 种理解让用户选，禁止默默挑一种执行。
2. 先读调用链：**urls → views/serializers → api.py → models**；有 WS 再读 `consumers` + `gateway/routing.py`。
3. 查：`.claude/rules/backend.md`、`api-conventions.md`、`python-code.md`、`database.md`；模块专属约束见笔记 §0️⃣。
4. 判边界：纯逻辑→①；Model/api 写库→②；HTTP/DRF→③；WS→④；AI Tool/SSE→⑤；跨界按序做。

---

## 1. 职责与红线

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
- **禁止**跨 App import `service` / `runner` / `consumer` / `state_machine`。
- 响应统一 `{status, data}` / `{status, message}`；JSON **snake_case**。
- 写操作禁止静默吞错；对用户错误文案不暴露技术术语。
- `dashboard` **只读**，禁止写操作。
- 表前缀：`dp_` `el_` `cm_` `tr_` `rg_` `ai_` `wf_` `ev_`；`db_table` 显式指定。
- 文件上限：`urls` 200 / `views` 300 / `api|service` 400 / executor 500；超阶梯必须拆分而非继续堆。
- 改 api 签名：调用方、注解、docstring、单测同改；Serializer 与 Model/前端契约同改。

**默认拒绝的重构**：无行为变化的大搬家；用函数内 import 掩盖循环依赖；过早万能 `helpers.py`；无测试保护的状态机/执行器迁移。

---

## 2. 协议要点

**HTTP / DRF**：`urls.py` 为路径真相源 → View/ViewSet → Serializer → `api.py`。  
- 身份：`request.user_id`（中间件）；业务 view 遵循现有 JWT / `@csrf_exempt` 约定。  
- 错误带 HTTP 状态码（400/401/403/404/409/500）。  
- 契约对照：前端 api、`VUE_API_CONTRACT.md`、本 App Serializer。

**WS**：Consumer 必须在 `gateway/routing.py` 注册；事件 `type` 与前端一致；写库仍走 api。

**AI**：Tool 只调各模块 `api.py`；SSE 事件变更同步前端；依赖 Redis（见 `backend.md`）。

---

## 3. 关单前最短清单

```
[ ] python manage.py check
[ ] makemigrations --check（若动 Model）
[ ] ruff check + ruff format --check（相关路径）
[ ] pytest -m "unit or integration"（涉及接口再加 api）
[ ] 写库只经 api；无跨模块内部 import
[ ] 信封与 snake_case；写失败有 message/日志
[ ] 涉及跨模块 → gen_arch_stats.py --check-boundaries
[ ] diff 每行可追溯到用户需求
```

详细门禁 → skill `django-backend-check`。  
详细决策树与模块踩坑 → `dev_docs/项目笔记/后端claude笔记.md`。  
完整自测命令 → `apps/自测与检测指令.md`。
