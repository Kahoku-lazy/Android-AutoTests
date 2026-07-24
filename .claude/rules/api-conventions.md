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
{"ok": true, "data": {...}}  // 成功
{"ok": false, "error": "..."}  // 失败
```

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

## 各层交互协议

| 层 | 协议 | 鉴权 |
|----|------|------|
| 前端 → 后端 | HTTP REST + WebSocket | JWT Bearer |
| 前端 → AI | SSE 流式 | JWT（共享 SECRET_KEY） |
| AI ↔ 后端 | 同进程直接调用 | Tool 调用前 AgentScope 已验证 |
| 后端 → 设备 | ADB + uiautomator2 | — |

## 新增 App 注册（4 文件各 1 行）

`config/settings.py` → `config/urls.py` → `frontend/src/router.js` → `frontend/src/shared/components/AppSidebar.vue`
