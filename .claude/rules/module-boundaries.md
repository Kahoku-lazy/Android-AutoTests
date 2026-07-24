# Module Boundaries — Android-AutoTests

## 三道防火墙

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

## 各层交互

| 层 | 协议 | 鉴权 |
|----|------|------|
| 前端 → 后端 | HTTP REST + WebSocket | JWT Bearer |
| 前端 → AI | SSE 流式 | JWT（共享 SECRET_KEY） |
| AI ↔ 后端 | 同进程直接调用 | Tool 调用前 AgentScope 已验证 |
| 后端 → 设备 | ADB + uiautomator2 | — |
