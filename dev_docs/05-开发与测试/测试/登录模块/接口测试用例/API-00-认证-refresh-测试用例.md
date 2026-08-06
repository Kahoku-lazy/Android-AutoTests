# API-00-认证 — 刷新 Token 接口测试用例

> 文档：`API-00-认证.md` · 实现：`auth_views.py::refresh_token`

| 编号 | 测试点 | 分类 | 场景 | 请求类型 | 请求地址 | 域名信息 | 请求参数 | Content-Type | 鉴权 | 请求体 | 期望 HTTP | 期望响应 | 说明 |
|:--:|:--:|:--:|------|:--:|------|------|------|:--:|:--:|------|:--:|------|------|
| TC-REF-001 | 刷新Token接口 | 功能 | 正常刷新 — 使用有效 refresh_token | POST | /api/ai/auth/refresh | http://localhost:8765 | refresh_token | application/json | 无需 | `{"refresh_token":"<有效refresh_token>"}` | 200 | `status=true`, `access_token`, `token_type:bearer` | 返回新 access_token |
| TC-REF-002 | 刷新Token接口 | 功能 | 刷新后原 access_token 失效 | POST | /api/ai/auth/refresh | http://localhost:8765 | refresh_token | application/json | 无需 | `{"refresh_token":"<有效refresh_token>"}` | 200 | `status=true`, `access_token` 为新值 | 旧 access_token 应被替换 |
| TC-REF-003 | 刷新Token接口 | 校验 | refresh_token 为空 | POST | /api/ai/auth/refresh | http://localhost:8765 | refresh_token | application/json | 无需 | `{"refresh_token":""}` | 401 | `status=false`, `message` 含错误描述 | `data.get("refresh_token","")` → `""` |
| TC-REF-004 | 刷新Token接口 | 校验 | 缺少 refresh_token 字段 | POST | /api/ai/auth/refresh | http://localhost:8765 | refresh_token | application/json | 无需 | `{}` | 401 | `status=false`, `message` 含错误描述 | 空 token 触发 verify 异常 |
| TC-REF-005 | 刷新Token接口 | 校验 | refresh_token 为随机字符串 | POST | /api/ai/auth/refresh | http://localhost:8765 | refresh_token | application/json | 无需 | `{"refresh_token":"random_string"}` | 401 | `status=false`, `message` 含 JWT 解析错误 | 非 JWT 格式 |
| TC-REF-006 | 刷新Token接口 | 校验 | refresh_token 已过期 | POST | /api/ai/auth/refresh | http://localhost:8765 | refresh_token | application/json | 无需 | `{"refresh_token":"<过期refresh_token>"}` | 401 | `Token has expired` | 超过 7 天 TTL |
| TC-REF-007 | 刷新Token接口 | 校验 | 使用 access_token 代替 refresh_token | POST | /api/ai/auth/refresh | http://localhost:8765 | refresh_token | application/json | 无需 | `{"refresh_token":"<有效access_token>"}` | 401 | `Not a refresh token` | `payload.get("type") != "refresh"` |
| TC-REF-008 | 刷新Token接口 | 校验 | 使用被篡改的 refresh_token | POST | /api/ai/auth/refresh | http://localhost:8765 | refresh_token | application/json | 无需 | `{"refresh_token":"<被篡改一位的token>"}` | 401 | `status=false`, `message` 含签名错误 | JWT 签名验证失败 |
| TC-REF-009 | 刷新Token接口 | 校验 | JSON 格式非法 | POST | /api/ai/auth/refresh | http://localhost:8765 | refresh_token | application/json | 无需 | `not a json` | 400 | `请求格式错误` | 此接口未 try/except JSONDecodeError，需验证实际行为 |
| TC-REF-010 | 刷新Token接口 | 安全 | 使用登出后的 refresh_token | POST | /api/ai/auth/refresh | http://localhost:8765 | refresh_token | application/json | 无需 | `{"refresh_token":"<已登出用户的refresh_token>"}` | 401 | `status=false` | 当前不支持 refresh_token 黑名单，需关注 |
