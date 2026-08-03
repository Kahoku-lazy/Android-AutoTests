# Backend 架构 — Android-AutoTests

> Django 后端架构约束。代码编写规范 → `python-code.md`
> 模块边界 / API 格式 → `api-conventions.md` | 数据库 → `database.md`

## 技术栈

Django + Daphne + Django Channels + Django ORM

## Django App 结构

```
apps/{app_name}/
├── models.py     # ORM Model 定义（表结构）
├── views.py      # HTTP 请求入口
├── api.py        # 跨模块写操作（__all__ 白名单）
├── urls.py       # URL 路由（app_name + urlpatterns）
├── consumers.py  # WebSocket Consumer（如有）
└── service.py    # 内部业务逻辑（可省略）
```

> 各文件的编写规范 → `python-code.md` §5

## 中间件和鉴权流程

```
请求 → JWTAuthenticationMiddleware
     → 检查 URL 是否在公开路径列表
     → 公开路径：直接放行
     → 需鉴权：从 Authorization header 提取 Bearer token
              → JWT 验证（共享 SECRET_KEY）
              → 注入 request.user_id
              → 放行
```

**公开路径**：`/api/ai/auth/*` `/admin/` `/static/`
**开发模式**：无 token 也放行（`request.user_id = None`）

## 配置约定

| 配置项 | 文件 | 说明 |
|--------|------|------|
| INSTALLED_APPS | `config/settings.py` | 新增 App 在此注册；jazzmin 在 admin 前 |
| 数据库引擎 | `config/settings.py` | `DB_ENGINE` 环境变量切换 sqlite/mysql |
| CORS | `config/settings.py` | 开发环境 `CORS_ALLOW_ALL_ORIGINS = True` |
| 时区 | `config/settings.py` | `LANGUAGE_CODE='zh-hans'` `TIME_ZONE='Asia/Shanghai'` `USE_TZ=False` |
| URL 分发 | `config/urls.py` | `include('apps.{name}.urls')` |
| ASGI 入口 | `config/asgi.py` | HTTP → URLRouter, WS → 中央路由 |
| WS 中央路由 | `gateway/routing.py` | 所有 WebSocket consumer 在此注册 |

> Token 黑名单使用 Redis 存储（`shared/auth/jwt_auth.py`），服务重启不丢失。

## 关键架构依赖

- **AgentScope 依赖 Redis**：Redis 不可用时 AgentScope 无法启动，AI 对话降级到 Django 阻塞模式
- **JWT 共享**：Django + AgentScope 共享 `SECRET_KEY`
- **服务端口**：Django `:8765`，AgentScope `:8000`，Redis `:6379`
- **新增 App 注册**：`settings.py` + `config/urls.py` + `router.js` + `AppSidebar.vue` 各 1 行

## 异步处理

- 同步视图：默认模式，Daphne 工作线程中执行（uiautomator2 阻塞调用适用）
- async 视图：仅 `POST /api/runner/run` 用 `async def`，`asyncio.create_task()` 后台执行测试
- AgentScope 桥接：`db_helper.run_sync()` 封装 `sync_to_async`，8s 超时
