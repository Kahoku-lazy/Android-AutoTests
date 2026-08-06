# API-00-认证 — 当前用户接口测试用例

> 文档：`API-00-认证.md` · 实现：`auth_views.py::me`

| 编号 | 测试点 | 分类 | 场景 | 请求类型 | 请求地址 | 域名信息 | 请求参数 | Content-Type | 鉴权 | 请求体 | 期望 HTTP | 期望响应 | 说明 |
|:--:|:--:|:--:|------|:--:|------|------|------|:--:|:--:|------|:--:|------|------|
| TC-ME-001 | 当前用户接口 | 功能 | 正常获取当前用户 | GET | /api/ai/auth/me | http://localhost:8765 | — | — | Bearer Token | — | 200 | `status=true`, `user:{id,username}` | 页面刷新后恢复登录态 |
| TC-ME-002 | 当前用户接口 | 功能 | 获取用户信息不返回敏感字段 | GET | /api/ai/auth/me | http://localhost:8765 | — | — | Bearer Token | — | 200 | `user` 不含 `password` `email` `api_key` | 确认响应中无敏感字段 |
| TC-ME-003 | 当前用户接口 | 校验 | 无 Authorization 请求头 | GET | /api/ai/auth/me | http://localhost:8765 | — | — | — | — | 401 | `Not authenticated` | `request.user_id` 为 None |
| TC-ME-004 | 当前用户接口 | 校验 | Authorization 值非 Bearer 格式 | GET | /api/ai/auth/me | http://localhost:8765 | — | — | `Token xxx` | — | 401 | `Not authenticated` | 中间件无法解析 |
| TC-ME-005 | 当前用户接口 | 校验 | access_token 已过期 | GET | /api/ai/auth/me | http://localhost:8765 | — | — | Bearer Token（过期） | — | 401 | `Not authenticated` | 中间件 `verify_token` 失败 → `user_id=None` |
| TC-ME-006 | 当前用户接口 | 校验 | access_token 被篡改 | GET | /api/ai/auth/me | http://localhost:8765 | — | — | Bearer Token（篡改） | — | 401 | `Not authenticated` | JWT 签名验证失败 |
| TC-ME-007 | 当前用户接口 | 校验 | access_token 已在黑名单 | GET | /api/ai/auth/me | http://localhost:8765 | — | — | Bearer Token（已登出） | — | 401 | `Not authenticated` | 中间件是否校验黑名单需确认 |
| TC-ME-008 | 当前用户接口 | 校验 | Token 中 user_id 对应用户已删除 | GET | /api/ai/auth/me | http://localhost:8765 | — | — | Bearer Token（有效但用户已删） | — | 404 | `User not found` | `User.objects.get(id=user_id)` 抛出 DoesNotExist |
| TC-ME-009 | 当前用户接口 | 安全 | 使用 refresh_token 访问 | GET | /api/ai/auth/me | http://localhost:8765 | — | — | Bearer Token（refresh_token） | — | 取决于中间件 | `verify_token` 只校验签名和过期，不校验 type，可能成功 |
