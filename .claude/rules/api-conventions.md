# API Conventions — Android-AutoTests

> **获取端点列表**：直接 Read 各 App 的 `urls.py`，这是唯一真相源。
> WebSocket 路由在 `gateway/routing.py`。AgentScope 路由由框架动态生成。

## API 交互规则

### 请求格式

- **Content-Type**：`application/json`（除文件上传用 `multipart/form-data`）
- **鉴权**：`Authorization: Bearer <JWT>`（除 `/api/ai/auth/*` 外全部需要）
- **CSRF**：所有业务视图使用 `@csrf_exempt`（前后端分离，JWT 鉴权替代 CSRF）

### 响应格式

```json
// 成功
{"ok": true, "data": {...}}
// 失败
{"ok": false, "error": "错误描述"}
```

### 跨域来源规则

| 来源 | 方式 | 规则 |
|------|------|------|
| **Vue 前端** | HTTP → Django view | JWT 鉴权，业务数据通过 `request.body` JSON 传递 |
| **AgentScope** | Tool → Django ORM/API | 同进程直接调用，不走 HTTP |
| **Django Admin** | ORM → DB | 管理员专用，走 Django 内置 session 认证 |

### 写操作收敛原则

```
前端只能通过 Django View 写数据 → View 调用 api.py 函数写 DB
AgentScope Tool 只能通过 api.py 函数写数据 → 同进程直接调用
禁止任何组件直接 ORM INSERT/UPDATE/DELETE（只读 ORM 查询除外）
```

## 新增 App 时的框架注册（4 个文件各 1 行）

| 文件 | 操作 |
|------|------|
| `config/settings.py` | `INSTALLED_APPS` 加 1 行 |
| `config/urls.py` | `include('apps.{name}.urls')` |
| `frontend/src/router.js` | `import` 模块路由汇总 |
| `frontend/src/shared/components/AppSidebar.vue` | `navItems` 加菜单项 |

## 技术细节

- **阻塞操作**：设备操作是阻塞的 — Django 同步视图在 Daphne 工作线程中运行
- **async 视图**：仅 `POST /api/runner/run` 使用 `async def`，通过 `asyncio.create_task()` 后台执行
- **Channels**：开发环境优先 Redis，不可用时回退 InMemoryChannelLayer
- **CORS**：开发环境 `CORS_ALLOW_ALL_ORIGINS = True`
