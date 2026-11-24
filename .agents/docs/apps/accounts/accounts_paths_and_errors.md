# accounts · 路径与错误码

> 归属模块：`backend/apps/accounts` ｜ 类型：模块功能开发说明
> 代码真相源：`backend/apps/accounts/urls.py`、`backend/config/urls.py`
> 上级约束：`backend/AGENTS.md` ｜ 模块索引：`backend/apps/AGENTS.md`

## 路径约定

`urls.py` 里的路径**必须带尾斜杠**（`login/` / `register/` / `refresh/` / `logout/` / `me/`）。
`POST /api/auth/login/` 命中；`POST /api/auth/login` 是 **404** —— 容错中间件已删除、
`APPEND_SLASH=False`，缺失尾斜杠不会再被重定向或改写（见 `openspec/specs/api-path-convention`）。

## 错误码

| 端点 | 码 | 触发 |
|---|---|---|
| login | 200 / 400 / 401 | 成功 / 用户名或密码缺失 / 凭证错误 |
| register | 200 / 400 / 409 | 成功 / 长度·一致性·邮箱校验 / 用户名已存在 |
| refresh | 200 / 401 | 换新 access / refresh 无效、已吊销、账号已停用或类型错 |
| logout | 200 / 503 | 已吊销 / 吊销存储不可用（拒绝登出） |
| me | 200 / 401 / 403 / 404 | 身份 / 无令牌或已吊销 / 账号已停用（`account_disabled`）/ 用户已删除 |

## 鉴权姿态

`login` / `register` / `refresh` 三条在 `backend/gateway/middleware.py` 的 `PUBLIC_PREFIXES` 内，免 JWT；
`logout` / `me` **不公开**，需有效 access。全局口径见 `backend/AGENTS.md` §2。

## 关联

- 会话与吊销语义 → [accounts_session_and_logout.md](accounts_session_and_logout.md)
- 用户名冲突的 409 路径 → [accounts_username_uniqueness.md](accounts_username_uniqueness.md)
