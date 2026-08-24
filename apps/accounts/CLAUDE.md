# accounts App CLAUDE.md

> 全局边界 / 协议要点 / 关单清单 → `../CLAUDE.md`；本文只写本 App 增量，冲突以全局为准。
> 版本：v1.0 · 最后更新：2026-08-21 · v1.0：从已归档 `dev_docs/_archive/后端claude笔记.md` §0️⃣ 模块表迁出并展开。

## 红线（全局索引表 accounts 行的展开）

| 只做 | 禁止 |
|------|------|
| 登录/注册/刷新/登出/me（`/api/auth/*`） | 其他模块放认证逻辑（全站唯一鉴权入口） |
| JWT 签发/校验、Redis 黑名单维护 | 手写第二条鉴权通道 |

- 公开路径列表以 `.claude/rules/backend.md` 与 JWTAuthenticationMiddleware 为唯一真相源，**两者必须一致**——改漏导致全站 401 或误放行。
- Token 黑名单在 Redis（`shared/auth/jwt_auth.py`），服务重启不丢失；登出必须入黑名单而非仅前端删 token。
- 认证接口是前端 `views/LoginView` 的唯一后端入口，无独立前端模块。

## 本 App 契约（特例 + 真相源）

真相源：`apps/accounts/urls.py`（5 端点：`login` / `register` / `refresh` / `logout` / `me`）+ `serializers.py` + `api.py`。端点有增删必须同改前端 `views/LoginView` api 层。

- 无 models（不建表）；`api.py` 已有 `__all__`，写操作参数为简单类型。
- 错误状态码：401（凭证错误/过期）、409（重名冲突，若有）、400（参数缺失）。
- **预留端点**：`me` 前端暂未消费（2026-08-21 校验确认），保留路由；前端新增消费时同步本文。

## 本 App 协议要点

无 WS / SSE。JWT 共享 `SECRET_KEY`（Django 与 AgentScope 同进程共享，见 `backend.md`）。

## 关单附加项（全局清单的 delta）

```
[ ] 无 token / 坏 token / 正常 token 三条路径验证过（pytest -m api）
[ ] 公开路径列表未改动；若改动，中间件与 backend.md 同改
[ ] 登出后旧 token 已入黑名单、无法再访问 /api/...（auth 外端点）
[ ] 错误文案无技术术语（不暴露 JWT 细节）
```
