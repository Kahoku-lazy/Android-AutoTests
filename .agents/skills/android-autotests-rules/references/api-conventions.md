# API Conventions — Android-AutoTests

> API 格式 + 模块边界 + 跨层交互。获取端点列表：Read 各 App 的 `urls.py`，这是唯一真相源。

## 写操作收敛原则

```
前端只能通过 Django View 写数据 → View 调用 api.py 函数写 DB
AgentScope Tool 只能通过 api.py 函数写数据 → 同进程直接调用
禁止任何组件直接 ORM INSERT/UPDATE/DELETE（只读 ORM 查询除外）
```

## 响应格式

```json
{"status": true, "data": {...}}  // 成功
{"status": false, "message": "..."}  // 失败
```

> **legacy 平铺特例**（report_generator `/reports/*`、workflow legacy）唯一登记在 `apps/AGENTS.md` §1.3，禁止新增；未收敛前禁止把特例改造成标准信封。

## 鉴权

`Authorization: Bearer <JWT>`（除 `/api/ai/auth/*` `/admin/` `/static/` 外全部需要）。所有业务视图使用 `@csrf_exempt`。

## 模块边界（三道防火墙）

```
防火墙 #1: service.py 互不 import
  ✅ 跨 App import Model (只读) + api.py (复杂写)
  ❌ 跨 App import service / 内部实现

防火墙 #2: 读放开，写收敛
  ✅ 跨 App 读 (SELECT): 直接 ORM
  ❌ 跨 App 写 (INSERT/UPDATE/DELETE): 必须走 api 函数

防火墙 #3: 外部访问只走 API
  Vue → HTTP → Django API → ORM → DB
  AgentScope → Tool → Django ORM/API (同进程，不走 HTTP)
  Django Admin → ORM → DB (管理员专用)
```

典型反例（跨模块边界）：

```text
❌ View 里 Device.objects.create(...)
❌ case_manager import test_runner.service / state_machine
❌ api.py 返回 Model 实例给跨模块调用方
✅ View → api.create_xxx(...) → ORM
✅ AgentScope Tool → api.create_xxx(...) → ORM
```

## 各层交互协议

| 层 | 协议 | 鉴权 |
|----|------|------|
| 前端 → 后端 | HTTP REST + WebSocket | JWT Bearer |
| AI ↔ 后端 | 同进程直接调用 | Tool 调用前 AgentScope 已验证 |
| 后端 → 设备 | UiEngine 协议（引擎中转，引擎内部 ADB/u2） | — |

## 新 App 检查清单（新增 Django App 必走）

```
[ ] apps/{name}/ 具备: models / views(或 views_drf) / api.py / urls.py / apps.py
[ ] models 显式 db_table + 正确表前缀（见 database.md）
[ ] api.py 有 __all__；写操作参数为简单类型
[ ] config/settings.py INSTALLED_APPS 已注册
[ ] config/urls.py include 已注册
[ ] 若有 WS：gateway/routing.py 已注册
[ ] apps/{name}/AGENTS.md 已建（照既有 App 模板：红线/契约特例/协议/关单附加项）
[ ] 前端：router.js + AppSidebar.vue 各 1 行（若暴露页面）
[ ] python manage.py makemigrations && migrate
[ ] python manage.py check 通过
```
