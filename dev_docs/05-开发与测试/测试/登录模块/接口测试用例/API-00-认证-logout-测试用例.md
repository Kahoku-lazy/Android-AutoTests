# API-00-认证 — 登出接口测试用例

> 文档：`API-00-认证.md` · 实现：`auth_views.py::logout`

| 编号 | 测试点 | 分类 | 场景 | 请求类型 | 请求地址 | 域名信息 | 请求参数 | Content-Type | 鉴权 | 请求体 | 期望 HTTP | 期望响应 | 说明 |
|:--:|:--:|:--:|------|:--:|------|------|------|:--:|:--:|------|:--:|------|------|
| TC-LOGOUT-001 | 登出接口 | 功能 | 正常登出 | POST | /api/ai/auth/logout | http://localhost:8765 | — | application/json | Bearer Token | — | 200 | `status=true` | Token 加入 Redis 黑名单 |
| TC-LOGOUT-002 | 登出接口 | 功能 | 登出后原 access_token 无法使用 | POST | /api/ai/auth/logout | http://localhost:8765 | — | application/json | Bearer Token | — | 200 → 后续 401 | 登出成功 → 用同 token 调 `/me` → 401 | 黑名单生效 |
| TC-LOGOUT-003 | 登出接口 | 校验 | 无 Authorization 请求头 | POST | /api/ai/auth/logout | http://localhost:8765 | — | application/json | — | — | 401 | `status=false` | `require_auth` 装饰器拦截，但 logout 无 try/except |
| TC-LOGOUT-004 | 登出接口 | 校验 | Authorization 值非 Bearer 格式 | POST | /api/ai/auth/logout | http://localhost:8765 | — | application/json | `Token xxx` | — | 200 | `status=true` | `auth_header.startswith("Bearer ")` 为 False，跳过黑名单，仍返回 200 |
| TC-LOGOUT-005 | 登出接口 | 校验 | Authorization 值为空 Bearer | POST | /api/ai/auth/logout | http://localhost:8765 | — | application/json | `Bearer ` | — | 200 | `status=true` | `auth_header[7:]` → `""`，空白 token 可能入黑名单 |
| TC-LOGOUT-006 | 登出接口 | 校验 | 使用已过期的 access_token | POST | /api/ai/auth/logout | http://localhost:8765 | — | application/json | Bearer Token（过期） | — | 401 | `status=false` | `require_auth` 先校验 JWT 有效性 |
| TC-LOGOUT-007 | 登出接口 | 校验 | 使用被篡改的 access_token | POST | /api/ai/auth/logout | http://localhost:8765 | — | application/json | Bearer Token（篡改） | — | 401 | `status=false` | JWT 签名验证失败 |
| TC-LOGOUT-008 | 登出接口 | 异常 | Redis 不可用 | POST | /api/ai/auth/logout | http://localhost:8765 | — | application/json | Bearer Token（有效） | — | 503 | `status=false`, `message` 含 Redis 提示, `retry:true` | `BlacklistUnavailableError` |
| TC-LOGOUT-009 | 登出接口 | 功能 | 重复登出（Token 已在黑名单） | POST | /api/ai/auth/logout | http://localhost:8765 | — | application/json | Bearer Token（已登出） | — | 取决于 `require_auth` | 如果 JWT 仍在有效期但已在黑名单，需确认行为 |
